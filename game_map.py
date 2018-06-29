import random
import math
from time import sleep

import display_constants
import state_constants
import game_parameters

Z = (0, 0)
N = (0, -1)
E = (1, 0)
S = (0, 1)
W = (-1, 0)

directions = [N, E, S, W]

#Initialize globals, sorry not really constants
DOOR_THRES = .6
ROUGH_THRES = .1
FAILED_ATTEMPTS = 100 
BIAS_STRAIGHT = False
MIN_ROOM_DIM = 3
ROOM_VAR = 5

WRITE_MAP_SETTINGS = False
ANIMATE = False and __name__=="__main__"

class ResourceCell(object):
	def __init__(self, position, cluster):
		self.position = position
		self.cluster = cluster
		self.type = "ResourceCell"
	def get_description(self):
		return "Resource Cell. Neighbouring Resource Cluster: {:0=3d}".format(self.cluster.get_total_amount())
	def get_display(self):
		return 'O', display_constants.PLAYER_COLOR_PAIR_INDEX, False
	def allows_route(self):
		return True
	def get_route_cost(self):
		return 0
	def supports_outpost(self):
		return True
	def attempt_select(self):
		return state_constants.RESOURCE_CELL_SELECTED
	

class Rock(object):
	def __init__(self, position):
		self.position = position
		self.type = "Rock"
	def get_description(self):
		return "Rock"
	def get_display(self):
		return '#', display_constants.STANDARD_COLOR_PAIR_INDEX, False
	def allows_route(self):
		return False
	def supports_outpost(self):
		return False
	def attempt_select(self):
		return False

class Resource(object):
	def __init__(self, position, amount, cluster):
		self.amount = amount
		self.cluster = cluster
		self.position = position
		self.type = "Resource"
	def get_description(self):
		return "Resource: {0:0=2d}. Cluster: {1:0=3d}".format(self.amount, self.cluster.get_total_amount())
	def get_display(self):
		return "{0:0=2d}".format(self.amount)[0], display_constants.RESOURCE_COLOR_PAIR_INDEX, False
	def allows_route(self):
		return False
	def supports_outpost(self):
		return False
	def attempt_select(self):
		return False

class ResourceCluster(object):
	def __init__(self):
		self.resources = []
	def get_total_amount(self):
		return sum([r.amount for r in self.resources])
	def get_description(self):
		return "Resource Cluster: {}".format(self.get_total_amount())
	def attempt_select(self):
		return False
	def remove_amount(self, amount_to_remove):
		if amount_to_remove > self.get_total_amount():
			return False
		amount_left_to_remove = amount_to_remove
		while amount_left_to_remove > 0:
			if amount_left_to_remove > 10:
				step = 10
			else:
				step = amount_left_to_remove
			amount_left_to_remove -= 10
			amount_left_in_step = step
			while amount_left_in_step > 0:
				highest_resource = max(self.resources, key = lambda p: p.amount)
				amount_removing_from_highest_resource = min(amount_left_in_step, highest_resource.amount)
				highest_resource.amount -= amount_removing_from_highest_resource
				amount_left_in_step -= amount_removing_from_highest_resource
		return True
		

class RouteAttemptTile(object):
	def __init__(self, position):
		self.position = position
		self.type = "RouteAttemptTile"
	def get_description(self):
		return ""
	def get_display(self):
		return '.', display_constants.STANDARD_COLOR_PAIR_INDEX, False
	def allows_route(self):
		return True
	def attempt_select(self):
		return False

class RouteAttempt(object):
	def __init__(self, attempt_tiles):
		self.attempt_tiles = attempt_tiles
		
class Outpost(object):
	def __init__(self, position):
		self.position = position
		self.type = "Outpost"
		self.max_health = game_parameters.OUTPOST_MAX_HEALTH
		self.health = self.max_health
		self.energy = 0
		self.can_remove = False
		self.withering = False
		self.wither_energy = 0
		self.supporting_neighbour_count = 0
	def get_description(self):
		if self.withering:
			title = "Withering Outpost"
		else:
			title = "Outpost"
		return "{} {:2}/{:2} | Support {} | Energy {}".format(title, self.health, self.max_health, self.supporting_neighbour_count, self.energy)
	def get_display(self):
		display_colour = display_constants.PLAYER_COLOR_PAIR_INDEX
		is_injured = self.health < game_parameters.OUTPOST_MAX_HEALTH
		if self.health < game_parameters.OUTPOST_MAX_HEALTH // 2:
			return '.', display_colour, is_injured
		return ':', display_colour, is_injured
	def allows_route(self):
		return True
	def supports_outpost(self):
		return True
	def get_route_cost(self):
		return 0
	def attempt_select(self):
		return False
	def update_self(self, neighbour_count):
		self.energy += 1
		self.supporting_neighbour_count = neighbour_count
		if (not self.withering) and (self.supporting_neighbour_count < game_parameters.OUTPOST_REQUIRED_SUPPORT):
			self.withering = True
		elif self.withering and (self.supporting_neighbour_count >= game_parameters.OUTPOST_REQUIRED_SUPPORT):
			self.withering = False
			self.wither_energy = 0
		if self.withering:
			self.wither_energy += 1
			if self.wither_energy >= game_parameters.OUTPOST_WITHER_ENERGY_COST:
				self.wither_energy -= game_parameters.OUTPOST_WITHER_ENERGY_COST
				self.health -= 1
		if self.health < 1:
			self.can_remove = True
			self.energy = 0

class Grid(object):
	def __init__(self, xm, ym):
		self.xm = xm
		self.ym = ym
		
		self.map = {}
		for y in range(ym + 1):
			for x in range(xm + 1):
				self.map[(x, y)] = None
		self.resource_clusters = []
		self.player_cells = []
		self.outposts = []

	def in_grid(self, pt):
		x,y = pt
		return not any([x >= self.xm, x < 0, y >= self.ym, y < 0])
	def get_tile(self, pt):
		return self.map[pt]
	def get_tile_description(self, pt):
		tile = self.get_tile(pt)
		if tile is None:
			return "Empty"
		else:
			return tile.get_description()
	def add_tile(self, item, pt):
		if self.map[pt] is None:
			self.map[pt] = (item)
		else:
			raise ValueError("Point {0} already has tile".format(pt))
	def remove_tile(self, item):
		pt = item.position
		self.map[pt] = None
	def get_tile_display(self, pt):
		tile = self.get_tile(pt)
		if tile is None:
			return ' ', 0, False
		else:
			return tile.get_display()
	def is_route_allowed(self, pt):
		tl = self.get_tile(pt)
		if tl:
			tile_allowed = tl.allows_route()
		else:
			tile_allowed = True
		return self.in_grid(pt) and tile_allowed
	def get_route_cost(self, pt):
		tl = self.get_tile(pt)
		if tl:
			return tl.get_route_cost()
		else:
			return 1
	def get_neighbouring_points(self, pt):
		return [av(pt, dr) for dr in directions if self.in_grid(av(pt, dr))]
	def get_neighbouring_objects(self, p1):
		return [self.get_tile(p2) for p2 in self.get_neighbouring_points(p1) if self.get_tile(p2)]



def set_constants():
	DOOR_THRES = random.random()*.9 + .1
	ROUGH_THRES = random.random() * .3
	FAILED_ATTEMPTS = random.randint(0, 200)
	BIAS_STRAIGHT = random.randint(0, 1)
	MIN_ROOM_DIM = random.randint(3, 4)
	ROOM_VAR = random.randint(3, 5)
	
	#DOOR_THRES = 0.32234678069988054
	#ROUGH_THRES = 0.14971437014511607
	#FAILED_ATTEMPTS = 32
	#BIAS_STRAIGHT = 1
	#MIN_ROOM_DIM = 1
	#ROOM_VAR = 0
	
	if WRITE_MAP_SETTINGS:
		with open("lastmapsettings.txt", "w+") as f:
			f.write("\n".join([
			
				"Door threshold: " + str(DOOR_THRES),
				"Roughness threshold: " + str(ROUGH_THRES),
				"Allowed failed room attempts: " + str(FAILED_ATTEMPTS),
				"Staight line bias? " + str(BIAS_STRAIGHT),
				"Min room dim: " + str(MIN_ROOM_DIM),
				"Room variation: " + str(ROOM_VAR),			
			]))
			
	if __name__ == "__main__":
		print("\n".join([
			
				"Door threshold: " + str(DOOR_THRES),
				"Roughness threshold: " + str(ROUGH_THRES),
				"Allowed failed room attempts: " + str(FAILED_ATTEMPTS),
				"Staight line bias? " + str(BIAS_STRAIGHT),
				"Min room dim: " + str(MIN_ROOM_DIM),
				"Room variation: " + str(ROOM_VAR),
			]))
			
	return DOOR_THRES,ROUGH_THRES,FAILED_ATTEMPTS,BIAS_STRAIGHT,MIN_ROOM_DIM,ROOM_VAR



def delay_func(tm = .1):
	sleep(tm)
	print()
	#input()
	
def gap_func():
	input()
	
def av(a, b):
	return (a[0] + b[0], a[1] + b[1])
	
class Room(object):
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.merged = False
		self.neighbours = set([av(pt, dir) for pt in self.points for dir in directions if av(pt, dir) not in self.points])
	@property
	def nw(self):
		return (self.x, self.y)
		
	@property
	def se(self):
		return (self.x + self.width, self.y + self.height)
		
	@property
	def points(self):
		return [(x,y) for x in range(self.x, self.x + self.width) for y in range(self.y, self.y + self.height)]
	def get_non_boundary_points(self):
		return [(x,y) for x in range(self.x + 1, self.x + self.width - 1) for y in range(self.y + 1, self.y + self.height - 1)]
		
		
class Maze(object):
	def __init__(self, points):
		self.points = points
		self.merged = False
		self.neighbours = set([av(pt, dir) for pt in points for dir in directions if av(pt, dir) not in points])

class Map(object):
	def __init__(self, width, height):
		self.height = height
		self.width = width
		self.ym = 2 * self.height + 1
		self.xm = 2 * self.width + 1
		
		self.grid = []
		for i in range(self.ym):
			self.grid.append(["#" for _ in range(self.xm)])
		
	def __str__(self):
		return "\n".join("".join(i) for i in self.grid)
		
	def __contains__(self, point):
		x,y = point
		return (y >= 0 and y < self.ym and x >= 0 and x < self.xm)
		
	def spot_empty(self, point):
		x,y = point
		return self.grid[y][x] == " "
		
	def get(self, point):
		x,y = point
		return self.grid[y][x]
		
	def clear(self, point):
		x,y = point
		self.grid[y][x] = " "
		
	def fill(self, point):
		x,y = point
		self.grid[y][x] = "X"
		
	def add_room(self, room):
		
		
		if room.nw not in self or room.se not in self:
			return False
			
		if any(
			[self.spot_empty((x,y)) for x in range(room.x, room.x + room.width) for y in range(room.y, room.y + room.height)]
		):
			return False
		
		for x in range(room.x, room.x + room.width):
			for y in range(room.y, room.y + room.height):
				self.clear((x,y))
		if ANIMATE:
				print(self)
				delay_func()
		return True
		
	def pt_has_avail_path(self, point):
		for direction in directions:
			one = av(point, direction)
			two = av(one, direction)
			if one in self and two in self and not (self.spot_empty(one) or self.spot_empty(two)):
				return True
		else:
			return False
		
		
	def get_align_points(self):
		return [(2 * x + 1, 2 * y + 1) for x in range(self.width) for y in range(self.height)]
	def get_off_points(self):
		return [(2 * x, 2 * y) for x in range(self.width) for y in range(self.height)]

def makeMaze(mp):
	options = [p for p in mp.get_align_points() if (not mp.spot_empty(p)) and mp.pt_has_avail_path(p) ]
	
	if not options:
		return False
	
	start = random.choice(options)
	
	active = set([start])
	clear_points = set([start])
	mazepoints = set()
	
	lastDirection = None
	
	while len(active):
		curr = active.pop()
		valid = []
		valid = []
		for direction in directions:
			one = av(curr, direction)
			two = av(one, direction)
			if one in mp and two in mp and not(mp.spot_empty(one) or mp.spot_empty(two)):
				valid.append(direction)
			
		if len(valid):
			
			if lastDirection and lastDirection in valid and BIAS_STRAIGHT:# and random.random() < .9:
				chosen = lastDirection
			else:
				chosen = random.choice(valid)
			lastDirection = chosen
			one = av(curr, chosen)
			two = av(one, chosen)
			clear_points.update([one, two])
			active.add(two)
			
		for point in clear_points:
			mp.clear(point)
			mazepoints.add(point)
			if ANIMATE:
				print(mp)
				delay_func(.15)
		clear_points.clear()
	return Maze(mazepoints)
	#for pt in options:
	#	x,y = pt
	#	mp.grid[y][x] = "h"


		
def getMap(wdth, ht):
	DOOR_THRES,ROUGH_THRES,FAILED_ATTEMPTS,BIAS_STRAIGHT,MIN_ROOM_DIM,ROOM_VAR = set_constants()



	m = Map(wdth, ht)
	if ANIMATE:
		print(m)
		print("\nClearing...")
	failed_attempts = FAILED_ATTEMPTS
	rooms = []
	mazes = []
	while failed_attempts > 0:
		rx = 2 * random.randint(1, m.width) - 1
		ry = 2 * random.randint(1, m.height) - 1
		width = 2 * random.randint(MIN_ROOM_DIM, MIN_ROOM_DIM + ROOM_VAR) - 1
		height = 2 * random.randint(MIN_ROOM_DIM, MIN_ROOM_DIM + ROOM_VAR) - 1
		rm = Room(rx, ry, width, height)
		if m.add_room(rm):
			rooms.append(rm)
		else:
			failed_attempts -= 1
	more = True
	while more:
		#print("Making maze...")
		more = makeMaze(m)
		mt = str(more)
		#print("More was " + mt)
		#if more:
			#print(len(more.points))
			#print(more.points)
		if more:
			mazes.append(more)
	zones = rooms + mazes
	m.rooms = rooms
	if ANIMATE:
		print("\nCleared.\n")
		print(m)
		print("\n")
	#for point in mazes[0].points:
	#	x,y = point
	#	m.grid[y][x] = "o"
	#for point in mazes[0].neighbours:
	#	x,y = point
	#	m.grid[y][x] = "."
	#for point in rooms[0].points:
	#	x,y = point
	#	m.grid[y][x] = "o"
	potential_doors = dict()
	for point in m.get_off_points():
		x,y = point
		nzs = set([zn for zn in zones for dr in directions if point in zn.neighbours])
		if not m.spot_empty(point) and len(nzs) == 2:
			potential_doors[point] = nzs
			#m.grid[y][x] = "&" #str(len(nzs))[-1]
	start = zones[0]
	working = set([start])
	while len(working):
		curr = working.pop()
		curr.merged = True
		if ANIMATE:
			for pt in curr.points:
				px,py = pt
				m.grid[py][px] = "."
		for pt in curr.neighbours:
			if pt in potential_doors:
				oz = [z for z in potential_doors[pt] if z != curr][0]
				if not oz.merged and not(oz in working and random.random() < DOOR_THRES):
					working.add(oz)
					px,py = pt
					m.grid[py][px] = "_"
					if ANIMATE:
						print(m)
						delay_func()
					
	if ANIMATE:
		gap_func()
	open_points = set()
	for y,row in enumerate(m.grid):
		for x in range(len(row)):
			if row[x] != "#":
				open_points.add((x,y))
				row[x] = " "
	if ANIMATE:
		print()
		print(m)
		gap_func()
	dead_ends = set()
	
	
	for point in open_points:
		ns = [av(point, dir) for dir in directions if not m.spot_empty(av(point,dir))]
		if len(ns) == 3:
			x,y=point
			m.grid[y][x] = "#"
			dead_ends.add((x,y))
			
	
	while len(dead_ends):
		for de in dead_ends:
			open_points.discard(de)
		dead_ends = set()
		for point in open_points:
			ns = [av(point, dir) for dir in directions if not m.spot_empty(av(point,dir))]
			if len(ns) >= 3:
				x,y=point
				m.grid[y][x] = "#"
				dead_ends.add((x,y))
				if ANIMATE:
					print(m)
					delay_func()
	if ANIMATE:
		gap_func()
	for point in open_points:
		for dir in directions:
			if not m.spot_empty(av(point, dir)):
				if random.random() < ROUGH_THRES:
					m.clear(av(point,dir))
					if ANIMATE:
						print(m)
						delay_func()
			
	#SET RESOURCES
	clusters = []
	for rm in rooms:
		available_points = rm.get_non_boundary_points()
		if len(available_points) < 4:
			continue
		else:
			cluster = []
			cluster_size = random.randint(4, min(8, len(available_points)))
			cluster_points = []
			cluster_points.append(random.choice(available_points))
			
			while len(cluster_points) < cluster_size:
				neighbours = set([av(pt, dir) for pt in cluster_points for dir in directions if av(pt, dir) not in cluster_points and av(pt, dir) in available_points])
				cluster_points.append(random.choice(list(neighbours)))
	
			for pt in cluster_points:
				x,y = pt
				cluster.append((pt, random.randint(20, 99)))
			clusters.append(cluster)
	m.clusters = clusters
	
	#PICK PLAYER STARTING LOCATION
	starting_cluster = random.choice(m.clusters)
	starting_cluster_points = [r[0] for r in starting_cluster]
	neighbours = set([av(pt, dir) for pt in starting_cluster_points for dir in directions if av(pt, dir) not in starting_cluster_points])
	m.start_location = random.choice(list(neighbours))
	if ANIMATE:
		print()
		print(m)
	return m

def get_grid(xm, ym):
	grid = Grid(xm , ym)
	
	mp = getMap(xm // 2, ym // 2)
	for y in range(len(mp.grid)):
		for x in range(len(mp.grid[y])):
			if mp.grid[y][x] == "#":
				grid.add_tile(Rock((x,y)), (x,y))
	
	for cluster in mp.clusters:
		rc = ResourceCluster()
		for rec in cluster:
			pt, amount = rec
			x,y = pt
			resource = Resource(pt, amount, rc)
			rc.resources.append(resource)
			grid.add_tile(resource, (x,y))
		grid.resource_clusters.append(rc)

	start_neighbours = grid.get_neighbouring_objects(mp.start_location)
	start_resource = next(t for t in start_neighbours if t.type == "Resource")
	starting_cell = ResourceCell(mp.start_location, start_resource.cluster)
	grid.player_cells.append(starting_cell)
	grid.add_tile(starting_cell, mp.start_location)
	#TODO remove
	grid.start_location = mp.start_location
	return grid

if __name__=="__main__":
	#m = getMap(40, 20)
	#print(m)
	p1 = (0, 0)
	p2 = (0, 1)
	p3 = (0, 2)
	rc = ResourceCluster()
	r1 = Resource(p1, 50, rc)
	r2 = Resource(p2, 35, rc)
	r3 = Resource(p3, 6, rc)
	rc.resources = [r1, r2, r3]
	print(rc.get_total_amount())
	print([r.amount for r in rc.resources])
	print(rc.remove_amount(10))
	print(rc.get_total_amount())
	print([r.amount for r in rc.resources])
	print(rc.remove_amount(20))
	print(rc.get_total_amount())
	print([r.amount for r in rc.resources])
	print(rc.remove_amount(50))
	print(rc.get_total_amount())
	print([r.amount for r in rc.resources])
	print(rc.remove_amount(8))
	print(rc.get_total_amount())
	print([r.amount for r in rc.resources])
	print(rc.remove_amount(6))
	print(rc.get_total_amount())
	print([r.amount for r in rc.resources])