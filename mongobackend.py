
#insert map data dictionaries into containerized (0.05 meridians) mongo database
import json
import pymongo
from pymongo import MongoClient
import math

client = MongoClient('localhost', 27017)
db = client['delco-network']

def string_to_float(input_string):
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def get_data(geojson_datafile):
	with open(geojson_datafile) as data_file:
		data = json.load(data_file)
	output_dict = {}
	for key in data:
		tuple_key = string_to_float(key)
		output_dict[tuple_key] = data[key]
	return output_dict


def prep_slice_dict(feature_dict, slice_network):
	slices = set([ math.floor(f[0] / 0.05) * 0.05 for f in feature_dict  ])
	for s in slices:
		subdict = { str(x).replace('.','&#46;'): feature_dict[x] for x in feature_dict if x[0] >= s and x[0] < s + 0.05}
		slice_network[ tuple([s,s+0.05])] = subdict	
	return

def insert_to_mongo( slice_network ):
	for slice_key in slice_network:
		db.slices.save( { 'latmin': slice_key[0], 'latmax':slice_key[1], 'nodes' : slice_network[slice_key] } )
	return

def querymongo():
	slices = db.slices
	pointlat = -75.28
	cursor = slices.find( { 'latmin' : { '$lt' : pointlat  } , 'latmax' : { '$gt' : pointlat  }   })
	#for document in cursor: print( len(document['nodes']) )
	return

def main(infile):
	features = get_data(infile)
	slice_network = {}
	prep_slice_dict( features, slice_network )
	insert_to_mongo( slice_network )
	querymongo()
	print("LEN SLICE NETWORK", len(slice_network))
	return

#sample input/output files
infile = '../../osmdata/compress_delco.geojson'

main(infile)