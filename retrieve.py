# Imports
import os
import sys
import time
import json
import httplib
import requests
import itertools

# Imports
from lxml import html
from Queue import Queue
from urllib import urlencode
from urlparse import urlparse
from threading import Thread

def data(state=None, datatype=None, year=None, period=None):
	"""
	Given information on location and time period, returns dictionary to be used w/HTTP request.
	"""
	return {
		'state': state,
		'datatype': datatype,
		'year': year,
		'period': period,
		'survey': 'la',
		'map': 'county',
		'seasonal': 'u'
	}

def headers():
	"""
	Returns headers that are used for browser spoofing.
	"""
	return {
		'Origin': 'https://data.bls.gov',
		'Accept-Encoding': 'gzip, deflate, br',
		'Accept-Language': 'en-US,en;q=0.8',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Cache-Control': 'max-age=0',
		'Referer': 'https://data.bls.gov/map/MapToolServlet',
		'Connection': 'keep-alive',
	}

def cookies():
	"""
	Returns cookies that are used for browser spoofing. 
	"""
	return {
		'JSESSIONID': 'C4ED79ECA0DF132B3C4D7B1317A7BEA5.tc_instance3',
		'_ga': 'GA1.2.240688613.1488207254',
		'_gat_GSA_ENOR0': '1',
		'fsr.s': '{"v2":-2,"v1":0,"rid":"de358f8-93135139-abd1-da7b-41f4f","ru":"https://www.google.com/","r":"www.google.com","st":"","to":3,"c":"https://data.bls.gov/map/MapToolServlet","pv":1,"lc":{"d0":{"v":1,"s":false}},"cd":0,"f":1488207156326}',
	}

# Establish base URL.
url = "https://data.bls.gov/map/MapToolServlet"

# Make a GET request to the page without specific data to retrieve all state / period (months) / year possibilities.
response = requests.get(url, params={ k: v for k, v in data().iteritems() if v is not None })
tree = html.document_fromstring(response.text)

def fetch_states():
	"""
	Return all <option> values for the <select> element with all states.
	"""
	states = tree.xpath('//select[@name="state"]')[0].xpath('option')
	data = {}
	for state in states:
		data[state.attrib['value']] = state.text_content()
	return data

def fetch_years():
	"""
	Return all <option> values for the <select> element with all states.
	"""
	years = tree.xpath('//select[@name="year"]')[0].xpath('option')
	data = {}
	for year in years:
		data[year.attrib['value']] = year.text_content()
	return data

def fetch_periods():
	"""
	Return all <option> values for the <select> element with all states.
	"""
	periods = tree.xpath('//select[@name="period"]')[0].xpath('option')
	data = {}
	for period in periods:
		data[period.attrib['value']] = period.text_content()
	return data

def fetch_datatypes():
	"""
	Returns all datatype views radio options.
	"""
	options = tree.xpath('//input[@name="datatype"]')
	data = {}
	for option in options:
		data[option.attrib['value']] = option.tail
	return data

# Get the entirety of these four entities that will be iterated over.
states = fetch_states()
periods = fetch_periods()
years = fetch_years()
datatypes = fetch_datatypes()

# Make sure a data directory exists.
if not os.path.isdir('data/'):
	os.makedirs('data/')

if not os.path.isdir('data/pages/'):
	os.makedirs('data/pages/')

# Build out the reference.json file for future work.
payload = {
	"states": states,
	"periods": periods,
	"years": years,
	"datatypes": datatypes
}

# Safe references.
f = open('data/reference.json', 'w')
f.write( json.dumps( payload, indent=4, sort_keys=True ) )
f.close()

# Combine all four lists.
# http://stackoverflow.com/questions/798854/all-combinations-of-a-list-of-lists
queries = list(itertools.product(*[states.keys(), datatypes.keys(), years.keys(), periods.keys()]))

# Set up threading function.
def doWork():
	while True:
		filename = queue.get()
		query = filename.split('-')
		payload = data( query[0], query[1], query[2], query[3] )

		response = requests.post(url, headers=headers(), cookies=cookies(), data=payload)

		f = open('data/pages/' + filename, 'w')
		f.write(response.text)
		f.close()
		print filename

		queue.task_done()

# Set up threading and queueing strategy.
concurrent = 100
queue = Queue( concurrent * 2 )

# Launch threads.
for i in range( concurrent ):
	t = Thread(target=doWork)
	t.daemon = True
	t.start()

# Add to queue.
try:

	# Get all pages.
	for query in queries:
		query = list(query)
		queue.put(query[0] + "-" + query[1] + "-" + query[2] + "-" + query[3])

	queue.join()

except KeyboardInterrupt:
	sys.exit(1)