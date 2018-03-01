
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

def create_compress_graph(feature_dict, compress_graph):
	for feature in feature_dict:
		if len(feature_dict[feature]) != 2:
			compress_graph[feature] = []
	return

def rewrite_nodes(feature_dict, compress_graph):
	#create compress graph
	create_compress_graph(feature_dict, compress_graph)
	#Walk through each feature in geojson data
	for c_node in compress_graph:
		#print("C_NODE**********" )
		
		for end_point in feature_dict[c_node]:
			#print("ENDPOINT$$$#############$")
			#if node is not 2 way node, add it	
			
			feature_dict_node = feature_dict[ tuple(end_point['end'])]
			if len( feature_dict_node ) != 2:
				compress_graph[c_node].append( {'end': end_point['end'],
												'dist': end_point['dist'],
												'st': end_point['st']  } )
			#if node is len 2, we need to crawl
			else:
				#print("NAME OF STREET FOR TWO WAY NODE ", end_point['st'])
				terminal_node, dist, street_name = crawl_2_way_node( c_node, tuple(end_point['end']) , feature_dict)
				#print( "RETURNED TERMINAL NODE ", street_name )
				compress_graph[c_node].append( {'end': terminal_node, 'dist': dist, 'st': street_name } )
	return

def crawl_2_way_node(prev_node, current_node, feature_dict):
	# if  feature_dict[current_node][0]["st"] != feature_dict[current_node][1]["st"]:
	# 	print("YIKES" , feature_dict[current_node] )
	next_node, dist, street_name = get_other_side_of_two_way_node( prev_node, current_node, feature_dict )#
	#print( "next_node -> ", next_node, " -> ", feature_dict[next_node])
	if len(feature_dict[ tuple(next_node)]) != 2:
		return next_node, dist, street_name
	else:
		return crawl_2_way_node(current_node, tuple(next_node), feature_dict)


def get_other_side_of_two_way_node( visited_node, current_node, feature_dict ):
	# print("CURRENT NODE", current_node)
	# print("VISITED NODE", visited_node)
	# print("TO CHOOSE FROM 0", tuple(feature_dict[current_node][0]['end']  ) == visited_node )
	# print("TO CHOOSE FROM 1", tuple(feature_dict[current_node][1]['end']  ) == visited_node )
	# print("TO CHOOSE FROM 0", tuple(feature_dict[current_node][0]['end']  )  )
	# print("TO CHOOSE FROM 1", tuple(feature_dict[current_node][1]['end']  )  )
	if visited_node == tuple(feature_dict[current_node][0]['end']):
		#print("######street ", feature_dict[current_node][1]['st']) 
		#print("returning ", feature_dict[current_node][1]['end']) 
		return [tuple(feature_dict[current_node][1]['end']),
					  feature_dict[current_node][1]['dist'],
					  feature_dict[current_node][1]['st']]
	if visited_node == tuple(feature_dict[current_node][1]['end']):
		#print("######street ", feature_dict[current_node][0]['st']) 
		#print("returning ", feature_dict[current_node][0]['end']) 
		return [tuple(feature_dict[current_node][0]['end']),
					  feature_dict[current_node][0]['dist'],
					  feature_dict[current_node][0]['st']]
	else:
		print("NEITHER")
	return

def sanity_check(network_graph):
	big_points = 0
	total = 0
	total_streets = 0
	blank_streets = 0
	for i in network_graph:	
		total += 1
		try:
			if len( network_graph[i] ) > 2:
				big_points += 1
		except:
			print(i)
			pass
		for end in network_graph[i]:
			total_streets += 1
			if end['st'] == "":
				blank_streets += 1
	print("total " , total) 
	print("big_points ", big_points)
	print( "total_streets ", total_streets )
	print( "blank_streets ", blank_streets )
	return

def glance(compress_graph):
	
	for n in compress_graph:
		print( compress_graph[n] )

def write_to_file(compress_graph, outfile):
	output_graph = {}
	for g in compress_graph:
		output_graph[str(g)] = compress_graph[g]
	with open(outfile, 'w') as write_file:
		json.dump(output_graph, write_file)
	return

def main(infile, outfile):
	features = get_data(infile)
	total = len(features)
	print( total )
	compress_graph = {}
	create_compress_graph(features, compress_graph)
	rewrite_nodes(features, compress_graph)
	sanity_check( compress_graph )
	print( len(compress_graph) )
	#write_to_file(compress_graph, outfile)
	return

#sample input/output files
infile = '../../osmdata/delco/delcoosm_network-streetnames.json'
outfile = '../../osmdata/delco/compress_delco-streetnames.json'

main(infile, outfile)
