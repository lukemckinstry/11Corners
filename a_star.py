#A* search implementation for geographic network graph. 

import json
from math import sqrt

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
		point = string_to_float(raw_point)
		dist = dist_between_nodes(input_point, point)
		if dist < nearest_dist:
			nearest_dist = dist
			nearest_point = point
	return nearest_point

def search(start_point, finish_point, ac_network_data):
	nav_path = dijkstra(start_point, finish_point, ac_network_data )
	return nav_path


def dijkstra( start_point, finish_point, ac_network_data ):
	
	search_start_node_id = find_nearest_node( start_point , ac_network_data )
	search_end_node_id = find_nearest_node( finish_point, ac_network_data )
	visited = [] #init dijkstra visited list
	dist_so_far = {} # init dijkstra queue
	dist_so_far[search_start_node_id] = { "fs": 0,
										  "tf": dist_between_nodes(search_start_node_id, search_end_node_id),
										  "path":[search_start_node_id] }
	
	#each node is two-item list... [tuple w/ lon/lat coords as floats, dict for each adjacent node w/ weight (i.e. dist, safety score) & coords]
	start_node = [search_start_node_id, ac_network_data.get( str(search_start_node_id) )]
	end_node = [search_end_node_id, ac_network_data.get( str(search_end_node_id) )]
	dist = 0
	found_it = False

	while found_it == False:
		visited.append(tuple(start_node[0]))
		if len(visited) > 1000: #limit size of visited list for performance
			remove_item = visited.pop(0)
			del dist_so_far[remove_item]
		
		next_nodes = [ d for d in start_node[1] if "c_pt" not in d.keys() ]  #get adjacent nodes
		
		if start_node == end_node: #reached destination
			found_it = True
			nav_path = dist_so_far[start_node[0]]["path"] + [end_node[0]]
			return {"path":[[i[0],i[1]] for i in nav_path],"visited":visited}

		for next_node in next_nodes:
			if tuple(next_node["end"]) not in [i[0] for i in dist_so_far]:	#add new node to queue	
				dist_so_far[tuple(next_node["end"])] = {"fs": dist + next_node["dist"],
														"tf": dist_between_nodes(tuple(next_node["end"]), end_node[0]),
														"path": dist_so_far.get(start_node[0])["path"] + [tuple(next_node["end"])] }
			else:  #update shortest dist to node value in queue
				if dist + next_node["dist"] < dist_so_far[tuple(next_node["end"])][0]:
					dist_so_far[tuple(next_node["end"])] = {"fs": dist + next_node["dist"],
															"tf": dist_between_nodes( tuple(next_node["end"]), end_node[0] ),
															"path": dist_so_far.get(start_node[0])["path"] + [tuple(next_node["end"])] }

		#return from queue possible next nodes to check 
		available_unvisited = {k: dist_so_far[k]["fs"] + dist_so_far[k]["tf"] for k in dist_so_far if k not in visited  }
		best_to_dest = min(available_unvisited, key=lambda x: available_unvisited[x] ) #first check node in queue that is closest to destination
		start_node = [best_to_dest, ac_network_data.get(str(best_to_dest))]
		dist = dist_so_far[best_to_dest]["fs"]

# delco_network_datafile = 'delco_crashes_in_geo_network.json'
# with open(delco_network_datafile) as data_file:    
#     ac_network_data = json.load(data_file)

# sample data points in Delaware County, PA 
# home = tuple([-75.345943, 39.903247])
# swat = tuple([-75.355627, 39.907071])
# media = tuple([-75.391199, 39.922603])
# ford = tuple([-75.311294, 40.005358])
# a_star = dijkstra( home, ford, ac_network_data )
# print(  "Reached destination with path of length", len(a_star["path"]) ) )
