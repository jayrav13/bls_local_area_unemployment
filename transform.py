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

# Reference data
reference = open('data/reference.json', 'r')
reference = json.load(reference)

# Prepare output array.
output = {}

# Iterate through all files.
for filename in os.listdir('data/pages/'):

	# Split filename and build breakdown dict.
	breakdown = filename.split('-')
	breakdown = {
		'state': reference['states'][breakdown[0]],
		'datatype': reference['datatypes'][breakdown[1]],
		'year': int(breakdown[2]),
		'period': reference['periods'][breakdown[3]]
	}

	# Check output for keys.
	if breakdown['year'] not in output:
		output[breakdown['year']] = {}
	if breakdown['period'] not in output[breakdown['year']]:
		output[breakdown['year']][breakdown['period']] = {}
	if breakdown['state'] not in output[breakdown['year']][breakdown['period']]:
		output[breakdown['year']][breakdown['period']][breakdown['state']] = {}
	if breakdown['datatype'] not in output[breakdown['year']][breakdown['period']][breakdown['state']]:
		output[breakdown['year']][breakdown['period']][breakdown['state']][breakdown['datatype']] = {}

	f = open('data/pages/' + filename)
	tree = html.document_fromstring(f.read())

	# Check to make sure this page has data.
	try:
		state = [x for x in tree.xpath('//select[@name="state"]')[0].xpath('option') if 'selected' in x.attrib][0]
	except:
		continue

	# Get unemployment statistics.
	counties = [x.text_content() for x in tree.xpath('//th[@class="OutputHead"]')]
	counties = counties[2:len(counties)]
	rates = [float(x.text_content()) for x in tree.xpath('//td[@class="OutputCell"]')]

	# Handle a failed retrieval.
	if len(counties) != len(rates):
		print "FAILED - " + filename
		continue

	# Iterate through all counties / rates and add.
	for i in range(0, len(counties)):
		output[breakdown['year']][breakdown['period']][breakdown['state']][breakdown['datatype']][counties[i]] = rates[i]

	print "SUCCESS - " + filename

	f.close()

f = open('result.json', 'w')
f.write(json.dumps(output, indent=4, sort_keys=True))
f.close()
