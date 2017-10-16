
#Dijkstra implementation to search a network graph. 
#Start, finish and all nodes have lon/lat labels. 
#Search is directed to favor points closer to destination for performance

import json
from math import sqrt

#network graph of geographic data
ac_network_datafile = 'ac_network_crashes_distributed_FULL.json'

def string_to_float(input_string):
	#*utility function bc json dict keys must be strings, in algo we need floats 
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

def dist_between_nodes(base_node, dest_node):
	#* both inputs should be float tuples
	return sqrt( (base_node[0] - dest_node[0])**2 + (base_node[1] - dest_node[1])**2 )

def find_nearest_node(input_point, network_data):
	#* Map Matching, input coordinates, return closest node from network graph
	iterable_network_dict = iter(network_data)
	nearest_point = string_to_float(next(iterable_network_dict) ) 
	nearest_dist = dist_between_nodes(input_point, nearest_point)
	for raw_point in network_data:
		point = string_to_float(raw_point)
		dist = dist_between_nodes(input_point, point)
		if dist < nearest_dist:
			nearest_dist = dist
			nearest_point = point
	return nearest_point

with open(ac_network_datafile) as data_file:    
    ac_network_data = json.load(data_file)

#sample points in Allegheny County
phipps =  tuple([-79.947843, 40.438784])
pnc_park = tuple([-80.005655, 40.447083])
near_pnc_park = tuple([-80.016136, 40.452080] )
heinz_field = tuple([-80.017552, 40.447802])
search_start_node_id = find_nearest_node( phipps , ac_network_data )
search_end_node_id = find_nearest_node( heinz_field, ac_network_data )

visited = [] #init dijkstra visited list
dist_so_far = {} #dijkstra queue
dist_so_far[search_start_node_id] = [0, dist_between_nodes(search_start_node_id, search_end_node_id)]
#each node is two-item list... [tuple w/ lon/lat coords as floats, dict for each adjacent node w/ weight (i.e. dist, safety score) & coords]
start_node = [search_start_node_id, ac_network_data.get( str(search_start_node_id) )]
end_node = [search_end_node_id, ac_network_data.get( str(search_end_node_id) )]
G = ac_network_data
def dijkstra( start_node, end_node ):
	dist = 0
	found_it = False
	while found_it == False:
		visited.append(tuple(start_node[0]))
		print("visited ", len(visited))
		next_nodes = [ d for d in start_node[1] if "c_pt" not in d.keys() ]  #get adjacent nodes
		if start_node == end_node:
			print("FINISH")
			found_it = True
			return
		for next_node in next_nodes:
			if tuple(next_node["end"]) not in [i[0] for i in dist_so_far]:	#add new node to queue	
				dist_so_far[tuple(next_node["end"])] = [dist + next_node["dist"], dist_between_nodes(tuple(next_node["end"]), end_node[0]  )]
			else:  #update shortest dist to node value in queue
				if dist + next_node["dist"] < dist_so_far[tuple(next_node["end"])][0]:
					dist_so_far[tuple(next_node["end"])] = [dist + next_node["dist"], dist_between_nodes( tuple(next_node["end"]), end_node[0] )]
		#return from queue possible next nodes to check 
		available_unvisited = {k: [dist_so_far[k][0], dist_so_far[k][1]] for k in dist_so_far if k not in visited  }
		nearest_to_dest = min(available_unvisited, key=lambda x: available_unvisited[x][1] ) #first check node in queue that is closest to destination
		start_node = [nearest_to_dest, ac_network_data.get(str(nearest_to_dest))]
		dist = dist_so_far[nearest_to_dest][0]

dijkstra(start_node, end_node )
