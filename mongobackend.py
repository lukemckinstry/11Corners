
#convert geojson data (composed of LineString or MultLineString features) to network graph
import json
import pymongo
from pymongo import MongoClient
import math

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


def prep_slice_dict(feature_dict, slice_network):
	slices = set([ math.floor(f[0] / 0.05) * 0.05 for f in feature_dict  ])
	for s in slices:
		subdict = { str(x).replace('.','&#46;'): feature_dict[x] for x in feature_dict if x[0] >= s and x[0] < s + 0.05}
		slice_network[ tuple([s,s+0.05])] = subdict	
	return

def insert_to_mongo( slice_network ):
	for slice_key in slice_network:
		print(  "HAPPENING ", slice_key)
		db.slices.save( { 'latmin': slice_key[0], 'latmax':slice_key[1], 'nodes' : slice_network[slice_key] } )
	return

def querymongo():
	slices = db.slices
	cursor = slices.find( {})
	for document in cursor:
          print( document['latmin'], document['latmax'])
          print( len(document['nodes']) )
	#print(  "GOT A SLICE", len( slice_obj  ))
	#print( slice_obj )
	print( "OUR WORK IS FINISHED" )
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
	

	slice_network = {}
	prep_slice_dict( features, slice_network )
	insert_to_mongo( slice_network )

	querymongo()
	
	return

#sample input/output files
outfile = ''
infile = '../../osmdata/compress_delco.geojson'

main(infile, outfile)