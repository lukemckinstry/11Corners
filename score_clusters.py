import json
import matplotlib.pyplot as plt

#convert dict key from string to floats
def string_to_float(input_string):
	item = input_string.split(",")
	return tuple([ float(point.replace("(","").replace(")","")) for point in item])
 
def get_crash_data(crash_datafile):
	with open(crash_datafile) as data_file:    
	    crash_data = json.load(data_file)
	crash_dict = {}
	for crash_point in crash_data:
		try:
			lon_lat_key = tuple([string_to_float(crash_point)[1], string_to_float(crash_point)[0]])
			crash_dict[lon_lat_key] = crash_data[crash_point]
		except:
			pass
	return crash_dict

def get_breakpoints( crash_dict, num_breakpoints  ):
	#specify breakpoints in longitude to subdivide network graph and crash points
	crash_lon_min = min([k[0] for k in crash_dict.keys()])
	crash_lon_max = max([k[0] for k in crash_dict.keys()])
	#print( "MAX MIN  ---> ", crash_lon_max, crash_lon_min )
	split = abs(crash_lon_max - crash_lon_min) /num_breakpoints
	breakpoints = [ crash_lon_min + i*split for i in range(num_breakpoints + 1)  ]
	#print("MAX MIN  ---> ", max(breakpoints), min(breakpoints) )
	return breakpoints

def split_crash_dict( crash_data, breakpoints ):
	#slice crash data
	split_dicts_list = [{} for _ in range(len(breakpoints)-1)]
	for i in range( len(breakpoints)-1 ):
		print(i / len(breakpoints) * 100)
		split_dicts_list[i] = { k: crash_data[k] for k in crash_data if breakpoints[i]<k[0]<breakpoints[i+1] }
	return split_dicts_list

def iterate_through_crashes( crash_dict_object, breakpoints, output_dict ):
	# iterate through each crash point to assign it to network graph
	for i in range(len(breakpoints)-1):
	#for i in range(3):	
		print( "PROGRESS ", i/len(breakpoints) * 100  )
		
		for this_crash_point in crash_dict_object[i]: #current graph point to pass through dist and assignment functions

			weight = find_nearby_crash_points( this_crash_point, crash_dict_object[i])
			output_dict[this_crash_point] = weight
			#assign_to_node( sub_dict, crash_dict_object, this_crash_point, nearest_graph_edge)
	return

def find_nearby_crash_points(crash_point, crash_dict_slice):
	#before iterating through each crash point, get small dict of nearby points 
	ct = crash_point
	x_margin = ct[0] * .00001 #buffer size
	y_margin = ct[1] * .00001
	xb = [ ct[0]-x_margin, ct[0]+x_margin ] # margin based on buffer
	yb = [ ct[1]-y_margin, ct[1]+y_margin ]
	#print( ct, xb, yb )
	sub_dict = {k for k in crash_dict_slice if xb[0]>k[0]>xb[1] and yb[0]<k[1]<yb[1] } # nearby points, next check which is nearest
	#print(  "NEARBY POINTS .00001 --> ", len(sub_dict))
	#return sub_dict
	return len(sub_dict)

def viz_data( output_dict):
	crash_totals = [output_dict[k] for k in output_dict]
	bins = []
	for i in range( max(crash_totals) ): bins.append(i) 
	plt.hist(crash_totals, bins='auto')  # arguments are passed to np.histogram
	plt.title("Histogram with 'auto' bins")
	plt.show()
	return

def write_to_file(crash_outfile, output_dict):
	write_dict = {}
	for pt in output_dict:
		write_dict[str(pt)] = output_dict[pt]
	with open(crash_outfile, 'w') as outfile:
		json.dump(write_dict, outfile)
	return

def main(crash_datafile, breakpoints_input, crash_outfile):
	crash_dict = get_crash_data(crash_datafile)
	print("HERE", len(crash_dict))
	breakpoints = get_breakpoints( crash_dict, int(breakpoints_input) )  #number of breakpoints specific by command line input
	print("HERE1")
	crash_dict_object = split_crash_dict( crash_dict, breakpoints )
	output_dict = {}
	iterate_through_crashes(crash_dict_object, breakpoints, output_dict)
	viz_data( output_dict)
	write_to_file(crash_outfile, output_dict)
	return

crash_datafile = '../../PA/pa_crash_data_light.json'
crash_outfile = '../../PA/pa_weighted_crashes.json'
breakpoints_input = 500

main(crash_datafile, breakpoints_input, crash_outfile)

