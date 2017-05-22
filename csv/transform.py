# Imports
import json

# Open file
f = open("../result.json", "r")
data = json.load(f)

output = open("output.csv", "a+")

for year, months in data.iteritems():
	months.pop("Annual")
	for month, states in months.iteritems():

		for state, categories in states.iteritems():

			for county, rate in categories["Unemployment Rate"].iteritems():

				output.write("\t".join([year, month, state, county, str(rate)]) + "\n")

f.close()
output.close()

