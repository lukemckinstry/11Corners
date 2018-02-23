
#insert map data dictionaries into containerized (0.05 meridians) mongo database
import json
import pymongo
from pymongo import MongoClient
import math
from config import mongo_uri

import sys

if len(sys.argv) != 2:
	print("Usage python mongobackend.py <space> compress_merge_file")
	sys.exit()

infile = sys.argv[1]




### Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
#uri = 'mongodb://user:pass@host:port/db'
client = pymongo.MongoClient(mongo_uri)
db = client.get_default_database()

#local mongo db setup
#client = MongoClient('localhost', 27017)
#db = client['delco-network']

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


def round_nearest(x, a):
    return round(round(x / a) * a, -int(math.floor(math.log10(a))))

def prep_insert_dict(feature_dict, prep_network):
	slices = sorted(set([ round_nearest(f[0], 0.05) for f in feature_dict  ]))
	for s in slices:
		subdict = { str(x).replace('.','&#46;'): feature_dict[x] for x in feature_dict if x[0] >= s and x[0] < s + 0.05}
		prep_network[ tuple([s,round_nearest(s+0.05,0.05)  ])] = subdict	
	return

def query_tile(tile_key):
	print( "QUERY-TILE", tile_key, tile_key[0], tile_key[1] )
	cursor = db.slices.find_one( { 'latmin' : { '$eq' : tile_key[0]  } , 'latmax' : { '$eq' : tile_key[1]  }   })	
	# for document in cursor:
	# 	print( len(document['nodes']) )
	if cursor:
		print("KEYS IN CURSOR -->", cursor.keys())
		cursor = cursor['nodes']
	return cursor

def insert_to_mongo( slice_network ):
	for slice_key in slice_network:
		existing_dict = query_tile( slice_key )
		if existing_dict:
			print( "DOC ALREADY EXISTS, UPDATING OLD ONE", slice_key  )
			#print( "BEFORE UPDATE ", len(existing_dict ) )
			existing_dict.update( slice_network[slice_key] )
			#print( "AFTER UPDATE ", len(existing_dict ) )
			db.slices.update( { 'latmin': slice_key[0], 'latmax':slice_key[1] }, { 'latmin': slice_key[0], 'latmax':slice_key[1], 'nodes' : existing_dict } )
		else:
			print( "NO EXISTING DOC, SAVING NEW ONE", slice_key  )
			existing_dict = slice_network[slice_key]
			db.slices.save( { 'latmin': slice_key[0], 'latmax':slice_key[1], 'nodes' : existing_dict } )		
	return


def querymongo():
	#slices = db.slices
	pointlat = -75.28
	cursor = db.slices.find( { 'latmin' : { '$lt' : pointlat  } , 'latmax' : { '$gt' : pointlat  }   })	
	for document in cursor:
		print( len(document['nodes']) )
	return

def main(infile):
	features = get_data(infile)
	prep_network = {}
	prep_insert_dict( features, prep_network )
	insert_to_mongo( prep_network )
	#querymongo()
	#print("MONGO URI", mongo_uri)
	return

#sample input/output files
#infile = '../../osmdata/compress_merge_region.json'

main(infile)