
#convert geojson data (composed of LineString or MultLineString features) to network graph
import json
from pprint import pprint
from math import sqrt

ac = 'psu_roads/AC/ac_geo_coords.json'

#read in data from geojson file with LineString features
with open(ac) as data_file:    
    data = json.load(data_file)
collecting_dict = {}
print( "Number of features in this data set:", len(data['features']) )

count = 0

for i in range(0,len(data['features'])):
  
	if data['features'][i]['geometry']['type'] == 'LineString':
		points_in_line = data['features'][i]['geometry']['coordinates']
	#flatten MultiLineString features so they become a LineString
	if data['features'][i]['geometry']['type'] != 'LineString':
		points_in_line = [item for sublist in data['features'][i]['geometry']['coordinates'] for item in sublist]
		count += 1
	
	for p in range(len(points_in_line)):	
		#assign current point in LineString, this will we node ID
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
		if str(this_point) not in collecting_dict:
			collecting_dict[str(this_point)] = []
			if prev_point != None: collecting_dict[str(this_point)].append(prev_point_obj)
			if next_point != None: collecting_dict[str(this_point)].append(next_point_obj)
		else: 
			if prev_point not in collecting_dict[str(this_point)] and prev_point != None: collecting_dict[str(this_point)].append(prev_point_obj)
			if next_point not in collecting_dict[str(this_point)] and next_point != None: collecting_dict[str(this_point)].append(next_point_obj)

print( "count", count)

#sanity check
big_points = 0
total = 0
for i in collecting_dict:	
	total += 1
	try:
		if len( collecting_dict[i] ) > 2:
			big_points += 1
	except:
		print(i)
		pass
print("total " , total) 
print("big_points ", big_points)

#read dictionary out to json file
with open('ac_network_geo_coords.json', 'w') as outfile:
    json.dump(collecting_dict, outfile)