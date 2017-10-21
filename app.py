from flask import Flask, render_template, request, redirect, url_for # , session
import os
import logging
logging.basicConfig(level=logging.INFO)

import re
import time

from PIL import Image, ImageDraw
from graph import Node, Graph

from img_parser import generate_image_2D as genimg2D, process

dynamic_image = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'je-suis-secret'

@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
	logging.info('Rendering /index')
	locations = ['hello', 'world']
	return render_template('index.html', locations=locations)



@app.route('/result')
def result():
	logging.info('Result!')
	graph = Graph.from_file(os.path.join('maps', 'map_data', 'smith_lab_2.txt'))
	start = graph.get(778, 411)	# 94
	end = graph.get(245, 373) # 138

	cost, path = graph.dijkstra(start, end)
	dynamic_image = genimg2D(os.path.join('maps', 'bw_maps', 'smith_lab_2.png'), path)
	dynamic_image.save(os.path.join('static', 'smith_lab_2.png'))
	return render_template('result.html', dynamic_image=url_for('static', filename='smith_lab_2.png'))

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='127.0.0.1', port=port, debug=True)
	process(Image.open('smith_lab_2.png'), os.path.join('maps', 'map_data', 'smith_lab_2.txt'))

	graph = Graph.from_file(os.path.join('maps', 'map_data', 'smith_lab_2.txt'))
	start = graph.get(778, 411)	# 94
	end = graph.get(245, 373) # 138

	cost, path = graph.dijkstra(start, end)
	dynamic_image = genimg2D(os.path.join('maps', 'bw_maps', 'smith_lab_2.png'), path)
	# dynamic_image.show()
