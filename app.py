from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import logging
logging.basicConfig(level=logging.INFO)

import re
import time
import json
import datetime

from PIL import Image, ImageDraw
from graph import Node, Graph

from img_parser import generate_image_2D as genimg2D, generate_image_3D as genimg3D, same_building, different_buildings

dynamic_image = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'je-suis-secret'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
	if request.method == 'POST':
		session['start-building'] = request.form['origin-select']
		session['end-building'] = request.form['destination-select']
		session['start-room'] = request.form['origin-room'].upper()
		session['end-room'] = request.form['destination-room'].upper()
		session['time_'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H%M')
		return redirect(url_for('result'))
	else:
		logging.info('Rendering /index')
		with open('locations.json', 'r') as locfile:
			loc = json.loads(locfile.read())
		locations = [{'name': k, 'addr': v} for k, v in loc.items()]
		return render_template('index.html', locations=locations)



@app.route('/result', methods=['POST', 'GET'])
def result():
	if request.method == 'POST':
		# back button
		return redirect(url_for('index'))

	logging.info('Result!')

	# data translation
	with open(os.path.join('maps', 'map_data', 'translation.json'), 'r') as f:
		translation = json.loads(f.read())

	# get buildings (addresses)
	start_bldg = session['start-building']
	end_bldg = session['end-building']

	start_label = session['start-room']
	end_label = session['end-room']

	if start_bldg == end_bldg:
		kwargs = same_building(start_bldg, start_label, end_label)
	else:
		kwargs = different_buildings(start_bldg, end_bldg, start_label, end_label)

	return render_template('result.html', **kwargs)
	# if start_bldg == end_bldg:
	# 	# just have to deal with one building
	# 	name = translation[start_bldg]['building_name']
	# 	data = os.path.join('maps', 'map_data', translation[start_bldg]['map_data'])
	# 	graph = Graph.from_file(data)
	# 	start = graph.get_from_label(session['start-room'])
	# 	end = graph.get_from_label(session['end-room'])
	#
	# 	if not start or not end:
	# 		flash('Error. Label not found.')
	# 		return redirect(url_for('index'))
	#
	# 	cost, path = graph.dijkstra(start, end)
	# 	t = session['time_']
	#
	# 	if start.z == end.z:
	# 		# same floor
	# 		bw_map = translation[start_bldg]['bw_maps'][str(start.z)]
	# 		filename = os.path.join('static', f'{bw_map}_{t}.png')
	# 		dynamic_image = genimg2D(os.path.join('maps', 'bw_maps', bw_map), path)
	# 		dynamic_image.save(filename)
	#
	# 		imgs = [filename]
	# 	else:
	# 		imgs = []
	#
	# 		# starting floor
	# 		path1 = list(filter(lambda n: n.z == start.z, path))
	# 		path2 = list(filter(lambda n: n.z == end.z, path))
	#
	# 		map1 = translation[start_bldg]['bw_maps'][str(start.z)]
	# 		map2 = translation[start_bldg]['bw_maps'][str(end.z)]
	#
	# 		filename1 = os.path.join('static', f'{map1}_{t}.png')
	# 		filename2 = os.path.join('static', f'{map2}_{t}.png')
	#
	# 		imgs = genimg3D(
	# 			os.path.join('maps', 'bw_maps', map1),
	# 			os.path.join('maps', 'bw_maps', map2),
	# 			path1,
	# 			path2
	# 		)
	#
	# 		imgs[0].save(filename1)
	# 		imgs[1].save(filename2)
	#
	# 	kwargs = {
	# 		'start_bldg': name,
	# 		'start_room': session['start-room'],
	# 		'dest_bldg': name,
	# 		'dest_room': session['end-room'],
	# 		'bldg_maps': [filename1, filename2],
	# 		'gmaps': False
	# 	}
	# 	return render_template('result.html', **kwargs)
	# else:
	# 	img_filenames = []
	#
	# 	# different buildings
	# 	start_name = translation[start_bldg]['building_name']
	# 	start_data = os.path.join('maps', 'map_data', translation[start_bldg]['map_data'])
	# 	start_graph = Graph.from_file(start_data)
	# 	start = graph.get_from_label(session['start-room'])
	#
	# 	# find closest exit
	# 	exit_nodes = [n for n in start_graph.nodes if n.label == 'EXIT']
	#
	# 	# sorted list, according to cost: [(node, cost, path)]
	# 	exit, cost, path = sorted([(e, *graph.dijkstra(start, e)) for e in exit_nodes], key=lambda t: t[1])[0]
	#
	#
	#
	# 	z0, z1 = start.z, exit.z
	#
	# 	map1 = translation[start_bldg]['bw_maps'][str(start.z)]
	# 	map2 = translation[start_bldg]['bw_maps'][str(exit.z)]
	#
	# 	filename1 = os.path.join('static', f'{map1}_{t}.png')
	# 	filename2 = os.path.join('static', f'{map2}_{t}.png')
	#
	# 	img1, img2 = genimg3D(
	# 		os.path.join('maps', 'bw_maps', map1),
	# 		os.path.join('maps', 'bw_maps', map2),
	# 		list(filter(lambda n: n.z == start.z, path)),
	# 		list(filter(lambda n: n.z == exit.z, path))
	# 	)
	# 	img1.save(filename1)
	# 	img2.save(filename2)
	#
	# 	img_filenames = [filename1, filename2]
	#
	#
	# 	end_name = translation[end_bldg]['building_name']
	# 	end_data = os.path.join('maps', 'map_data', translation[end_bldg]['map_data'])
	# 	end_graph = Graph.from_file(end_data)
	# 	end_end = graph.get_from_label(session['end-room'])
	#
	# 	kwargs = {
	# 		'start_bldg': start_name,
	# 		'start_room': session['start-room'],
	# 		'dest_bldg': end_bldg,
	# 		'dest_room': session['end-room'],
	# 		'gmaps': True,
	# 		'bldg_maps': img_filenames
	# 	}

@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	# app.run(host='0.0.0.0', port=port)
	app.run(host='127.0.0.1', port=5000)
