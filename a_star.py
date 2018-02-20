#A* search implementation for geographic network graph. 

import json
from math import sqrt

def get_breakpoints( geo_network_data, num_breakpoints  ):
	geo_network_keys_lon = [k[0] for k in geo_network_data.keys()]
	network_lon_min = min(geo_network_keys_lon)
	network_lon_max = max(geo_network_keys_lon)
	lon_splitter = abs(network_lon_max - network_lon_min) /num_breakpoints
	breakpoints = [ network_lon_min + i*lon_splitter for i in range(num_breakpoints + 1)  ]
	return breakpoints

def split_geo_dict( geo_network_data, num_breakpoints ):
	#split_dicts_list = [{} for _ in range(len(breakpoints)-1)]
	breakpoints = get_breakpoints( geo_network_data, num_breakpoints )
	split_dicts_list = {}
	for i in range( len(breakpoints)-1 ):
		label = tuple([breakpoints[i], breakpoints[i+1]])
		print("LABEL", label)
		split_dicts_list[label] = { k: geo_network_data[k] for k in geo_network_data if breakpoints[i]<k[0]<breakpoints[i+1] } 
		print("SIZE OF THIS ONE: ", len(split_dicts_list[label]) )
	return split_dicts_list

def prep_network_graph(geo_network):
	geo_node_dict = {}
	for node_point in geo_network:
		try:
			lon_lat_key = string_to_float(node_point)
			geo_node_dict[lon_lat_key] = geo_network[node_point]
		except:
			pass
	return geo_node_dict

def string_to_float(input_string):
	#*utility function bc json dict keys must be strings, in algo we need floats 
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def dist_between_nodes(base_node, dest_node):
	#* both inputs should be float tuples
	return sqrt( (base_node[0] - dest_node[0])**2 + (base_node[1] - dest_node[1])**2 )

def find_nearest_node(input_point, network_data):
	#* Map Matching, input coordinates, return closest node from network graph
	nearest_dist = 1
	for raw_point in network_data:
		point = raw_point
		dist = dist_between_nodes(input_point, point)
		if dist < nearest_dist:
			nearest_dist = dist
			nearest_point = point
	return nearest_point

def search(start_point, finish_point, prep_network, sliced_dict):
	nav_path = dijkstra(start_point, finish_point, prep_network, sliced_dict )
	return nav_path

def call_slice(in_node, sliced_dict):
	d_slice = [sliced_dict[n] for n in sliced_dict if n[0]<in_node[0]<n[1]]
	return d_slice[0]
	
def dijkstra( start_point, finish_point, ac_network_data, sliced_dict ):
	
	search_start_node_id = find_nearest_node( start_point , ac_network_data )
	search_end_node_id = find_nearest_node( finish_point, ac_network_data )
	visited = [] #init dijkstra visited list
	dist_so_far = {} #dijkstra queue
	dist_so_far[search_start_node_id] = { "fs": 0,
										  "tf": dist_between_nodes(search_start_node_id, search_end_node_id),
										  "path":[search_start_node_id] }
	#each node is two-item list... [tuple w/ lon/lat coords as floats, dict for each adjacent node w/ weight (i.e. dist, safety score) & coords]
	
	#### THIS IS WHERE WE CALL THE SLICE
	this_slice = call_slice(search_start_node_id, sliced_dict)
	start_node = [search_start_node_id, this_slice.get( search_start_node_id) ]
	end_node = [search_end_node_id, ac_network_data.get( search_end_node_id) ]
	# if end_node == None:
	# 	end_slice = call_slice(search_start_node_id, sliced_dict)
	# 	end_node = [search_end_node_id, end_slice.get( search_end_node_id) ]
	dist = 0
	found_it = False
	count = 0
	call_slice_count = 0
	while found_it == False:
		visited.append(tuple(start_node[0]))
		if len(visited) > 1000:
			remove_item = visited.pop(0)
			del dist_so_far[remove_item]
		count += 1
		print("num loops ", count, len(visited))
		next_nodes = [ d for d in start_node[1]  ]  #get adjacent nodes
		if start_node == end_node:
			found_it = True
			nav_path = dist_so_far[start_node[0]]["path"] + [end_node[0]]
			crashes = []
			print( "NUM SLICE CHANGES: ", call_slice_count  )
			for node in nav_path:
				node_crashes = 0
				node_crashes += sum(  [i["c_pt"] for i in ac_network_data[node] if "c_pt" in i.keys()]  )
				if node_crashes > 0:
					crashes.append({"node":node, "c":node_crashes })
				#print(crashes)
				#print("num crashes on route: ", len(crashes))
			return {"path":[[i[0],i[1]] for i in nav_path],"visited":visited, "crashes":crashes}

		#available_next = {nn: dist + nn["dist"] for nn in next_nodes  }		  

		for next_node in next_nodes:
			crash_coef = 1
			try:
				crash_coef += (next_node["c_pt"]) **2
			except:
				pass 
			if tuple(next_node["end"]) not in [i[0] for i in dist_so_far]:	#add new node to queue	
				dist_so_far[tuple(next_node["end"])] = {"fs": dist + (crash_coef * next_node["dist"]),
														"tf": dist_between_nodes(tuple(next_node["end"]), end_node[0]),
														"path": dist_so_far.get(start_node[0])["path"] + [tuple(next_node["end"])] }
			else:  #update shortest dist to node value in queue
				if dist + (crash_coef * next_node["dist"]) < dist_so_far[tuple(next_node["end"])][0]:
					dist_so_far[tuple(next_node["end"])] = {"fs": dist + (crash_coef * next_node["dist"]),
															"tf": dist_between_nodes( tuple(next_node["end"]), end_node[0] ),
															"path": dist_so_far.get(start_node[0])["path"] + [tuple(next_node["end"])] }

		#return from queue possible next nodes to check 
		#available_unvisited = {k: dist_so_far[k]["fs"] + dist_so_far[k]["tf"] for k in dist_so_far  }
		#THIS IS THE RIGHT ONE:
		available_unvisited = {k: dist_so_far[k]["fs"] + dist_so_far[k]["tf"] for k in dist_so_far if k not in visited  }
		best_to_dest = min(available_unvisited, key=lambda x: available_unvisited[x] ) #first check node in queue that is closest to destination
		

		print("####", dist_between_nodes(best_to_dest, end_node[0]))
		start_node_ref = this_slice.get( best_to_dest )
		if start_node_ref == None:
			#print( "MOVE TO NEW DICT SLICE" )
			call_slice_count += 1
			this_slice = call_slice(best_to_dest, sliced_dict)
			start_node_ref = this_slice.get( best_to_dest )
		start_node = [best_to_dest, this_slice.get( best_to_dest)]
		dist = dist_so_far[best_to_dest]["fs"]

delco_network_datafile = '../../osmdata/matched-osm-delco.json'
with open(delco_network_datafile) as data_file:    
    ac_network_data = json.load(data_file)

prep_network = prep_network_graph(ac_network_data)
sliced_dict = split_geo_dict( prep_network, 20 )

# sample data points in Delaware County, PA 
home = tuple([-75.345943, 39.903247])
swat = tuple([-75.355627, 39.907071])
media = tuple([-75.391199, 39.922603])
ford = tuple([-75.311294, 40.005358])
#a_star = dijkstra( home, ford, ac_network_data )
search_result = search(home, media, prep_network, sliced_dict ) 
print(  "Reached destination with path of length", len(search_result["path"]) ) 

#python map_matching.py ../../delco/delco_crash_data_fullfield.json ../../osmdata/delcoosm_network.json ../../osmdata/matched-osm-delco.json 100

