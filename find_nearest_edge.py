#algorithm to find nearest edge for point on map, to be used in map matching

def nearest_line(p1, p2, p0):
	m = (p1[1] - p2[1]) / (p1[0] - p2[0])
	# print("slope: ", m)
	inverse_m = m * -1
	# print("inverse slope: ", inverse_m)	
	numerator = abs( ((p2[0] - p1[0]) * (p1[1] - p0[1])) - ((p1[0] - p0[0]) * (p2[1] - p1[1])) )
	dist  = numerator / (((p2[0] - p1[0])**2) + ((p2[1] - p1[1])**2))**0.5
	# print("dist", dist)
	# print("p0: ", p0[0], p0[1] )
	dx =  dist * ((1/(1 + inverse_m**2))**0.5 )
	dy = inverse_m * dx
	p3 = [p0[0]-dx, p0[1]-dy]
	if p3[0] < min(p1[0], p2[0]) or p3[0] > max(p1[0], p2[0]) or p3[1] < min(p1[1], p2[1]) or p3[1] > max(p1[1], p2[1]):
		dist = min( dist_bt_nodes(p0,p1), dist_bt_nodes(p0,p2) )
	return dist
	
def dist_bt_nodes(base_node, dest_node):
	return ( (base_node[0] - dest_node[0])**2 + (base_node[1] - dest_node[1])**2 )**0.5

# p1 = [-4,4]
# p2 = [-1,1]
# p0 = [-1.9,2.1]

p1 = tuple([-75.40680399999998, 39.860479999999995])
p2 = tuple([-75.40702699999999, 39.86017199999999])
p0 = tuple([-75.40597699999998, 39.86106199999999])
dist = nearest_line(p1, p2, p0  )
print(dist)
