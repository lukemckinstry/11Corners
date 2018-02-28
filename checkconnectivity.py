
#convert geojson data (composed of LineString or MultLineString features) to network graph
import json
from math import sqrt

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


def get_points_in_line(feature_geometry):
	#handle geojson data types
	if feature_geometry['type'] == 'LineString':
		return feature_geometry['coordinates']
	if feature_geometry['type'] != 'LineString':
		return [item for sublist in feature_geometry['coordinates'] for item in sublist]

def add_points_to_graph(points_in_line, network_graph):
	# walk through geojson data to build network graph
	for p in range(len(points_in_line)):
		
		#assign current point in LineString, this will be node ID
		this_point = tuple( points_in_line[p] )

		#assign previous and next points in linestring, edges will connect to these nodes
		if (p > 0):
			prev_point = tuple(points_in_line[p-1])
			prev_point_dist = sqrt( (this_point[0] - prev_point[0])**2 + (this_point[1] - prev_point[1])**2 )
			prev_point_obj = {"end": prev_point, "dist": prev_point_dist}
		else: #first point in LineString has no previous point
			prev_point = None

		if p < (len( points_in_line) -1):
			next_point = tuple(points_in_line[p+1])
			next_point_dist = sqrt( (this_point[0] - next_point[0])**2 + (this_point[1] - next_point[1])**2 )
			next_point_obj = {"end": next_point, "dist": next_point_dist}
		else: #last point in LineString has no next point
			next_point = None
		
		if str(this_point) not in network_graph: #add new node to network graph
			network_graph[str(this_point)] = []
			if prev_point != None: network_graph[str(this_point)].append(prev_point_obj)
			if next_point != None: network_graph[str(this_point)].append(next_point_obj)
		else: #add new edges to existing node
			if prev_point not in network_graph[str(this_point)] and prev_point != None: network_graph[str(this_point)].append(prev_point_obj)
			if next_point not in network_graph[str(this_point)] and next_point != None: network_graph[str(this_point)].append(next_point_obj)

def process_feature(feature, network_graph):
	#Get points in feature (e.g. LineString) and assign them to network graph
	#feature_geometry = feature['geometry']
	#if feature_geometry['type'] != 'Point':
	print("######", len(feature))
	# if len(feature) != 2:
	# 	network_graph[]




		#points_in_line = get_points_in_line(feature_geometry)
		#add_points_to_graph(points_in_line, network_graph)
	return

def connectivity(feature_dict, total):
	#Walk through each feature in geojson data
	count = 0
	for feature in feature_dict:
		print( "FFFFFFFF", type(feature) )
		print( "******",  feature_dict[feature] )
		#for node in feature_dict[feature]:
		#	print( "###### ", node )
		#	print( feature_dict[ tuple(node['end']) ] )
		if len(feature_dict[feature]) <=2:
			#print( len([ feature_dict[ tuple(node['end']) ] for node in feature_dict[feature]  ]) )
			results = [ feature_dict[ tuple(node['end']) ] for node in feature_dict[feature]  ] 
			for i in results:
				if feature not in [ tuple(j['end']) for j in i]:
					count += 1
					print(feature_dict[feature])
	print( "COUNT VON COUNT", count)
	return

def add_easy_nodes(feature_dict, compress_graph, total):
	#Walk through each feature in geojson data
	for c_node in compress_graph:
		print("C_NODE**********", c_node )
		for fd_c_node_endpoint in feature_dict[c_node]:
			#if node is not 2 way node, add it	
			feature_dict_node = feature_dict[ tuple(fd_c_node_endpoint['end'])]
			if len( feature_dict_node ) != 2:
				compress_graph[c_node].append( {'end': fd_c_node_endpoint['end'], 'dist': fd_c_node_endpoint['dist']  } )
			#if node is len 2, we need to crawl
			else:
				#print( "2 WAY FEATURE DICT NODE", feature_dict_node )
				terminal_node = crawl_2_way_node( c_node, feature_dict_node, feature_dict)
				#print( "RETURNED TERMINAL NODE", terminal_node  )
				compress_graph[c_node].append( {'end': terminal_node } )
	return

def crawl_2_way_node(c_node, feature_dict_node, feature_dict):
	print("CRAWL")	
	next_node = get_other_side_of_two_way_node( c_node, feature_dict_node )
	new_c_node = next_node
	#print( "SELECTED NEXT NODE/OTHER SIDE NODE", next_node )
	#print( "LEN NEXT NODE", len(feature_dict[ tuple(next_node)]) )
	if len(feature_dict[ tuple(next_node)]) != 2:
		# print( "LEN NEXT NODE", feature_dict[ tuple(next_node)]  )
		# print( "NEXT NODE", next_node )
		return next_node
	else:
		
		new_feature_dict_node = feature_dict[ tuple(new_c_node) ]
		
		print("NEW FD NODE", new_c_node,  new_feature_dict_node  )
		#print("RECURSE ITS 2 WAY NODE", next_node, feature_dict_node   )
		return crawl_2_way_node( new_c_node, new_feature_dict_node, feature_dict)


def get_other_side_of_two_way_node( c_node, two_way_node ):
	# print("GET OTHER SIDE")
	print("STARTING NODE", c_node)
	print("TO CHOOSE FROM 1", two_way_node[0]['end'])
	print("TO CHOOSE FROM 1", two_way_node[1]['end'])

	print( c_node == tuple(two_way_node[0]['end']) )
	print( c_node == tuple(two_way_node[1]['end']) )


	if c_node == tuple( two_way_node[0]['end'] ):
		print( "return ", two_way_node[1]['end']  )
		return two_way_node[1]['end']
	if c_node == tuple( two_way_node[1]['end'] ):
		print( "return ", two_way_node[0]['end']  )
		return two_way_node[0]['end']
	else:
		print("WOMP")



def sanity_check(network_graph):
	big_points = 0
	total = 0
	for i in network_graph:	
		total += 1
		try:
			if len( network_graph[i] ) > 2:
				big_points += 1
		except:
			print(i)
			pass
	print("total " , total) 
	print("big_points ", big_points)
	return

def glance(compress_graph):
	
	for n in compress_graph:
		print( compress_graph[n] )

def write_to_file(network_graph, outfile):
	with open(outfile, 'w') as write_file:
		json.dump(network_graph, write_file)
	return

def main(infile, outfile):
	features = get_data(infile)
	total = len(features)
	print( total )
	connectivity(features, total)
	
	#glance( compress_graph )
	# sanity_check(network_graph)
	# write_to_file(network_graph, outfile)
	return

#sample input/output files
infile = '../../osmdata/delcoosm_network.json'
outfile = '../../osmdata/compress_delco.geojson'

main(infile, outfile)
