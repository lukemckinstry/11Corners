import requests
from xml.etree import ElementTree as ET

overpass_url = "http://overpass-api.de/api/interpreter"

flq2 = """
(
  node
  	["highway"]
  	["highway"!="footway"]
    ["highway"!="path"]
    ["highway"!="pedestrian"]
    ["highway"!="steps"]
    ["highway"!="elevator"]
    ["highway"!="track"]
    ["highway"!="service"]
    ["highway"!="living_street"]
    ["highway"!="unclassified"]
    ["highway"!="escape"]
    ["highway"!="raceway"]
    ["highway"!="cycleway"]
    ["highway"!="proposed"]
    ["highway"!="construction"]
    {bounds};
  way
    ["highway"]
  	["highway"!="footway"]
    ["highway"!="path"]
    ["highway"!="pedestrian"]
    ["highway"!="steps"]
    ["highway"!="elevator"]
    ["highway"!="track"]
    ["highway"!="service"]
    ["highway"!="living_street"]
    ["highway"!="unclassified"]
    ["highway"!="escape"]
    ["highway"!="raceway"]
    ["highway"!="cycleway"]
    ["highway"!="proposed"]
    ["highway"!="construction"]
    {bounds};
  rel
    ["highway"]
    ["highway"!="footway"]
    ["highway"!="path"]
    ["highway"!="pedestrian"]
    ["highway"!="steps"]
    ["highway"!="elevator"]
    ["highway"!="track"]
    ["highway"!="service"]
    ["highway"!="living_street"]
    ["highway"!="unclassified"]
    ["highway"!="escape"]
    ["highway"!="raceway"]
    ["highway"!="cycleway"]
    ["highway"!="proposed"]
    ["highway"!="construction"]
    {bounds};
);
(
    ._;
    >;
);
out;
"""


q = str(flq2.format( bounds = "(30.217541849095714,-87.09686279296874,31.395846541938496,-86.13418579101562)" ))

response = requests.get(overpass_url, 
                        params={'data': q })


print( len( response.text ))
print(  type(response.text ))


myfile = open("items2.xml", "w")  
myfile.write( response.text )  