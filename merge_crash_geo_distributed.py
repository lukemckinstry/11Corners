import json
from math import sqrt

#read in and process crash data, create list of lon,lat tuples of floats
crash_datafile = 'crash_data_sorted_lonlat.json'
ac_geo_network_datafile = 'ac_network_geo_coords.json'
with open(crash_datafile) as data_file:    
    crash_data = json.load(data_file)
crash_tuples = []
for crash_point in crash_data:
	point_tuple = tuple(crash_point)
	crash_tuples.append(point_tuple)
print( "Number of Allegheny County crashes", len(crash_tuples))

#json requires dict key be stored as string, but after reading in data 
#this function converts key back into lon, lat tuple of floats
def string_to_float(input_string):
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])

with open(ac_geo_network_datafile) as data_file:    
    geo_network_data = json.load(data_file)

geo_network_keys_lon = [string_to_float(k)[0] for k in geo_network_data.keys()]
print("Num Allegheny County road map nodes ", len(geo_network_keys_lon) )
network_lon_min = min(geo_network_keys_lon)
network_lon_max = max(geo_network_keys_lon )
fifth_range_lon = abs(network_lon_max - network_lon_min) /5

#create break points based on longitude to divide map data nodes into smaller pots to speed map matching of crash points
break_one = network_lon_min + fifth_range_lon
break_two = network_lon_min + (fifth_range_lon * 2)
break_two_2 = network_lon_min + (fifth_range_lon * 2.3)
break_two_3 = network_lon_min + (fifth_range_lon * 2.6)
break_two_4 = network_lon_min + (fifth_range_lon * 2.8)
break_three = network_lon_min + (fifth_range_lon * 3)
break_three_2 = network_lon_min + (fifth_range_lon * 3.2)
break_three_3 = network_lon_min + (fifth_range_lon * 3.4)
break_three_4 = network_lon_min + (fifth_range_lon * 3.6)
break_four = network_lon_min + (fifth_range_lon * 4)
print("Breaks: ", break_one, break_two, break_three, break_four )

#use these variables to check stats after map matching of crash points
bad_counter = 0
subCounter = 0
counter = 0
doubles = 0
triples = 0

total = len(crash_tuples)
searchable_dict_one = {}
searchable_dict_two = {}
searchable_dict_three = {}
searchable_dict_three_2 = {}
searchable_dict_three_3 = {}
searchable_dict_three_4 = {}
searchable_dict_four = {}
searchable_dict_four_2 = {}
searchable_dict_four_3 = {}
searchable_dict_four_4 = {}
searchable_dict_five = {}

#assign road map nodes points to smaller searchable dictionaries based on longtitude break points
for i in geo_network_data:
	k = string_to_float(i)
	if k[0] < break_one:
		searchable_dict_one[k] = geo_network_data[i]
	if  break_one <=  k[0] < break_two:
		searchable_dict_two[k] = geo_network_data[i]
	if  break_two <=  k[0] < break_two_2:
		searchable_dict_three[k] = geo_network_data[i]
	if  break_two_2 <=  k[0] < break_two_3:
		searchable_dict_three_2[k] = geo_network_data[i]
	if  break_two_3 <=  k[0] < break_two_4:
		searchable_dict_three_3[k] = geo_network_data[i]
	if  break_two_4 <=  k[0] < break_three:
		searchable_dict_three_4[k] = geo_network_data[i]
	if  break_three <=  k[0] < break_three_2:
		searchable_dict_four[k] = geo_network_data[i]
	if  break_three_2 <=  k[0] < break_three_3:
		searchable_dict_four_2[k] = geo_network_data[i]
	if  break_three_3 <=  k[0] < break_three_4:
		searchable_dict_four_3[k] = geo_network_data[i]
	if  break_three_4 <=  k[0] < break_four:
		searchable_dict_four_4[k] = geo_network_data[i]
	if  break_four <=  k[0]:
		searchable_dict_five[k] = geo_network_data[i]

#check searchable dicts are fairly even in size 
print("one dict", len(searchable_dict_one))
print("two dict", len(searchable_dict_two))
print("three dict", len(searchable_dict_three))
print("three2 dict", len(searchable_dict_three_2))
print("three3 dict", len(searchable_dict_three_3))
print("three4 dict", len(searchable_dict_three_4))
print("four dict", len(searchable_dict_four))
print("four dict2", len(searchable_dict_four_2))
print("four dict3", len(searchable_dict_four_3))
print("four dict4", len(searchable_dict_four_4))
print("five dict", len(searchable_dict_five))

#make iterator for each searchable dict
search_dict_iterator_one = searchable_dict_one.items()
search_dict_iterator_two = searchable_dict_two.items()
search_dict_iterator_three = searchable_dict_three.items()
search_dict_iterator_three_2 = searchable_dict_three_2.items()
search_dict_iterator_three_3 = searchable_dict_three_3.items()
search_dict_iterator_three_4 = searchable_dict_three_4.items()
search_dict_iterator_four = searchable_dict_four.items()
search_dict_iterator_four_2 = searchable_dict_four_2.items()
search_dict_iterator_four_3 = searchable_dict_four_3.items()
search_dict_iterator_four_4 = searchable_dict_four_4.items()
search_dict_iterator_five = searchable_dict_five.items()

#run through crash data points, assign each to road map node if one is nearby (within .00001 radians) else dont assign it
for ct in crash_tuples:
	counter += 1
	print( counter, float(counter) * 1.00000 / float(total)  )
	x_margin = ct[0] * .000010
	y_margin = ct[1] * .000010
	#set x bound and y bound so we can run find nearest on smaller set of nearby points (sub_dict) from searchable dict for performance
	xb = [ ct[0]-x_margin, ct[0]+x_margin ]
	yb = [ ct[1]-y_margin, ct[1]+y_margin ]
	if ct[0] < break_one:
		sub_dict = {k: v for k, v in search_dict_iterator_one if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_one <= ct[0] < break_two:
		sub_dict = {k: v for k, v in search_dict_iterator_two if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_two <= ct[0] < break_two_2:
		sub_dict = {k: v for k, v in search_dict_iterator_three if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_two_2 <= ct[0] < break_two_3:
		sub_dict = {k: v for k, v in search_dict_iterator_three_2 if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_two_3 <= ct[0] < break_two_4:
		sub_dict = {k: v for k, v in search_dict_iterator_three_3 if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_two <= ct[0] < break_three:
		sub_dict = {k: v for k, v in search_dict_iterator_three_4 if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_three <= ct[0] < break_three_2:
		sub_dict = {k: v for k, v in search_dict_iterator_four if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_three_2 <= ct[0] < break_three_3:
		sub_dict = {k: v for k, v in search_dict_iterator_four_2 if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_three_3 <= ct[0] < break_three_4:
		sub_dict = {k: v for k, v in search_dict_iterator_four_3 if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_three_4 <= ct[0] < break_four:
		sub_dict = {k: v for k, v in search_dict_iterator_four_4 if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }
	if break_four <= ct[0]:
		sub_dict = {k: v for k, v in search_dict_iterator_five if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] }

	#within subdict, find nearest node to which crash point will be assigned
	if len(sub_dict) > 0:
		iterable_sub_dict = iter(sub_dict)
		nearest_point = next(iterable_sub_dict)  
		nearest_dist = sqrt( (ct[0] - nearest_point[0])**2 + (ct[1] - nearest_point[1])**2 )
		for sub_point in sub_dict:
			dist = sqrt( (ct[0] - sub_point[0])**2 + (ct[1] - sub_point[1])**2 )
			if dist < nearest_dist:
				nearest_dist = dist
				nearest_point = sub_point


		try:
			if ct[0] < break_one:
				searchable_dict_one.get(  nearest_point).append( { "c_pt": ct } )
			if break_one <= ct[0] < break_two:
				searchable_dict_two.get(  nearest_point).append( { "c_pt": ct } )	
			if break_two <= ct[0] < break_two_2:
				searchable_dict_three.get(  nearest_point).append( { "c_pt": ct } )
			if break_two_2 <= ct[0] < break_two_3:
				searchable_dict_three_2.get(  nearest_point).append( { "c_pt": ct } )
			if break_two_3 <= ct[0] < break_two_4:
				searchable_dict_three_3.get(  nearest_point).append( { "c_pt": ct } )		
			if break_two_4 <= ct[0] < break_three:
				searchable_dict_three_4.get(  nearest_point).append( { "c_pt": ct } )
			if break_three <= ct[0] < break_three_2:
				searchable_dict_four.get(  nearest_point).append( { "c_pt": ct } )
			if break_three_2 <= ct[0] < break_three_3:
				searchable_dict_four_2.get(  nearest_point).append( { "c_pt": ct } )
			if break_three_3 <= ct[0] < break_three_4:
				searchable_dict_four_3.get(  nearest_point).append( { "c_pt": ct } )
			if break_three_4 <= ct[0] < break_four:
				searchable_dict_four_4.get(  nearest_point).append( { "c_pt": ct } )
			if break_four <= ct[0]:
				searchable_dict_five.get(  nearest_point).append( { "c_pt": ct } )
		except:
			#track crash points directed to wrong searchable dict
			bad_counter += 1

	# if counter > 10000:
	# 	break

#combine searchable dicts back together into one dataset, the searchable network graph
output_dict = {}
for item in searchable_dict_one:
	output_dict[ str(item) ] = searchable_dict_one[item]
for item in searchable_dict_two:
	output_dict[ str(item) ] = searchable_dict_two[item]
for item in searchable_dict_three:
	output_dict[ str(item) ] = searchable_dict_three[item]
for item in searchable_dict_three_2:
	output_dict[ str(item) ] = searchable_dict_three_2[item]
for item in searchable_dict_three_3:
	output_dict[ str(item) ] = searchable_dict_three_3[item]
for item in searchable_dict_three_4:
	output_dict[ str(item) ] = searchable_dict_three_4[item]
for item in searchable_dict_four:
	output_dict[ str(item) ] = searchable_dict_four[item]
for item in searchable_dict_four_2:
	output_dict[ str(item) ] = searchable_dict_four_2[item]
for item in searchable_dict_four_3:
	output_dict[ str(item) ] = searchable_dict_four_3[item]
for item in searchable_dict_four_4:
	output_dict[ str(item) ] = searchable_dict_four_4[item]	
for item in searchable_dict_five:
	output_dict[ str(item) ] = searchable_dict_five[item]



#sanity check of metadata for each network node
for item in output_dict:
	network_meta_keys = [ ip for i in [ list(f) for f in output_dict[item] ] for ip in i ]
	if network_meta_keys.count("c_pt") == 1:
	 	subCounter += 1
	if network_meta_keys.count("c_pt") == 2:
	 	subCounter += 1
	 	doubles += 1
	if network_meta_keys.count("c_pt") >= 3:
	 	subCounter += 1
	 	doubles += 1
	 	triples += 1

print(subCounter, doubles, triples, counter)
print(bad_counter)

#read output dictionary (searchable network graph) to json file
with open('ac_network_crashes_distributed_FULL.json', 'w') as outfile:
 json.dump(output_dict, outfile)
