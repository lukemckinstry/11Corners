#match crash points to map edges, not nodes

import json
import math
import sys
from config import mongo_uri
import pymongo
from pymongo import MongoClient


client = pymongo.MongoClient(mongo_uri)
db = client.get_default_database()

# if len(sys.argv) != 5:
# 	print("Command Line Input Error: please enter crash_datafile <space> geo_network_graph_datafile <space> outputfile <space> breakpoints (10,100, etc.)")
# 	sys.exit()

# crash_datafile = sys.argv[1]
# network_geo_datafile = sys.argv[2]
# merged_output_datafile = sys.argv[3]
# breakpoints_input = sys.argv[4]

#optional directly specify filepaths
#crash_datafile = '../delco_crash_data_fullfield.json'
#network_geo_datafile = '../delco_network.json'
#merged_output_datafile = 'delco_crashes_in_geo_network.json'

#convert dict key from string to floats
def string_to_float(input_string):
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def get_crash_data(crash_datafile):
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
    return round(round(x / a) * a, -int(math.floor(math.log10(a))))

def make_crash_tiles(crash_dict ):
	crash_tiles = {}
	lon_slices = sorted(set([ round_nearest(f[0], 0.05) for f in crash_dict  ]))
	lat_slices = sorted(set([ round_nearest(f[1], 0.05) for f in crash_dict  ]))
	print( "LON SLICES --> ", lon_slices )
	print( "LAT SLICES --> ", lat_slices )
	total = len(lat_slices) * len(lon_slices)
	count = 0
	total_mongo_tile_count = 0
	for lat_s in lat_slices:
		for lon_s in lon_slices:
			lon_id = tuple([lon_s,round_nearest(lon_s+0.05,0.05) ])
			lat_id = tuple([lat_s,round_nearest(lat_s+0.05,0.05) ])
			tile_id = tuple([lon_id, lat_id])
			crash_subdict = { str(x).replace('.','&#46;'): crash_dict[x] for x in crash_dict if
								x[0] >= lon_s and x[0] < lon_s + 0.05  and
								x[1] >= lat_s and x[1] < lat_s + 0.05	}
			count += 1
			print( count / total * 100 , " this one is --> ", len(crash_subdict ))  
			crash_tiles[tile_id] = crash_subdict
	return crash_tiles


def get_geo_tiles( ):
	output_list = []
	cursor = db.slices.find( {} )	
	if cursor:
		for document in cursor: 
			tile_id = tuple([	tuple( [document['lonmin'], document['lonmax']] ),
								tuple( [document['latmin'], document['latmax']] ) ])	
			output_list.append( tile_id ) 
		return output_list
	else:
		return None
		

def mongo_keys_to_float(input_string):
	item = input_string.replace('&#46;','.').split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def clean_mongo_slice(mongo_slice):
	output_dict = {}
	for s in mongo_slice:
		t = mongo_keys_to_float(s) 
		#print( "MONGO KEYS TO FLOAT--> ", t )
		output_dict[t] = mongo_slice[s]
	return output_dict


# def find_nearby(sub_dict, ct):
# 	# find nearest edge to crash point
# 	if len(sub_dict) == 0: #no network graph edges nearby
# 		return None
# 	else:	
# 		score = 0
# 		nearest_dist = 1
# 		for node in sub_dict: # get start and end of each edge
# 			#print( "FIND NEAREST TO --> ", node )
# 			start = node			
# 			for edge in sub_dict[node]:
# 				#print( "IN SUBDICT --> ", edge )

# 				end = edge["end"]
# 				try:
# 					#get dist from crash point to edge
# 					dist = dist_to_line_segment(start, end, ct)
# 					if dist < 0.0001:
# 				 		nearest_dist = dist
# 				 		nearest_edge = [start, end]
# 				except:
# 					pass
# 		return nearest_edge

# def assign_to_node(geo_dict_slice, crash_dict_object, this_crash_point, nearest_graph_edge):
# 	# tally crashes for each network graph edge
# 	try:
# 		start_node = geo_dict_slice.get(nearest_graph_edge[0])
# 		end_node = next((item for item in start_node if item['end'] == nearest_graph_edge[1] ), None)  
 
# 		if "c_pt" not in end_node.keys():
# 			end_node["c_pt"] = 1
# 		else:
# 			end_node["c_pt"] += 1

# 		return True
# 	except:
# 		return False


def get_sub_search_dict(crash_point, geo_dict):
	#before iterating through each crash point, get small dict of nearby points 
	ct = crash_point
	x_margin = ct[0] * .000010 #buffer size
	y_margin = ct[1] * .000010
	xb = [ ct[0]-x_margin, ct[0]+x_margin ] # margin based on buffer
	yb = [ ct[1]-y_margin, ct[1]+y_margin ]
	sub_dict = {k: geo_dict[k] for k in geo_dict if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] } # nearby points, next check which is nearest
	return sub_dict


def reinsert_geo_tile(slice_key, existing_dict):
	db.slices.update( { 'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1], },
							{ 	'lonmin': slice_key[0][0], 'lonmax':slice_key[0][1],
								'latmin': slice_key[1][0], 'latmax':slice_key[1][1],
								'nodes' : existing_dict } )
	return

def dist_to_line_segment(p1, p2, p0):
	#distance from point p0 to line segment between p1, p2 
	m = (p1[1] - p2[1]) / (p1[0] - p2[0])
	inverse_m = m * -1
	numerator = abs( ((p2[0] - p1[0]) * (p1[1] - p0[1])) - ((p1[0] - p0[0]) * (p2[1] - p1[1])) )
	dist  = numerator / (((p2[0] - p1[0])**2) + ((p2[1] - p1[1])**2))**0.5
	dx =  dist * ((1/(1 + inverse_m**2))**0.5 )
	dy = inverse_m * dx
	p3 = [p0[0]-dx, p0[1]-dy]
	if p3[0] < min(p1[0], p2[0]) or p3[0] > max(p1[0], p2[0]) or p3[1] < min(p1[1], p2[1]) or p3[1] > max(p1[1], p2[1]):
		dist = min( dist_bt_nodes(p0,p1), dist_bt_nodes(p0,p2) )
	return dist
	
def dist_bt_nodes(base_node, dest_node):
	return ( (base_node[0] - dest_node[0])**2 + (base_node[1] - dest_node[1])**2 )**0.5

def iter_match_crashes(  ):
	# iterate through each crash point to assign it to network graph
	geo_tiles = get_geo_tiles()
	print( "LEN GEO TILES--> ", len(geo_tiles)  )
	
	for tile_key in geo_tiles:
		geo_tile = query_geo_tile( tile_key )
		clean_geo_tile = clean_mongo_slice(geo_tile)
		crash_tile = query_crash_tile( tile_key )
		clean_crash_tile = clean_mongo_slice(crash_tile)
		#print( "LEN GEO TILE -> ", len(clean_geo_tile), "LEN CRASH TILE -> ", len(clean_crash_tile ) )
		count = 0
		print( "BEFORE GEO TILE --> ", len(geo_tile)) 
		for crash_point in clean_crash_tile:
			rank = clean_crash_tile[crash_point]			
			subdict = get_sub_search_dict( crash_point, clean_geo_tile )
			for node in subdict:
				node_id = str(node).replace('.','&#46;')
				for end in subdict[node]:
					dist = dist_to_line_segment( node, end['end'], crash_point  )
					orig_edge = next((item for item in geo_tile[node_id] if item == end), None)
					if dist < 0.000005:
						if 'c_pt' in orig_edge:
							orig_edge['c_pt'] += rank
						else:
							orig_edge['c_pt'] = rank

					print( "updated orig node", geo_tile[node_id] )
				
				
		print( "AFTER GEO TILE --> ", len(geo_tile)) 
		#reinsert_geo_tile(tile_key, geo_tile )
		#put back geo tile

	return

def query_geo_tile(tile_key):
	#print( "QUERY-TILE", tile_key, tile_key[0][0],tile_key[0][1], tile_key[1][0], tile_key[1][1] )
	cursor = db.slices.find_one( {	'lonmin' : { '$eq' : tile_key[0][0]  } ,
									'lonmax' : { '$eq' : tile_key[0][1]  } ,
									'latmin' : { '$eq' : tile_key[1][0]  } ,
									'latmax' : { '$eq' : tile_key[1][1]  } ,
									  })
	if cursor:
		cursor = cursor['nodes']
	return cursor

def query_crash_tile(tile_key):
	#print( "QUERY-TILE", tile_key, tile_key[0][0],tile_key[0][1], tile_key[1][0], tile_key[1][1] )
	cursor = db.crashes.find_one( {	'lonmin' : { '$eq' : tile_key[0][0]  } ,
									'lonmax' : { '$eq' : tile_key[0][1]  } ,
									'latmin' : { '$eq' : tile_key[1][0]  } ,
									'latmax' : { '$eq' : tile_key[1][1]  } ,
									  })
	if cursor:
		cursor = cursor['nodes']
	return cursor

def insert_to_mongo( slice_network ):
	count = 0
	for slice_key in slice_network:
		count += 1
		print( "insert_to_mongo ", count / len(slice_network) )
		existing_dict = query_crash_tile( slice_key )
		if existing_dict:
			print( "DOC ALREADY EXISTS, UPDATING OLD ONE", slice_key  )
			#print( "BEFORE UPDATE ", len(existing_dict ) )
			existing_dict.update( slice_network[slice_key] )
			#print( "AFTER UPDATE ", len(existing_dict ) )
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




def combine(crash_tiles, output_dict):
	# merge slices back to single graph network 
	for i in range(len(crash_tiles)):
		output_dict.update( crash_tiles[i] )
		print( "COMBINE, len is now -> ", len(output_dict) ) 
	return


def write_to_file(output_dict, tile_crash_outfile):
	with open(tile_crash_outfile, 'w') as outfile:
		json.dump(output_dict, outfile)
	return

def main(crash_datafile, tile_crash_outfile ):

	#crash_dict = get_crash_data(crash_datafile)
	#crash_tiles = make_crash_tiles( crash_dict)
	# print( "ORIG CRASH LEN", len(crash_dict ) )
	# print( "LEN CRASH TILES", sum([len(crash_tiles[i]) for i in crash_tiles] ) )
	#insert_to_mongo(crash_tiles)
	

	iter_match_crashes( )
	


	#output_dict = {}
	##combine( crash_tiles, output_dict )
	#write_to_file(output_dict, tile_crash_outfile)
	return
#USE WEIGHTED FILE!!!!!!!???????
crash_datafile = '../../PA/pa_weighted_crashesBACKUP.json'
tile_crash_outfile = '../../PA/pa_tile_weighted_crashes.json'

main(crash_datafile, tile_crash_outfile )

