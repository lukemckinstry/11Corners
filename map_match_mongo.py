#match crash points to map edges, not nodes

import json
import math
from math import sqrt
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
	for crash_point in crash_data:
		try:
			lon_lat_key = tuple([string_to_float(crash_point)[1], string_to_float(crash_point)[0]])
			crash_dict[lon_lat_key] = crash_data[crash_point]
		except:
			pass
	return crash_dict

def get_network_graph(network_geo_datafile):
	with open(network_geo_datafile) as data_file:    
	    geo_network_data = json.load(data_file)
	geo_node_dict = {}
	for node_point in geo_network_data:
		try:
			lon_lat_key = string_to_float(node_point)
			geo_node_dict[lon_lat_key] = geo_network_data[node_point]
		except:
			pass
	return geo_node_dict

def get_breakpoints( geo_network_data, num_breakpoints  ):
	#specify breakpoints in longitude to subdivide network graph and crash points
	geo_network_keys_lon = [k[0] for k in geo_network_data.keys()]
	network_lon_min = min(geo_network_keys_lon)
	network_lon_max = max(geo_network_keys_lon)
	lon_splitter = abs(network_lon_max - network_lon_min) /num_breakpoints
	breakpoints = [ network_lon_min + i*lon_splitter for i in range(num_breakpoints + 1)  ]
	return breakpoints

def split_geo_dict( geo_network_data, breakpoints ):
	#slice network graph
	split_dicts_list = [{} for _ in range(len(breakpoints)-1)]
	for i in range( len(breakpoints)-1 ):
		split_dicts_list[i] = { k: geo_network_data[k] for k in geo_network_data if breakpoints[i]<k[0]<breakpoints[i+1] } 
	return split_dicts_list

def split_crash_dict( crash_data, breakpoints ):
	#slice crash data
	split_dicts_list = [{} for _ in range(len(breakpoints)-1)]
	for i in range( len(breakpoints)-1 ):
		split_dicts_list[i] = { k: crash_data[k] for k in crash_data if breakpoints[i]<k[0]<breakpoints[i+1] }
	return split_dicts_list

def round_nearest(x, a):
    return round(round(x / a) * a, -int(math.floor(math.log10(a))))

def make_crash_tiles(crash_dict, crash_tiles):
	lon_slices = sorted(set([ round_nearest(f[0], 0.05) for f in crash_dict  ]))
	lat_slices = sorted(set([ round_nearest(f[1], 0.05) for f in crash_dict  ]))
	print( "LON SLICES --> ", lon_slices )
	print( "LAT SLICES --> ", lat_slices )
	total = len(lat_slices) * len(lon_slices)
	count = 0
	for lat_s in lat_slices:
		for lon_s in lon_slices:
			lon_id = tuple([lon_s,round_nearest(lon_s+0.05,0.05) ])
			lat_id = tuple([lat_s,round_nearest(lat_s+0.05,0.05) ])
			tile_id = tuple([lon_id, lat_id])
			mongo_tile = get_mongo_tile(tile_id)
			count += 1
			print(  "HERE" , count / total * 100)  
			if mongo_tile:
				print( "GOT MONGO TILE ", tile_id )
				crash_subdict = { x: crash_dict[x] for x in crash_dict if 
								x[0] >= lon_s and x[0] < lon_s + 0.05  and
								x[1] >= lat_s and x[1] < lat_s + 0.05	}				
				#crash_tiles[ tile_id ] = crash_subdict				
				print( "LEN MONGO TILE", len(mongo_tile) )
				nearest_edge = iter_crash( mongo_tile, crash_subdict )
				#edit_mongo_tile( mongo_tile, crash_subdict )
				#reinsert_mongo_tile( mongo_tile )
			# else:
			# 	print( "NO MONGO TILE HERE",  )
	return

def get_mongo_tile( tile_key ):
	output_dict = {}
	cursor = db.slices.find( {	'lonmin' : { '$eq' : tile_key[0][0]  } ,
									'lonmax' : { '$eq' : tile_key[0][1]  } ,
									'latmin' : { '$eq' : tile_key[1][0]  } ,
									'latmax' : { '$eq' : tile_key[1][1]  } ,
									  })	
	if not cursor:
		return None
	else:
		for document in cursor: 
			
			output_dict.update( document['nodes']  )
		clean_output_dict = clean_mongo_slice( output_dict )
		return clean_output_dict

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


def show_split_dist(geo_dict_object, crash_dict_object):
	#check distribution into dict slices
	return [ [len(i) for i in geo_dict_object], [len(i) for i in crash_dict_object] ]



def find_nearby(sub_dict, ct):
	# find nearest edge to crash point
	if len(sub_dict) == 0: #no network graph edges nearby
		return None
	else:	
		score = 0
		nearest_dist = 1
		for node in sub_dict: # get start and end of each edge
			#print( "FIND NEAREST TO --> ", node )
			start = node			
			for edge in sub_dict[node]:
				#print( "IN SUBDICT --> ", edge )

				end = edge["end"]
				try:
					#get dist from crash point to edge
					dist = dist_to_line_segment(start, end, ct)
					if dist < 0.0001:
				 		nearest_dist = dist
				 		nearest_edge = [start, end]
				except:
					pass
		return nearest_edge

def assign_to_node(geo_dict_slice, crash_dict_object, this_crash_point, nearest_graph_edge):
	# tally crashes for each network graph edge
	try:
		start_node = geo_dict_slice.get(nearest_graph_edge[0])
		end_node = next((item for item in start_node if item['end'] == nearest_graph_edge[1] ), None)  
 
		if "c_pt" not in end_node.keys():
			end_node["c_pt"] = 1
		else:
			end_node["c_pt"] += 1

		return True
	except:
		return False


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


# def call_mongo_slice(point):
# 	print( "QUERY MONGO--> ", point )
# 	slices = db.slices
# 	cursor = slices.find( {	'lonmin' : { '$lt' : point[0]  } ,
# 							'lonmax' : { '$gt' : point[0]  } ,
# 							'latmin' : { '$lt' : point[1]  } ,
# 							'latmax' : { '$gt' : point[1]  }   })
# 	output_dict = {}
# 	for document in cursor: 
# 		output_dict.update( document['nodes']  )
# 		print( "RAN CURSOR LOOP HOPEFULLY ONCE!!" )
# 	clean_mongo_dict = clean_mongo_slice(output_dict)
# 	return clean_mongo_dict

def get_sub_search_dict(crash_point, geo_dict):
	#before iterating through each crash point, get small dict of nearby points 
	ct = crash_point
	x_margin = ct[0] * .000010 #buffer size
	y_margin = ct[1] * .000010
	xb = [ ct[0]-x_margin, ct[0]+x_margin ] # margin based on buffer
	yb = [ ct[1]-y_margin, ct[1]+y_margin ]
	sub_dict = {k: geo_dict[k] for k in geo_dict if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] } # nearby points, next check which is nearest
	return sub_dict

def iter_crash( mongo_tile, crash_subdict ):
	# iterate through each crash point to assign it to network graph
	for cp in crash_subdict: #current graph point to pass through dist and assignment functions
		sub_search_dict = get_sub_search_dict(cp, mongo_tile)
		print("SIZE OF TILE ", len(mongo_tile), " SIZE OF SUB SEARCH DICT ", len(sub_search_dict)  )
		
		#INSTEAD OF JUST SNAPPING, APPLY WEIGHT TO ALL NEARBY ROADS?!?!?!?!?
		nearest_edge = find_nearby(sub_search_dict, cp)


		#print( "FOUND NEAREST EDGE" )
		#assign_to_node( sub_dict, crash_dict_object, this_crash_point, nearest_graph_edge)
	return

def combine(geo_dict_object, output_dict, breakpoints):
	# merge slices back to single graph network 
	for i in range(len(breakpoints)-1):
		for geo_node in geo_dict_object[i]: 
			output_dict[ str(geo_node) ] = geo_dict_object[i][geo_node] 
	return


def write_to_file(output_dict):
	with open(merged_output_datafile, 'w') as outfile:
		json.dump(output_dict, outfile)
	return

def main(crash_datafile, ):
	#network =  get_network_graph( network_geo_datafile )
	#breakpoints = get_breakpoints( network, int(breakpoints_input) )  #number of breakpoints specific by command line input
	#geo_dict_object = split_geo_dict( network, breakpoints )
	crash_dict = get_crash_data(crash_datafile)
	crash_tiles = {}
	crash_tiles = make_crash_tiles( crash_dict, crash_tiles)

	for i in crash_tiles:
		print("TILE SIZE --> ", i, " <--> ", len(crash_tiles[i])  )
	#crash_dict_object = split_crash_dict( crash_dict, breakpoints )


	#iterate_through_crashes(crash_dict_object, geo_dict_object, breakpoints)
	#output_dict = {}
	#combine( geo_dict_object, output_dict, breakpoints )
	#write_to_file(output_dict)
	return
#USE WEIGHTED FILE!!!!!!!???????
crash_datafile = '../../PA/pa_weighted_crashesBACKUP.json'

main(crash_datafile )

