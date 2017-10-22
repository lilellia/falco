from flask import session
import os
from PIL import Image, ImageDraw
import pytesseract
import json
from collections import deque

from graph import Node, Graph

# path to PyTesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'

# color constants
CLR_HALLWAY = 255, 0, 0, 255
CLR_PATH = 0, 255, 0, 255
CLR_CLASSROOM = 0, 0, 255, 255
CLR_STAIRS = 222, 0, 255, 255

def decolorize(filename):
	image = Image.open(os.path.join('maps', 'split_maps', filename))
	w, h = image.size

	converted = Image.new('L', (w, h))
	for x in range(w):
		for y in range(h):
			pxl = x, y
			r, g, b, a = image.getpixel(pxl)
			converted.putpixel(pxl, 255 if r == 255 else 0)

	outpath = os.path.join('maps', 'bw_maps', filename)
	converted.save(outpath)
	print(f'Decolorized: {outpath}')

def process(img_filenames, output_file, z0=0):
	"""
	Output a list of graph.Node objects, complete with positions and connections,
	but blank labels. The labels will have to be added in manually.

	The connections are defined as CLR_PATH pixels; the intersections/branches are
	defined as CLR_HALLWAY.
	"""
	def find_connections(image, x, y, z, below=None, above=None):
		connections = []
		# search for CLR_HALLWAY/CLR_CLASSROOM node above
		for y_ in range(y-1, -1, -1):
			if image.getpixel((x, y_)) in (CLR_HALLWAY, CLR_CLASSROOM, CLR_STAIRS):
				# found node
				if all(image.getpixel((x, yy)) == CLR_PATH for yy in range(y_+1, y)):
					connections.append((x, y_, z))
					break

		# search for CLR_HALLWAY/CLR_CLASSROOM node below
		for y_ in range(y+1, image.height):
			if image.getpixel((x, y_)) in (CLR_HALLWAY, CLR_CLASSROOM, CLR_STAIRS):
				# found node
				if all(image.getpixel((x, yy)) == CLR_PATH for yy in range(y+1, y_)):
					connections.append((x, y_, z))
					break

		# search for CLR_HALLWAY/CLR_CLASSROOM node left
		for x_ in range(x-1, -1, -1):
			if image.getpixel((x_, y)) in (CLR_HALLWAY, CLR_CLASSROOM, CLR_STAIRS):
				# found node
				if all(image.getpixel((xx, y)) == CLR_PATH for xx in range(x_+1, x)):
					connections.append((x_, y, z))
					break

		# search for CLR_HALLWAY/CLR_CLASSROOM node right
		for x_ in range(x+1, image.width):
			if image.getpixel((x_, y)) in (CLR_HALLWAY, CLR_CLASSROOM, CLR_STAIRS):
				# found node
				if all(image.getpixel((xx, y)) == CLR_PATH for xx in range(x+1, x_)):
					connections.append((x_, y, z))
					break

		if below:
			for x_ in range(x - 40, x + 40):
				for y_ in range(y - 40, y + 40):
					if below.getpixel((x_, y_)) == CLR_STAIRS:
						connections.append((x_, y_, z - 1))
						break
		if above:
			for x_ in range(x - 40, x + 40):
				for y_ in range(y - 40, y + 40):
					if above.getpixel((x_, y_)) == CLR_STAIRS:
						connections.append((x_, y_, z + 1))
						break

		return connections

	for z, fn in enumerate(img_filenames, z0):
		image = Image.open(fn)
		w, h = image.size
		new = Image.new('L', (w, h))
		nodes = []

		for y in range(h):
			for x in range(w):
				pxl = x, y
				color = image.getpixel(pxl)

				if color == CLR_PATH:	# CLR_PATH (path)
					new.putpixel(pxl, 0)
				elif color == CLR_HALLWAY:	# CLR_HALLWAY (hallway node)
					conn = find_connections(image, x, y, z)
					nodes.append(Node(x, y, z, '', conn))
				elif color == CLR_CLASSROOM:	# CLR_CLASSROOM (classroom node)
					conn = find_connections(image, x, y, z)
					nodes.append(Node(x, y, z, 'INSERT-LABEL-HERE', conn))
				elif color == CLR_STAIRS:
					below = Image.open(img_filenames[z-z0-1]) if z > 0 else None
					above = Image.open(img_filenames[z-z0+1]) if z+1 < len(img_filenames) else None
					conn = find_connections(image, x, y, z, below, above)
					nodes.append(Node(x, y, z, '', conn))
				else:
					new.putpixel(pxl, 255)

		with open(output_file, 'a+') as f:
			f.write('\n'.join(map(repr, nodes)) + '\n')

def generate_image_2D(img_file, path):
	img = Image.open(img_file).convert('RGB')
	draw = ImageDraw.Draw(img)

	for A, B in zip(path, path[1:]):
		draw.line((A.x, A.y, B.x, B.y), fill=(255, 0, 0), width=3)
	return img

def generate_image_3D(img_fn1, img_fn2, path1, path2):
	img1 = generate_image_2D(img_fn1, path1)
	img2 = generate_image_2D(img_fn2, path2)

	return img1, img2

def same_building(bldg, start_label, end_label, mode='label'):
	# data translation
	with open(os.path.join('maps', 'map_data', 'translation.json'), 'r') as f:
		translation = json.loads(f.read())

	# just have to deal with one building
	name = translation[bldg]['building_name']
	data = os.path.join('maps', 'map_data', translation[bldg]['map_data'])
	graph = Graph.from_file(data)
	if mode == 'label':
		start = graph.get_from_label(start_label)
		end = graph.get_from_label(end_label)
	elif mode == 'coord':
		start = graph.get_from_coordinates(*start_label)
		end = graph.get_from_coordinates(*end_label)
	else:
		raise ValueError(f'Invalid mode: {mode}.')

	if not start or not end:
		raise ValueError(f'Label(s) not found. -- {start_label}; {end_label}')

	cost, path = graph.dijkstra(start, end)
	t = session['time_']

	if start.z == end.z:
		# same floor
		bw_map = translation[bldg]['bw_maps'][str(start.z)]
		filename = os.path.join('static', f'{bw_map}_{t}.png')
		img = generate_image_2D(os.path.join('maps', 'bw_maps', bw_map), path)
		img.save(filename)
		bldg_maps = [filename]
	else:
		path1 = list(filter(lambda n: n.z == start.z, path))
		path2 = list(filter(lambda n: n.z == end.z, path))

		map1 = translation[bldg]['bw_maps'][str(start.z)]
		map2 = translation[bldg]['bw_maps'][str(end.z)]

		filename1 = os.path.join('static', f'{map1}_{t}.png')
		filename2 = os.path.join('static', f'{map2}_{t}.png')

		img1, img2 = generate_image_3D(
			os.path.join('maps', 'bw_maps', map1),
			os.path.join('maps', 'bw_maps', map2),
			path1,
			path2
		)

		img1.save(filename1)
		img2.save(filename2)
		bldg_maps = [filename1, filename2]

	kwargs = {
		'start_bldg': name,
		'start_room': start_label,
		'dest_bldg': name,
		'dest_room': end_label,
		'bldg_maps': bldg_maps,
		'gmaps': False
	}
	return kwargs

def different_buildings(bldg1, bldg2, start_label, end_label):
	# data translation
	with open(os.path.join('maps', 'map_data', 'translation.json'), 'r') as f:
		translation = json.loads(f.read())

	# starting building
	name = translation[bldg1]['building_name']
	data = os.path.join('maps', 'map_data', translation[bldg1]['map_data'])
	graph = Graph.from_file(data)
	start = graph.get_from_label(start_label)

	# find closest exit
	exits = [node for node in graph.nodes if node.label == 'EXIT']
	exit, cost, path = sorted([(e, *graph.dijkstra(start, e)) for e in exits], key=lambda tup: tup[1])[0]

	kwargs_1 = same_building(
		bldg1,
		(start.x, start.y, start.z),
		(exit.x, exit.y, exit.z),
		mode='coord'
	)

	# ending building
	dest_name = translation[bldg2]['building_name']
	data = os.path.join('maps', 'map_data', translation[bldg2]['map_data'])
	graph = Graph.from_file(data)
	end = graph.get_from_label(end_label)

	# find closest entrance/exit
	exits = [node for node in graph.nodes if node.label == 'EXIT']
	entrance, cost, path = sorted([(e, *graph.dijkstra(e, end)) for e in exits], key=lambda tup: tup[1])[0]

	kwargs_2 = same_building(
		bldg2,
		(entrance.x, entrance.y, entrance.z),
		(end.x, end.y, end.z),
		mode='coord'
	)

	bldg_maps = kwargs_1['bldg_maps']
	bldg_maps.extend(kwargs_2['bldg_maps'])
	kwargs = {
		'start_bldg': kwargs_1['start_bldg'],
		'start_room': start_label,
		'dest_bldg': kwargs_2['dest_bldg'],
		'dest_room': end_label,
		'bldg_maps': bldg_maps,
		'gmaps': True
	}
	return kwargs

if __name__ == '__main__':
	images = [
		os.path.join('maps', 'processed_maps', 'scott_lab_2.png')
	]
	process(images, os.path.join('maps', 'map_data', 'scott_lab.txt'), 1)

	# for filename in os.listdir(os.path.join('maps', 'split_maps')):
	# 	if filename not in os.listdir(os.path.join('maps', 'bw_maps')):
	# 		decolorize(filename)
