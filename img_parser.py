# http://francescopochetti.com/text-recognition-natural-scenes/
import os
from PIL import Image, ImageDraw
import pytesseract
import json
from collections import deque

from graph import Node

# path to PyTesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'

# color constants
RED = 255, 0, 0, 255
GREEN = 0, 255, 0, 255
BLUE = 0, 0, 255, 255

def decolorize():
	for filename in os.listdir(os.path.join('maps', 'split_maps')):
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

def process(image, output_path):
	"""
	Output a list of graph.Node objects, complete with positions and connections,
	but blank labels. The labels will have to be added in manually.

	The connections are defined as green pixels; the intersections/branches are
	defined as red.
	"""
	def find_connections(x, y):
		connections = []
		# search for red/blue node above
		for y_ in range(y-1, -1, -1):
			if image.getpixel((x, y_)) in (RED, BLUE):
				# found node
				if all(image.getpixel((x, yy)) == GREEN for yy in range(y_+1, y)):
					connections.append((x, y_))
					break

		# search for red/blue node below
		for y_ in range(y+1, image.height):
			if image.getpixel((x, y_)) in (RED, BLUE):
				# found node
				if all(image.getpixel((x, yy)) == GREEN for yy in range(y+1, y_)):
					connections.append((x, y_))
					break

		# search for red/blue node left
		for x_ in range(x-1, -1, -1):
			if image.getpixel((x_, y)) in (RED, BLUE):
				# found node
				if all(image.getpixel((xx, y)) == GREEN for xx in range(x_+1, x)):
					connections.append((x_, y))
					break

		# search for red/blue node right
		for x_ in range(x+1, image.width):
			if image.getpixel((x_, y)) in (RED, BLUE):
				# found node
				if all(image.getpixel((xx, y)) == GREEN for xx in range(x+1, x_)):
					connections.append((x_, y))
					break

		return connections

	w, h = image.size
	new = Image.new('L', (w, h))
	draw = ImageDraw.Draw(new)

	nodes = []

	for y in range(h):
		for x in range(w):
			pxl = x, y
			color = image.getpixel(pxl)

			if color == GREEN:	# green (path)
				new.putpixel(pxl, 0)
			elif color == RED:	# red (hallway node)
				conn = find_connections(*pxl)
				nodes.append(Node(*pxl, '', conn))
			elif color == BLUE:	# blue (classroom node)
				conn = find_connections(*pxl)
				nodes.append(Node(*pxl, 'INSERT-LABEL-HERE', conn))
			else:
				new.putpixel(pxl, 255)

	with open(output_path, 'w+') as outfile:
		outfile.write('\n'.join(map(repr, nodes)))

def generate_image_2D(img_file, path):
	img = Image.open(img_file).convert('RGB')
	draw = ImageDraw.Draw(img)

	for A, B in zip(path, path[1:]):
		draw.line((A.x, A.y, B.x, B.y), fill=(255, 0, 0), width=3)
	return img

if __name__ == '__main__':
	# decolorize()
	img = Image.open('smith_lab_2.png')
	process(img, output_path=os.path.join('maps', 'map_data', 'smith_lab_2.txt'))
 	# print(pytesseract.image_to_string(img))

# def process(path):
# 	# open image
# 	image = Image.open(path)
# 	img_width, img_height = image.size
# 	print('Img Size:', image.size)
#
# 	# convert to B/W via single-pass-algorithm
# 	converted = Image.new('L', image.size)
# 	for x in range(img_width):
# 		for y in range(img_height):
# 			pxl = x, y
# 			r, g, b, a = image.getpixel(pxl)
# 			converted.putpixel(pxl, 255 if r == 255 else 0)
# 	converted.save('converted.png')
# 	print('File `converted.png` has been saved.')
#
# 	# detect text via another single-pass-algorithm
# 	tol = 10		# tolerance
# 	text = {}
# 	upper_left = None
# 	upper_right = None
# 	history = deque()
#
# 	for y in range(2, img_height):
# 		for x in range(2, img_width):
# 			pxl = x, y
# 			color = converted.getpixel(pxl)
#
# 			# updates the history
# 			history.append(pxl)
# 			if len(history) >= tol:
# 				history.popleft()
#
# 			if upper_left is None:
# 				if color == 0:
# 					upper_left = pxl
# 					print('Upper left:', upper_left)
# 			elif upper_right is None:
# 					if all(c == 255 for c in history) or x + 1 == img_width:
# 						upper_right = pxl
# 						print('Found upper_right =', pxl)
#
# 						# both top corners found; find bottom edge
# 						subhistory = []
# 						dy = 1
# 						while len(subhistory) < tol and y + dy < img_height:
# 							pxls = [(x_, y + dy) for x_ in range(upper_left[0], x)]
# 							if any(converted.getpixel(p) == 0 for p in pxls):
# 								subhistory = []
# 							else:
# 								subhistory.append('all white row')
# 							dy += 1
#
# 						box = (*upper_left, x, y + dy)
# 						print('Box:', box)
# 						cropped = converted.crop(box)
# 						captured_text = pytesseract.image_to_string(cropped)
#
# 						if captured_text:
# 							text[box] = captured_text
# 						upper_left = upper_right = None
# 	return text
#
#
# if __name__ == '__main__':
# 	text = process(os.path.join('maps_pdf', 'prb_basement.png'))
# 	print(json.dumps(text, indent=4))
