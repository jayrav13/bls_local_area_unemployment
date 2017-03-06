# Imports
import sys
import requests
from lxml import html
import json
from urllib import urlencode

from urlparse import urlparse
from threading import Thread
import httplib
from Queue import Queue
import time

class Unemployment:
	"""
	Unemployment

	Scraper for Local Area Unemployment. Source: https://data.bls.gov
	"""

	def __init__(self, level="county", seasonal="u"):

		# Validate inputs for class constructor.
		if level not in ["state", "county"]:
			raise Exception("The first parameter \"level\", must be \"state\" or \"county\".")
		self._map = level

		if seasonal not in ["s", "u"]:
			raise Exception("For state-level data, the second parameter must be \"s\" (seasonal) or \"u\" (not seasonal, or unadjusted).")
		self._seasonal = seasonal

		# Establish base URL.
		self._url = "https://data.bls.gov/map/MapToolServlet"

		# Make a GET request to the page without specific data to retrieve all state / period (months) / year possibilities.
		self._base_page = requests.get(self._url, params={ k: v for k, v in self._data().iteritems() if v is not None })
		self._tree = html.document_fromstring(self._base_page.text)

		# Get the entirety of these four entities that will be iterated over.
		self._states = self._fetch_states()
		self._periods = self._fetch_periods()
		self._years = self._fetch_years()
		self._datatypes = self._fetch_datatypes()

		self._concurrent = 100
		self._q = Queue( self._concurrent * 2 )
		self._result = {}

	def scrape(self):
		"""
		Primary function that executes the scrape.
		"""

		# Spin up threads per class variable.
		for i in range( self._concurrent ):
			t = Thread(target=self._doWork)
			t.daemon = True
			t.start()

		# Set counter for testing.
		count = 0

		# Try / Except for queue'ing and threading.
		try:

			# Years
			for year in self._years:

				# Add year as key.
				if year.keys()[0] not in self._result:
					self._result[ int(year.keys()[0]) ] = {}

				# Period (i.e. month, year)
				for period in self._periods:

					if period.keys()[0] not in self._result[ int(year.keys()[0]) ]:
						self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ] = {}
						self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ]['details'] = {
							"key": period.keys()[0],
							"name": period.values()[0],
							"permalink": period.values()[0].lower().replace(' ', '_')
						}

					# State
					for state in self._states:

						if state.values()[0].lower().replace(' ', '_') not in self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ]:
							self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ][ state.values()[0].lower().replace(' ', '_') ] = {}
							self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ][ state.values()[0].lower().replace(' ', '_') ]['details'] = {
								"key": state.keys()[0],
								"name": state.values()[0],
								"permalink": state.values()[0].lower().replace(' ', '_')
							}

						for datatype in self._datatypes:

							if datatype.keys()[0] not in self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ][ state.values()[0].lower().replace(' ', '_') ]:
								self._result[ int(year.keys()[0]) ][ period.values()[0].lower().replace(' ', '_') ][ state.values()[0].lower().replace(' ', '_') ][ datatype.keys()[0] ] = []

							packet = {
								"query": self._data( state.keys()[0], datatype.keys()[0], year.keys()[0], period.keys()[0] ),
								"keys": {
									"state": state.values()[0].lower().replace(' ', '_'),
									"datatype": datatype.keys()[0],
									"year": int(year.keys()[0]),
									"period": period.values()[0].lower().replace(' ', '_')
								}
							}

							self._q.put( json.dumps( packet ) )

			self._q.join()

		except KeyboardInterrupt:
			sys.exit(1)

		return self._result


	def _doWork(self):
		while True:
			data = self._q.get()
			data = json.loads(data)
			result = self._request(data['query'])
			if result is not False:
				self._result[ data['keys']['year'] ][ data['keys']['period'] ][ data['keys']['state'] ][ data['keys']['datatype'] ].append(result)

			self._q.task_done()
		"""
		result = self._request(data)
		self._data.append(result)
		self._q.task_done()
		"""

	def _headers(self):
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

	def _cookies(self):
		"""
		Returns cookies that are used for browser spoofing. 
		"""
		return {
			'JSESSIONID': 'C4ED79ECA0DF132B3C4D7B1317A7BEA5.tc_instance3',
			'_ga': 'GA1.2.240688613.1488207254',
			'_gat_GSA_ENOR0': '1',
			'fsr.s': '{"v2":-2,"v1":0,"rid":"de358f8-93135139-abd1-da7b-41f4f","ru":"https://www.google.com/","r":"www.google.com","st":"","to":3,"c":"https://data.bls.gov/map/MapToolServlet","pv":1,"lc":{"d0":{"v":1,"s":false}},"cd":0,"f":1488207156326}',
		}

	def _data(self, state=None, datatype=None, year=None, period=None):
		"""
		Given information on location and time period, returns dictionary to be used w/HTTP request.

		datatype: 	["unemployment", "12_month_net"]
		map: 		["state", "county"]
		seasonal:	["s", "u"]
		"""
		return {
			'state': state,
			'datatype': datatype,
			'year': year,
			'period': period,
			'survey': 'la',
			'map': self._map,
			'seasonal': self._seasonal
		}

	def _request(self, data):

		# Simple GET request to get started with states data.
		r = requests.post(self._url, headers=self._headers(), cookies=self._cookies(), data=data)

		f = open('pages/' + data['year'] + "-" + data['period'] + "-" + data['state'] + "-" + data['datatype'] + "-" + data['map'] + "-" + data['seasonal'] + "-" + data['survey'], 'w')
		f.write(r.text)
		f.close()
		print data['year'] + "-" + data['period'] + "-" + data['state'] + "-" + data['datatype'] + "-" + data['map'] + "-" + data['seasonal'] + "-" + data['survey']
		return False

		tree = html.document_fromstring(r.text)

		# Get State
		try:
			state = [x for x in tree.xpath('//select[@name="state"]')[0].xpath('option') if 'selected' in x.attrib][0]
		except:
			return False

		# Retrieve counties and unemployment rates.
		counties = [x.text_content() for x in tree.xpath('//th[@class="OutputHead"]')]
		counties = counties[2:len(counties)]
		rates = [float(x.text_content()) for x in tree.xpath('//td[@class="OutputCell"]')]

		# Confirm that this scrape was successful.
		if len(counties) != len(rates):
			return False

		# Set up object for states.
		obj = {
			"state": state.text_content(),
			"permalink": state.text_content().lower().replace(' ', '_'),
			"counties": []
		}

		# Build county data.
		for i in range(0, len(counties)):
			obj['counties'].append({
				"county": counties[i],
				"permalink": counties[i].lower().replace(' ', '_'),
				"unemployment": rates[i],
				"state": state.text_content()
			})

		print data
		obj['request'] = data

		return obj

	def _fetch_states(self):
		"""
		Return all <option> values for the <select> element with all states.
		"""
		states = self._tree.xpath('//select[@name="state"]')[0].xpath('option')
		return [ { x.attrib['value'] : x.text_content() } for x in states]

	def _fetch_years(self):
		"""
		Return all <option> values for the <select> element with all states.
		"""
		years = self._tree.xpath('//select[@name="year"]')[0].xpath('option')
		return [ { x.attrib['value'] : x.text_content() } for x in years]

	def _fetch_periods(self):
		"""
		Return all <option> values for the <select> element with all states.
		"""
		periods = self._tree.xpath('//select[@name="period"]')[0].xpath('option')
		return [ { x.attrib['value'] : x.text_content() } for x in periods]

	def _fetch_datatypes(self):
		"""
		Returns all datatype views radio options.
		"""
		options = self._tree.xpath('//input[@name="datatype"]')
		return [ { x.attrib['value'] : x.tail } for x in options]
