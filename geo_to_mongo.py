
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
	'''
	for reading data from file i.e. not mongo db
	converts "(str1,str2)" to tuple(float,float)
	'''
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def get_data(geojson_datafile):
	'''
	for reading data from file i.e. not mongo db
	reads json object network graph from file to python dict 
	'''
	with open(geojson_datafile) as data_file:
		data = json.load(data_file)
	output_dict = {}
	for key in data:
		tuple_key = string_to_float(key)
		output_dict[tuple_key] = data[key]
	return output_dict


def round_nearest(x, a):
	'''
	floors to precision a, and then to number of significant digits, that has precision a
	'''
	return round(math.floor(x / a) * a, -int(math.floor(math.log10(a))))

def prep_insert_dict(feature_dict, prep_network):
	'''
	for reading data from file i.e not mongo db
	adds 4-part keys (minlon, maxlon, minlat, maxlat) to python dict to store each network graph point 
	'''
	slices = sorted(set([ round_nearest(f[0], 0.05) for f in feature_dict  ]))
	for s in slices:
		subdict = { str(x).replace('.','&#46;'): feature_dict[x] for x in feature_dict if x[0] >= s and x[0] < s + 0.05}
		prep_network[ tuple([s,round_nearest(s+0.05,0.05)  ])] = subdict	
	return


def prep_slice_dict(feature_dict, slice_network):
	'''
	for reading data from mongo db, not file
	adds subdict of network graph points to new python dict id'd  by 4-part keys (minlon, maxlon, minlat. maxlat) 
	'''
	lon_breaks = sorted(set([ round_nearest(f[0], 0.05) for f in feature_dict  ]))
	lat_breaks = sorted(set([ round_nearest(f[1], 0.05) for f in feature_dict  ]))
	lon_slices = [tuple([s, round_nearest(s+0.05, 0.05)]) for s in lon_breaks ] 
	lat_slices = [tuple([s, round_nearest(s+0.05, 0.05)]) for s in lat_breaks ] 
	for lat_s in lat_slices:
		for lon_s in lon_slices:
			subdict = { str(x).replace('.','&#46;'): feature_dict[x] for x in feature_dict if 
							x[0] >= lon_s[0] and x[0] < lon_s[1] and
							x[1] >= lat_s[0] and x[1] < lat_s[1] }
			lon_id = tuple([lon_s[0],lon_s[1] ])
			lat_id = tuple([lat_s[0],lat_s[1] ])
			#print( "PREP -> ", lon_id, lat_id, len(subdict) )
			if len(subdict) > 0:
				slice_network[ tuple([lon_id, lat_id] )  ] = subdict	
	return

def query_tile(tile_key):
	'''
	get a doc (json obj) from geo slices collection of mongo db, using 4-part key that ids it 
	return none if doc does not exist i.e. not yet data for that tile in db
	'''
	cursor = db.slices.find_one( {	'lonmin' : { '$eq' : tile_key[0][0]  } ,
									'lonmax' : { '$eq' : tile_key[0][1]  } ,
									'latmin' : { '$eq' : tile_key[1][0]  } ,
									'latmax' : { '$eq' : tile_key[1][1]  } ,
									  })	
	if cursor:
		cursor = cursor['nodes']
	return cursor

def insert_to_mongo( slice_network ):
	'''
	insert data to mongo db, if tile exists update it, otherwise create new doc for tile in db
	'''
	for slice_key in slice_network:
		existing_dict = query_tile( slice_key )
		if existing_dict:
			#DOC ALREADY EXISTS, UPDATING OLD ONE
			existing_dict.update( slice_network[slice_key] )
			db.slices.update( { 'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1], },
							{ 	'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1],
								'nodes' : existing_dict } )
		else:
			#NO EXISTING DOC, SAVING NEW ONE
			existing_dict = slice_network[slice_key]
			db.slices.save( {	'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1],
								'nodes' : existing_dict } )		
	return

def querymongo():
	'''
	sanity check, query a doc (tile) from db, or all docs in collection
	currently set up to solve duplicate docs issue
	'''
	#cursor = db.slices.find( { 'lonmin' : { '$lt' : pointlat  } , 'lonmax' : { '$gt' : pointlat  }   })	
	cursor = db.slices.find( { })	
	total = 0
	doc_list = []
	for document in cursor:
		doc_id = tuple([ document['lonmin'], document['lonmax'], document['latmin'], document['latmax']]) 
		doc_list.append( doc_id )
	#print( "TOTAL DOCS--> ", len(doc_list), "SET --> ", len( set(doc_list) ) )
	multiples = []
	for d in set(doc_list):
		if doc_list.count(d) > 1:
			multiples.append(d)
	#print( "##### -> ", [ [f, doc_list.count(f)] for f in multiples] )
	return

def main(infile):
	features = get_data(infile)
	prep_network = {}
	prep_slice_dict( features, prep_network )
	#insert_to_mongo( prep_network )
	#querymongo()
	#print("MONGO URI", mongo_uri)
	return

#sample input/output files
#infile = '../../osmdata/compress_merge_region.json'

main(infile)