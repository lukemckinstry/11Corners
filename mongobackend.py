
#convert geojson data (composed of LineString or MultLineString features) to network graph
import json
import pymongo
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['delco-network']
print("derp")


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


def prep_slice_dict(feature_dict, slice_network, NUM_SLICES):
	slice_max = max([key[0] for key in feature_dict])
	slice_min = min([key[0] for key in feature_dict])
	incrementer = (slice_max - slice_min) / NUM_SLICES
	for i in range(0, NUM_SLICES):
		slice_network[tuple([slice_max - ( incrementer * i), slice_max - ( incrementer * (i+1)) ])] = {}
	return

def make_slices(feature_dict, slice_network):
	slice_keys = [k for k in slice_network]
	print( "slice keys",  slice_keys )
	for feature in feature_dict:
		insert_key = [k for k in slice_keys if feature[0] <= k[0] and feature[0] >= k[1] ][0]
		slice_network[insert_key][str(feature).replace('.','&#46;')] = feature_dict[feature]
		#str(feature).replace('.','&#46;')
	return

def insert_to_mongo( slice_network ):
	for slice_key in slice_network:
		print(  "HAPPENING ", slice_key)
		db.slices.save( { str(slice_key).replace('.','&#46;') : slice_network[slice_key] } )


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
	NUM_SLICES = 10
	features = get_data(infile)
	total = len(features)
	print( total )

	slice_network = {}
	prep_slice_dict( features, slice_network, NUM_SLICES )
	make_slices( features, slice_network )
	#insert_to_mongo( slice_network )
	
	return

#sample input/output files
outfile = ''
infile = '../../osmdata/compress_delco.geojson'

main(infile, outfile)