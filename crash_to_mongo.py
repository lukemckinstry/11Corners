

import json
import math
import sys
from config import mongo_uri
import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient(mongo_uri)
db = client.get_default_database()


def string_to_float(input_string):
	'''
	for reading data from file i.e. not mongo db
	converts "(str1,str2)" to tuple(float,float)
	'''
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def get_crash_data(crash_datafile):
	'''
	for reading data from file i.e. not mongo db
	reads json object network graph from file to python dict 
	'''
	with open(crash_datafile) as data_file:    
	    crash_data = json.load(data_file)
	crash_dict = {}
	count = 0
	for crash_point in crash_data:
		try:
			lon_lat_key = tuple([string_to_float(crash_point)[0], string_to_float(crash_point)[1]])
			crash_dict[lon_lat_key] = crash_data[crash_point]
			count += 1
			print( count / len( crash_data ) * 100 )
		except:
			pass
	return crash_dict

def round_nearest(x, a):
	'''
	floors to precision a, and then to number of significant digits, that has precision a
	'''
    return round(math.floor(x / a) * a, -int(math.floor(math.log10(a))))

def make_crash_tiles(crash_dict ):
	'''
	for reading data from file i.e not mongo db
	makes dict of tiles with 4-part keys (minlon, maxlon, minlat, maxlat) to store crash point 
	'''
	crash_tiles = {}
	lon_breaks = sorted(set([ round_nearest(f[0], 0.05) for f in crash_dict  ]))
	lat_breaks = sorted(set([ round_nearest(f[1], 0.05) for f in crash_dict  ]))
	lon_slices = [tuple([s, round_nearest(s+0.05, 0.05)]) for s in lon_breaks ] 
	lat_slices = [tuple([s, round_nearest(s+0.05, 0.05)]) for s in lat_breaks ] 
	total = len(lat_slices) * len(lon_slices)
	count = 0
	total_mongo_tile_count = 0
	for lat_s in lat_slices:
		for lon_s in lon_slices:
			lon_id = tuple([lon_s[0],lon_s[1] ])
			lat_id = tuple([lat_s[0],lat_s[1] ])
			tile_id = tuple([lon_id, lat_id])
			crash_subdict = { str(x).replace('.','&#46;'): crash_dict[x] for x in crash_dict if
								x[0] >= lon_s[0] and x[0] < lon_s[1] and
								x[1] >= lat_s[0] and x[1] < lat_s[1]	}
			count += 1
			if len(crash_subdict) > 0:
				crash_tiles[tile_id] = crash_subdict
			else:
				print( "NOPE!!", len(crash_subdict) )
			#print( count / total * 100 , " this one is --> ", len(crash_subdict ))  
	return crash_tiles

def query_crash_tile(tile_key):
	'''
	get a doc (json obj) from geo slices collection of mongo db, using 4-part key that ids it 
	return none if doc does not exist i.e. not yet data for that tile in db
	'''
	cursor = db.crashes.find_one( {	'lonmin' : { '$eq' : tile_key[0][0]  } ,
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
	count = 0
	for slice_key in slice_network:
		count += 1
		print( "insert_to_mongo ", count / len(slice_network) )
		existing_dict = query_crash_tile( slice_key )
		if existing_dict:
			print( "DOC ALREADY EXISTS, UPDATING OLD ONE", slice_key  )
			existing_dict.update( slice_network[slice_key] )
			db.crashes.update( { 'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1], },
							{ 	'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1],
								'nodes' : existing_dict } )
		else:
			print( "NO EXISTING DOC, SAVING NEW ONE", slice_key  )
			existing_dict = slice_network[slice_key]
			db.crashes.save( {	'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1],
								'nodes' : existing_dict } )		
	return


def main(crash_datafile  ):
	crash_dict = get_crash_data(crash_datafile)
	crash_tiles = make_crash_tiles( crash_dict)
	#insert_to_mongo(crash_tiles)
	return

crash_datafile = '../../PA/pa_weighted_crashesBACKUP.json'

main(crash_datafile  )