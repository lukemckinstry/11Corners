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


def show_split_dist(geo_dict_object, crash_dict_object):
	#check distribution into dict slices
	return [ [len(i) for i in geo_dict_object], [len(i) for i in crash_dict_object] ]

def get_sub_dict(crash_point, geo_dict_iterator):
	#before iterating through each crash point, get small dict of nearby points 
	ct = crash_point
	x_margin = ct[0] * .000010 #buffer size
	y_margin = ct[1] * .000010
	xb = [ ct[0]-x_margin, ct[0]+x_margin ] # margin based on buffer
	yb = [ ct[1]-y_margin, ct[1]+y_margin ]
	sub_dict = {k: v for k, v in geo_dict_iterator if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] } # nearby points, next check which is nearest
	return sub_dict

def find_nearest(sub_dict, ct):
	# find nearest edge to crash point
	if len(sub_dict) == 0: #no network graph edges nearby
		return None
	else:	
		nearest_dist = 1
		for node in sub_dict: # get start and end of each edge
			start = node			
			for edge in sub_dict[node]:
				end = edge["end"]
				try:
					#get dist from crash point to edge
					dist = dist_to_line_segment(start, end, ct)
					if dist < nearest_dist:
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


def iterate_through_crashes( crash_dict_object, geo_dict_object, breakpoints ):
	# iterate through each crash point to assign it to network graph
	for i in range(len(breakpoints)-1):  
		geo_dict_iterator = geo_dict_object[i].items()   
		for this_crash_point in crash_dict_object[i]: #current graph point to pass through dist and assignment functions
			sub_dict = get_sub_dict(this_crash_point, geo_dict_iterator)
			nearest_graph_edge = find_nearest(sub_dict, this_crash_point)
			assign_to_node( sub_dict, crash_dict_object, this_crash_point, nearest_graph_edge)
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

def main(crash_datafile, network_geo_datafile, breakpoints_input):
	network =  get_network_graph( network_geo_datafile )
	breakpoints = get_breakpoints( network, int(breakpoints_input) )  #number of breakpoints specific by command line input
	geo_dict_object = split_geo_dict( network, breakpoints )
	crash_dict = get_crash_data(crash_datafile)
	crash_dict_object = split_crash_dict( crash_dict, breakpoints )
	iterate_through_crashes(crash_dict_object, geo_dict_object, breakpoints)
	output_dict = {}
	combine( geo_dict_object, output_dict, breakpoints )
	write_to_file(output_dict)
	return

main(crash_datafile, network_geo_datafile, breakpoints_input)

