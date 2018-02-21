# 11Corners
Driving directions for the safety inclined

Prototype: 
Try out the app here: https://blooming-castle-96992.herokuapp.com/ 

About:
This is a project of the Code4PA Hackathon https://www.code4pa.tech/

Pipeline:
1) Get Some Roadway Data
  A) (New and better!) Use the Open Street Map query tool http://overpass-turbo.eu/, to get a geojson file of roadways. Help exporting roads is here (https://help.openstreetmap.org/questions/30692/export-only-roads). 
  B) or download US Census Bureau .shp files of roadways, convert to geojson (https://github.com/mbostock/shapefile#shp2json)
2) Convert and Compress 
  2a) Convert geojson to network graph with geojson-to-networkgraph.py (geojson features should be 'LineString' or 'MultiLineString'), this file will be big so...
  2b) Compress the network graph with compressnetwork.py, simplify network x10!
3) Add PennDOT crash locations (or any data with geographic coordinates) to the network graph with map_matching.py
