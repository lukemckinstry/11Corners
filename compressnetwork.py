
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

def create_compress_graph(feature_dict, compress_graph, total):
	#Walk through each feature in geojson data
	for feature in feature_dict:
		if len(feature_dict[feature]) != 2:
			compress_graph[feature] = []
		#process_feature(feature_dict[feature], compress_graph)
	return

def rewrite_nodes(feature_dict, compress_graph, total):
	#Walk through each feature in geojson data
	for c_node in compress_graph:
		#print("C_NODE**********", c_node )
		for end_point in feature_dict[c_node]:
			#print("ENDPOINT$$$$", end_point)
			#if node is not 2 way node, add it	
			feature_dict_node = feature_dict[ tuple(end_point['end'])]
			if len( feature_dict_node ) != 2:
				compress_graph[c_node].append( {'end': end_point['end'], 'dist': end_point['dist']  } )
			#if node is len 2, we need to crawl
			else:
				#print("end_point", end_point['end']  )
				#print("2 WAY NODE", feature_dict_node )

				terminal_node = crawl_2_way_node( c_node, tuple(end_point['end']) , feature_dict)
				compress_graph[c_node].append( {'end': terminal_node } )
	return

def crawl_2_way_node(prev_node, current_node, feature_dict):
	#print("CRAWL --> c_node", current_node)	
	next_node = get_other_side_of_two_way_node( prev_node, current_node, feature_dict )#
	if len(feature_dict[ tuple(next_node)]) != 2:
		return next_node
	else:
		#print( "NEXT NODE of", str(next_node),  feature_dict[tuple(next_node)] )		
		return crawl_2_way_node(current_node, tuple(next_node), feature_dict)


def get_other_side_of_two_way_node( visited_node, current_node, feature_dict ):
	# print("CURRENT NODE", current_node)
	# print("VISITED NODE", visited_node)
	# print("TO CHOOSE FROM 0", tuple(feature_dict[current_node][0]['end']  ) == visited_node )
	# print("TO CHOOSE FROM 1", tuple(feature_dict[current_node][1]['end']  ) == visited_node )
	# print("TO CHOOSE FROM 0", tuple(feature_dict[current_node][0]['end']  )  )
	# print("TO CHOOSE FROM 1", tuple(feature_dict[current_node][1]['end']  )  )
	if visited_node == tuple(feature_dict[current_node][0]['end']):
		#print("returning ", feature_dict[current_node][1]['end']) 
		return tuple(feature_dict[current_node][1]['end'])
	if visited_node == tuple(feature_dict[current_node][1]['end']):
		#print("returning ", feature_dict[current_node][0]['end']) 
		return tuple(feature_dict[current_node][0]['end'])
	else:
		print("NEITHER")
	return

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
	create_compress_graph(features, compress_graph, total)
	rewrite_nodes(features, compress_graph, total)
	glance( compress_graph )
	print( len(compress_graph) )
	write_to_file(compress_graph, outfile)
	return

#sample input/output files
infile = '../../osmdata/delcoosm_network.json'
outfile = '../../osmdata/compress_delco.geojson'

main(infile, outfile)
