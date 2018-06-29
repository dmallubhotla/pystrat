import pathfinding
import input_retrieval
import game_map
from state_constants import *
from game_parameters import *

def mve(p1, p2):
	x1,y1 = p1
	x2,y2 = p2
	return (x1 + x2, y1 + y2)


class GameState(object):
	def __init__(self, init_cursor, game_map):
		self.cursor = init_cursor
		self.game_map = game_map
		self.state_type = STANDARD
		self.last_op = None
		self.action_desc = ""
		
		self.money = 1000
		
		#STANDARD_CONSTRUCTION_AVAILABLE
		self.neighbouring_resource = None

		#ANY SELECTED
		self.selected = None
		#RESOURCE_CELL_SELECTED_ROUTE_CREATION fields
		self.route_attempts = []
	def updateCursor(self, dr):
		old = self.cursor
		result = mve(self.cursor, dr)
		if self.game_map.in_grid(result):
			self.cursor = result
		return old, self.cursor
	def _game_tick(self):
		self._process_incomes()
	def _process_incomes(self):
		for outpost in self.game_map.outposts[:]:
			outpost.update_self(len([obj for obj in self.game_map.get_neighbouring_objects(outpost.position) if obj.supports_outpost()]))
			if outpost.energy >= OUTPOST_MONEY_GAIN_ENERGY_COST:
				outpost.energy -= OUTPOST_MONEY_GAIN_ENERGY_COST
				self.money += OUTPOST_MONEY_GAIN_AMOUNT
			if outpost.can_remove:
				self.game_map.outposts.remove(outpost)
				self.game_map.remove_tile(outpost)
	def update(self, op):
		if op != input_retrieval.NOP:
			self.last_op = op
		
		if self.state_type in CURSOR_MOVE_STATES:
			if op in input_retrieval.CARDDRS:
			#Actual updates
				self.updateCursor(op)

		#DISPATCHING STATE_SPECIFIC UPDATE LOGIC
		dispatch_dict = {
			STANDARD: _update_standard,
			STANDARD_CONSTRUCTION_AVAILABLE: _update_standard_construction_available,
			RESOURCE_CELL_SELECTED: _update_resource_cell_selected,
			RESOURCE_CELL_SELECTED_ROUTE_CREATION: _update_resource_cell_selected_route_creation,
			RESOURCE_CELL_SELECTED_OUTPOST_CREATION: _update_resource_cell_selected_outpost_creation,
		}
		dispatch_dict.get(self.state_type)(self, op)
		
		if self.state_type in GAME_TICK_STATES:
			self._game_tick()


## HERE FOLLOWS GARBAGE PRIVATE METHODS FOR EACH STATE
def _update_standard(self, op):
	if op == input_retrieval.SELECT:
		cursor_tile = self.game_map.get_tile(self.cursor)
		if cursor_tile:
			attempt_select_result = self.game_map.get_tile(self.cursor).attempt_select()
			if attempt_select_result:
				self.selected = self.game_map.get_tile(self.cursor)
				self.state_type = attempt_select_result
				return
	elif op in input_retrieval.CARDDRS:
		if any([obj.type == "Resource" for obj in self.game_map.get_neighbouring_objects(self.cursor)]
				) and not self.game_map.get_tile(self.cursor):
			self.neighbouring_resource = next(t for t in self.game_map.get_neighbouring_objects(self.cursor) if t.type == "Resource")
			self.state_type = STANDARD_CONSTRUCTION_AVAILABLE
def _update_standard_construction_available(self, op):
	_update_standard(self, op)
	
	if op == input_retrieval.OPTION_1:
		if self.neighbouring_resource.cluster.remove_amount(RESOURCE_CELL_RESOURCE_COST):
			new_rc = game_map.ResourceCell(self.cursor, self.neighbouring_resource.cluster)
			self.game_map.player_cells.append(new_rc)
			self.game_map.add_tile(new_rc, self.cursor)
	elif op in input_retrieval.CARDDRS:
		if all([obj.type != "Resource" for obj in self.game_map.get_neighbouring_objects(self.cursor)]
				) or self.game_map.get_tile(self.cursor):
			self.neighbouring_resource = None
			self.state_type = STANDARD

def _update_resource_cell_selected(self, op):
	if op == input_retrieval.CANCEL:
		self.selected = None
		self.state_type = STANDARD
	if op == input_retrieval.OPTION_1:
		self.state_type = RESOURCE_CELL_SELECTED_ROUTE_CREATION
	elif op == input_retrieval.OPTION_2:
		self.state_type = RESOURCE_CELL_SELECTED_OUTPOST_CREATION
def _update_resource_cell_selected_route_creation(self, op):
	if op == input_retrieval.CANCEL:
		self.route_attempts.clear()
		self.selected = None
		self.action_desc = ""
		self.state_type = STANDARD
	#with resource cell selected, still only recalculate on cursor update
	if op in input_retrieval.CARDDRS:
		#Always clear attempts?
		self.route_attempts.clear()
		self.action_desc = ""
		
		attempted_path_from_start, pathfinding_cost = pathfinding.a_star_search(self.game_map, self.selected.position, self.cursor)
		if attempted_path_from_start:
			path_from_start_tiles = []
			for pt in attempted_path_from_start:
				if not self.game_map.get_tile(pt):
					path_from_start_tiles.append(game_map.RouteAttemptTile(pt))
			attempted_start_route = game_map.RouteAttempt(path_from_start_tiles)
			self.route_attempts.append(attempted_start_route)
			self.action_desc = "About to create {0:0} route tiles, with cost {1:0} out of available {2:0}. PF Cost {3:0}".format(len(path_from_start_tiles), OUTPOST_CREATION_RESOURCE_COST * len(path_from_start_tiles), self.selected.cluster.get_total_amount(), pathfinding_cost)
			#print(attempted_path_from_start)
	if op == input_retrieval.SELECT:
		#Attempt route creation
		if len(self.route_attempts):
			ra = self.route_attempts[0]
			route_creation_cost = len(ra.attempt_tiles) * OUTPOST_CREATION_RESOURCE_COST
			if self.selected.cluster.remove_amount(route_creation_cost):
				for tile in ra.attempt_tiles:
					outpost = game_map.Outpost(tile.position)
					self.game_map.outposts.append(outpost)
					self.game_map.add_tile(outpost, outpost.position)
			self.route_attempts.clear()
			self.selected = None
			self.action_desc = ""
			self.state_type = STANDARD
			
def _update_resource_cell_selected_outpost_creation(self, op):
	if op == input_retrieval.CANCEL:
		self.route_attempts.clear()
		self.selected = None
		self.action_desc = ""
		self.state_type = STANDARD
	#with resource cell selected, still only recalculate on cursor update
	if op in input_retrieval.CARDDRS:
		#Always clear attempts?
		self.route_attempts.clear()
		self.action_desc = ""
		
		if not self.game_map.get_tile(self.cursor):
			
			attempt_tile = game_map.RouteAttemptTile(self.cursor)
			ra = game_map.RouteAttempt([attempt_tile])
			self.route_attempts.append(ra)
			
			self.action_desc = "Will create outpost, with cost {} out of available {}.".format(
			OUTPOST_CREATION_RESOURCE_COST , self.selected.cluster.get_total_amount())
			#print(attempted_path_from_start)
	if op == input_retrieval.SELECT:
		#Attempt route creation
		if len(self.route_attempts):
			ra = self.route_attempts[0]
			route_creation_cost = len(ra.attempt_tiles) * OUTPOST_CREATION_RESOURCE_COST
			if self.selected.cluster.remove_amount(route_creation_cost):
				for tile in ra.attempt_tiles:
					outpost = game_map.Outpost(tile.position)
					self.game_map.outposts.append(outpost)
					self.game_map.add_tile(outpost, outpost.position)
			self.route_attempts.clear()
			#self.selected = None
			#self.action_desc = ""
			#self.state_type = STANDARD


