from lib.unemployment import Unemployment
import json

unemployment = Unemployment()
data = unemployment.scrape()

f = open('./data/test.json', 'w')
f.write(json.dumps(data, indent=4, sort_keys=True))
f.close()