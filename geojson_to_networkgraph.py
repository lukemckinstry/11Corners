
#convert geojson data (composed of LineString or MultLineString features) to network graph
import json
from math import sqrt

def get_data(geojson_datafile):
	with open(geojson_datafile) as data_file:
		data = json.load(data_file)
	return data['features']

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
	feature_geometry = feature['geometry']
	points_in_line = get_points_in_line(feature_geometry)
	add_points_to_graph(points_in_line, network_graph)
	return

def iterate_features(features, network_graph, total):
	#Walk through each feature in geojson data
	for i in range(0,len(features)):
		process_feature(features[i], network_graph)
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

def write_to_file(network_graph, outfile):
	with open(outfile, 'w') as write_file:
		json.dump(network_graph, write_file)
	return

def main(infile, outfile):
	features = get_data(infile)
	total = len(features)
	network_graph = {}
	iterate_features(features, network_graph, total)
	sanity_check(network_graph)
	write_to_file(network_graph, outfile)
	return

#sample input/output files
# infile = 'pa.json'
# outfile = 'pa_network.json'

main(infile, outfile)
