# 11Corners
Driving directions for the safety inclined

Pipeline:
1) Download US Census Bureau .shp files of roadways, convert to geojson (https://github.com/mbostock/shapefile#shp2json)
2) Convert geojson to network graph with geojson-to-networkgraph.py (geojson features should be 'LineString' or 'MultiLineString'), pop this in app backend or...
3) Add processed PennDOT crash data (or other processed data with geographic coordinates) to network graph using map matching script, map_matching.py
