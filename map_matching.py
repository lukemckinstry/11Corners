#match crash points to map edges, not nodes

import json
from math import sqrt
import sys

if len(sys.argv) != 5:
	print("Command Line Input Error: please enter crash_datafile <space> geo_network_graph_datafile <space> outputfile <space> breakpoints (10,100, etc.)")
	sys.exit()

crash_datafile = sys.argv[1]
network_geo_datafile = sys.argv[2]
merged_output_datafile = sys.argv[3]
breakpoints_input = sys.argv[4]

#optional directly specify filepaths
#crash_datafile = '../delco_crash_data_fullfield.json'
#network_geo_datafile = '../delco_network.json'
#merged_output_datafile = 'delco_crashes_in_geo_network.json'

#json requires dict key be stored as string, after reading in json convert key back into lon, lat tuple of floats
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

#for performance, specify number of dicts to subdivide data based on lon
def get_breakpoints( geo_network_data, num_breakpoints  ):
	geo_network_keys_lon = [k[0] for k in geo_network_data.keys()]
	network_lon_min = min(geo_network_keys_lon)
	network_lon_max = max(geo_network_keys_lon )
	#print("min/max ", network_lon_min, network_lon_max)
	lon_splitter = abs(network_lon_max - network_lon_min) /num_breakpoints
	breakpoints = [ network_lon_min + i*lon_splitter for i in range(num_breakpoints + 1)  ]
	return breakpoints

def split_geo_dict( geo_network_data, breakpoints ):
	split_dicts_list = [{} for _ in range(len(breakpoints)-1)]
	for i in range( len(breakpoints)-1 ):
		split_dicts_list[i] = { k: geo_network_data[k] for k in geo_network_data if breakpoints[i]<k[0]<breakpoints[i+1] } 
	return split_dicts_list

def split_crash_dict( crash_data, breakpoints ):
	split_dicts_list = [{} for _ in range(len(breakpoints)-1)]
	for i in range( len(breakpoints)-1 ):
		split_dicts_list[i] = { k: crash_data[k] for k in crash_data if breakpoints[i]<k[0]<breakpoints[i+1] }
	return split_dicts_list

#helper func to see how data divided
def show_split_dist(geo_dict_object, crash_dict_object):
	return [ [len(i) for i in geo_dict_object], [len(i) for i in crash_dict_object] ]

#when iterating through each crash point, get nearby points before checking which is nearest
def get_sub_dict(crash_point, geo_dict_iterator):
	ct = crash_point
	x_margin = ct[0] * .000010 #buffer size
	y_margin = ct[1] * .000010
	xb = [ ct[0]-x_margin, ct[0]+x_margin ] # margin based on buffer
	yb = [ ct[1]-y_margin, ct[1]+y_margin ]
	sub_dict = {k: v for k, v in geo_dict_iterator if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] } # nearby points, next check which is nearest
	return sub_dict

def find_nearest(sub_dict, this_crash_point):
	if len(sub_dict) == 0:
		return None
	else:
		ct = this_crash_point
		#iterable_sub_dict = iter(sub_dict)
		#nearest_point = next(iterable_sub_dict)  
		#nearest_dist = sqrt( (ct[0] - nearest_point[0])**2 + (ct[1] - nearest_point[1])**2 ) # simple distance calc using lat lon
		nearest_dist = 1
		for node in sub_dict:
			
		# 	dist = sqrt( (ct[0] - sub_point[0])**2 + (ct[1] - sub_point[1])**2 )
		# 	if dist < nearest_dist:
		# 		nearest_dist = dist
		# 		nearest_point = sub_point
		# return nearest_point

			start = node			
			for edge in sub_dict[node]:
					# print("EDGE")
					# print( edge )
				end = edge["end"]
					# print("END")
					# print( type(end[0]), type(end[1]) )
					# print( end[0], end[1])
				try:
					dist = dist_to_line_segment(start, end, ct)
					if dist < nearest_dist:
					 	#print("****************")
				 		nearest_dist = dist
				 		nearest_edge = [start, end]
				except:
					pass
					#print("DIST")
					#print(dist, nearest_dist)
				# for edge in node:
				# dist = sqrt( (ct[0] - sub_point[0])**2 + (ct[1] - sub_point[1])**2 )
				
		return nearest_edge

def assign_to_node(geo_dict_slice, crash_dict_object, this_crash_point, nearest_graph_edge):
	# print("ASSIGN TO NODE")
	try:
		start_node = geo_dict_slice.get(nearest_graph_edge[0])
		end_node = next((item for item in start_node if item['end'] == nearest_graph_edge[1] ), None)  
		# print("END NODE KEYS")
		# print( end_node.keys() )  
		if "c_pt" not in end_node.keys():
			end_node["c_pt"] = 1
		else:
			end_node["c_pt"] += 1
		# print( "ADDED ")
		# print(geo_dict_slice[nearest_graph_edge[0]])
		return True
	except:
		return False


def dist_to_line_segment(p1, p2, p0):
	m = (p1[1] - p2[1]) / (p1[0] - p2[0])
	# print("slope: ", m)
	inverse_m = m * -1
	# print("inverse slope: ", inverse_m)	
	numerator = abs( ((p2[0] - p1[0]) * (p1[1] - p0[1])) - ((p1[0] - p0[0]) * (p2[1] - p1[1])) )
	dist  = numerator / (((p2[0] - p1[0])**2) + ((p2[1] - p1[1])**2))**0.5
	# print("dist", dist)
	# print("p0: ", p0[0], p0[1] )
	dx =  dist * ((1/(1 + inverse_m**2))**0.5 )
	dy = inverse_m * dx
	p3 = [p0[0]-dx, p0[1]-dy]
	if p3[0] < min(p1[0], p2[0]) or p3[0] > max(p1[0], p2[0]) or p3[1] < min(p1[1], p2[1]) or p3[1] > max(p1[1], p2[1]):
		dist = min( dist_bt_nodes(p0,p1), dist_bt_nodes(p0,p2) )
	return dist
	
def dist_bt_nodes(base_node, dest_node):
	return ( (base_node[0] - dest_node[0])**2 + (base_node[1] - dest_node[1])**2 )**0.5



def iterate_through_crashes( crash_dict_object, geo_dict_object, breakpoints ):
	counter = 0
	bad_counter = 0
	total = sum([ len(i) for i in crash_dict_object ])
	for i in range(len(breakpoints)-1):  # iterate through each slice determined by breakpoints
		geo_dict_iterator = geo_dict_object[i].items()   # make each slice iterator object for faster search
		for this_crash_point in crash_dict_object[i]:
			counter += 1
			print( counter/ float(total)*100.000  )   # optional progress output to terminal
			sub_dict = get_sub_dict(this_crash_point, geo_dict_iterator)
			nearest_graph_edge = find_nearest(sub_dict, this_crash_point)
			if assign_to_node(geo_dict_object[i], crash_dict_object[i], this_crash_point, nearest_graph_edge ) == False:
				bad_counter += 1  # optional sanity check, breakpoints may separate crash from nearest map node
	#print("after iterating ", counter, "  this many bad assignments ", bad_counter)
	return

def combine(geo_dict_object, output_dict, breakpoints):
	for i in range(len(breakpoints)-1):
		for geo_node in geo_dict_object[i]: # combine slices back to one graph network that can be searched
			output_dict[ str(geo_node) ] = geo_dict_object[i][geo_node] 
	return

def sanity_check(output_dict): # optional sanity check to ensure crashes matched to nodes
	singles, doubles, triples = 0,0,0
	# for node in output_dict:
	# 	for edge in output_dict[node]:
	# 		keys = [ i for i in output_dict[node][edge].keys() ]
	# 		if "c_pt" in keys:
	# 			#print("Good sign")
	# 			singles += 1
	print(  "single, ", singles, " doubles ", doubles, " triples, ", triples)
	return

def write_to_file(output_dict):
	with open(merged_output_datafile, 'w') as outfile:
		json.dump(output_dict, outfile)
	return

def main(crash_datafile, network_geo_datafile, breakpoints_input):
	network =  get_network_graph( network_geo_datafile )
	breakpoints = get_breakpoints( network, int(breakpoints_input) )  #number of breakpoints specific by command line input
	geo_dict_object = split_geo_dict( network, breakpoints )
	crash_dict = get_crash_data(crash_datafile)
	crash_dict_object = split_crash_dict( crash_dict, breakpoints )
	print(show_split_dist(geo_dict_object, crash_dict_object))
	iterate_through_crashes(crash_dict_object, geo_dict_object, breakpoints)
	output_dict = {}
	combine( geo_dict_object, output_dict, breakpoints )
	sanity_check(output_dict)
	write_to_file(output_dict)
	return

main(crash_datafile, network_geo_datafile, breakpoints_input)

