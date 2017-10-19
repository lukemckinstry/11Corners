
#convert geojson data (composed of LineString or MultLineString features) to network graph
import json
from math import sqrt
import sys

if len(sys.argv) != 3:
	print("Command Line Error: please enter infile <space> outfile ")
	sys.exit()

infile = sys.argv[1]
outfile = sys.argv[2]

#sample input/output files
# infile = 'pa.json'
# outfile = 'pa_network.json'


def get_data(geojson_datafile):
	with open(geojson_datafile) as data_file:
		data = json.load(data_file)
	return data['features']

def get_features(data):
	return data

def get_points_in_line(feature_geometry):
	if feature_geometry['type'] == 'LineString':
		return feature_geometry['coordinates']
	if feature_geometry['type'] != 'LineString':
		print(feature_geometry['type'])
		return [item for sublist in feature_geometry['coordinates'] for item in sublist]

def add_points_to_graph(points_in_line, network_graph):
	for p in range(len(points_in_line)):
		#assign current point in LineString, this will be node ID
		this_point = tuple( points_in_line[p] )
		#assign previous and next points in linestring, edges will connect current point to these nodes
		if (p > 0):
			prev_point = tuple(points_in_line[p-1])
			prev_point_dist = sqrt( (this_point[0] - prev_point[0])**2 + (this_point[1] - prev_point[1])**2 )
			prev_point_obj = {"end": prev_point, "dist": prev_point_dist}
		else:
			prev_point = None

		if p < (len( points_in_line) -1):
			next_point = tuple(points_in_line[p+1])
			next_point_dist = sqrt( (this_point[0] - next_point[0])**2 + (this_point[1] - next_point[1])**2 )
			next_point_obj = {"end": next_point, "dist": next_point_dist}
		else:
			next_point = None
		
		#add new node to network graph or add new edges to existing node
		if str(this_point) not in network_graph:
			network_graph[str(this_point)] = []
			if prev_point != None: network_graph[str(this_point)].append(prev_point_obj)
			if next_point != None: network_graph[str(this_point)].append(next_point_obj)
		else: 
			if prev_point not in network_graph[str(this_point)] and prev_point != None: network_graph[str(this_point)].append(prev_point_obj)
			if next_point not in network_graph[str(this_point)] and next_point != None: network_graph[str(this_point)].append(next_point_obj)

def process_feature(feature, network_graph):
	feature_geometry = feature['geometry']
	points_in_line = get_points_in_line(feature_geometry)
	add_points_to_graph(points_in_line, network_graph)
	return

def iterate_features(features, network_graph, total):
	count = 0
	for i in range(0,len(features)):
		count += 1
		#print( count / float(total) * 100.000 )
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
	print( "HOW MANY FEATURES: ", total )
	network_graph = {}
	iterate_features(features, network_graph, total)
	sanity_check(network_graph)
	write_to_file(network_graph, outfile)
	return

main(infile, outfile)
