from math import inf as infinity, sqrt
import re

class Node:
	def __init__(self, x, y, label=None, connections=None):
		self.x, self.y = x, y
		self.label = label
		self.connections = list(connections) if connections else list()

	def __repr__(self):
		return f'Node(x={self.x}, y={self.y}, label={self.label}, connections={self.connections})'

class Graph:
	def __init__(self, nodes=None):
		self.nodes = list(nodes) if nodes else list()

	def get(self, x, y):
		for node in self.nodes:
			if node.x == x and node.y == y:
				return node
		else:
			return None

	@classmethod
	def from_file(cls, filename):
		with open(filename, 'r') as f:
			lines = [line.strip() for line in f.readlines()]

		nodes = []
		for line in lines:
			x = int(re.search('x=(\d+)', line).group(1))
			y = int(re.search('y=(\d+)', line).group(1))
			label = re.search('label=(.*?), ', line).group(1)
			conn = re.findall('\(\d+, \d+\)', line)

			connections = []
			for c in conn:
				connections.append(list(map(int, re.findall('\d+', c))))

			n = Node(x, y, label, connections)
			nodes.append(n)

		return cls(nodes)

	def dijkstra(self, start, end):
		""" algorithm implemented from https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm """

		# 1. Assign to every node a tentative distance value:
		#    Set it to zero for our initial node and infinity for all other nodes
		for node in self.nodes:
			node.cost = infinity
			node.previous = None

		start.cost = 0

		# 2. Set the initial node as current. Mark all other nodes unvisited.
		#    Create a set of all unvisited nodes called the "unvisited set".
		for node in self.nodes:
			node.visited = False

		unvisited = set(node for node in self.nodes if not node.visited)

		# 5. If the destination node has been marked visited or if the smallest
		#    distance among the unvisited set is infinity, then stop.

		# 6. Otherwise, select the unvisited node that is marked with the smallest
		#    tentative distance, set it as the current node, and go back to step 3.
		while not end.visited and min(map(lambda node: node.cost, unvisited)) < infinity:
			# 3. For the current node, consider all of its neighbors and calculate
			#    their tentative distances. Compare the newly calculated tentative
			#    distance to the current assigned value and assign the smaller one.
			#    For example, if the current node A is marked with a distance of 6,
			#    and the edge connecting it to neighbor B has length 2, then the distance
			#    to B (through A) will be 6 + 2 = 7. If B was previously marked with
			#    a distance greater than 8, then change it to 8. Otherwise, keep the
			#    current value.
			current = sorted(unvisited, key=lambda node: node.cost)[0]

			for pointer in current.connections:
				node = self.get(*pointer)
				xx = current.x - node.x
				yy = current.y - node.y
				d = sqrt(xx * xx + yy * yy)

				dist = current.cost + d
				if dist < node.cost:
					node.cost = dist
					node.previous = current

			# 4. When we are done considering all of the neighbors of the current node,
			#    mark the current node as visited and remove it form the unvisited set. A
			#    visited node will never be checked again.
			current.visited = True
			unvisited.remove(current)

		# get path
		path = []
		current = end
		while current:
			path.insert(0, current)
			current = current.previous

		return end.cost, path
