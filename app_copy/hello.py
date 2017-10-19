from flask import Flask, url_for, redirect
from flask import render_template
from flask import request
import requests
import json
from dijkstra import search

app = Flask(__name__)

with open('static/pa_match.json') as data_file:    
	ac_network_data = json.load(data_file)

@app.route('/')
def hello_world():
    return redirect(url_for('show_nav'))

@app.route('/show_nav')
def hello(start, finish, path, center):
    return render_template('nav.html', start=start, finish=finish, path=path, center=center )

@app.route('/nav', methods=['POST', 'GET'] )
def show_search():
	if request.method == 'POST':
		result = request.form
		print( result["start_input"] )
		print( result["finish_input"] )
		start = result["start_input"].replace(" ", "+")
		dest = result["finish_input"].replace(" ", "+")
		googleapi_stub = 'https://maps.googleapis.com/maps/api/geocode/json?address='
		key = '&key=AIzaSyD-rm5ut-cafjcCgiyO0mfJ_zL8WQq4mf4'
		start_addr = requests.get(googleapi_stub + start + key)
		dest_addr = requests.get(googleapi_stub + dest + key)
		start_json = json.loads(start_addr.text)['results'][0]['geometry']['location']
		dest_json = json.loads(dest_addr.text)['results'][0]['geometry']['location']
		start_coords = tuple( [start_json['lng'], start_json['lat']])
		dest_coords = tuple( [dest_json['lng'], dest_json['lat']])
		search_result = search(start_coords, dest_coords, ac_network_data ) 
		lats, lons = [i[1] for i in search_result], [i[0] for i in search_result]
		map_center = [ sum(lats)/float(len(lats)), sum(lons)/float(len(lons)) ]
		return hello(start,dest,search_result,map_center )
	if request.method == 'GET':
		return redirect(url_for('show_nav'))

@app.route('/search')
def show_nav(name=None):
    return render_template('hello.html')
