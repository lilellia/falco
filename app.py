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

@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
	# app.run(host='127.0.0.1', port=5000)  # localhost
