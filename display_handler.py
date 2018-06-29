import curses
import state_constants

WRITE_DEBUG = True

#A_TOP, A_VERTICAL have no effect
INJURED_ATTR = curses.A_LEFT | curses.A_UNDERLINE

class DisplayHandler(object):
	def __init__(self, game_state, game_window, detail_window):
		self.game_state = game_state
		self.game_window = game_window
		self.detail_window = detail_window

	def display_update(self):
		#update bottom to top
		
		#Draw terrain first
		for pt in self.game_state.game_map.map.keys():
			x,y = pt
			try:
				displaych, color_pair_index, apply_injured = self.game_state.game_map.get_tile_display(pt)
				self.game_window.addch(y, x, displaych, curses.color_pair(color_pair_index))
			except curses.error:
				pass

		#Route attempts must go above ground
		for ra in self.game_state.route_attempts:
			
			for rat in ra.attempt_tiles:
				displaych, color_pair_index, apply_injured = rat.get_display()
				x,y = rat.position
				try:
					self.game_window.addch(y, x, displaych, curses.color_pair(color_pair_index))
				except curses.error:
					pass
		
		#Draw cells a second time to fix z order, this is annoying.
		for cell in self.game_state.game_map.player_cells:
			x,y = cell.position
			try:
				displaych, color_pair_index, apply_injured = cell.get_display()
				if displaych:
					self.game_window.addch(y, x, displaych, curses.color_pair(color_pair_index))
			except curses.error:
				pass
				
		for cell in self.game_state.game_map.outposts:
			x,y = cell.position
			try:
				displaych, color_pair_index, apply_injured = cell.get_display()
				if displaych:
					self.game_window.addch(y, x, displaych, curses.color_pair(color_pair_index))
					if apply_injured:
						self.add_attr(cell.position, INJURED_ATTR)
			except curses.error:
				pass
		#End by setting cursor
		
		self.write_tile_desc(self.game_state.game_map.get_tile_description(self.game_state.cursor))
		self.write_action_desc(self.game_state.action_desc)
		self.write_helptext(state_constants.STATE_HELPTEXT_DICT.get(self.game_state.state_type, ""))
		self.write_helptext2(state_constants.STATE_HELPTEXT2_DICT.get(self.game_state.state_type, ""))
		self.write_money(state_constants.MONEY_DISPLAY_TEXT.format(self.game_state.money))
		self.write_debug("LastOp: [{0}] | CurrState: [{1}]".format(self.game_state.last_op, self.game_state.state_type))
		#if self.game_state.game_map.get_tile(self.game_state.cursor):
		#	self.write_debug("Current tile type is " + str(type(self.game_state.game_map.get_tile(self.game_state.cursor))))
		#else:
		#	self.write_debug("")
		
		
		cursx,cursy = self.game_state.cursor
		cursor_char = self.game_window.inch(cursy, cursx)
		cursor_attrs = cursor_char & curses.A_ATTRIBUTES
		self.game_window.chgat(cursy, cursx, 1, curses.A_BLINK | cursor_attrs)

		self.game_window.refresh()
		self.detail_window.refresh()
	def write_detail_window_line(self, lineno, str):
		self.detail_window.move(lineno, 0)
		self.detail_window.clrtoeol()
		self.detail_window.addstr(lineno, 0, str)
	def write_tile_desc(self, str):
		self.write_detail_window_line(0, str)
	def write_action_desc(self, str):
		self.write_detail_window_line(1, str)
	def write_helptext(self, str):
		self.write_detail_window_line(2, str)
	def write_helptext2(self, str):
		self.write_detail_window_line(3, str)
	def write_money(self, str):
		self.write_detail_window_line(6, str)
	def write_debug(self, str):
		if WRITE_DEBUG:
			self.write_detail_window_line(7, str)
	def add_attr(self, pos, attr):
		x,y = pos
		curr_chr = self.game_window.inch(y,x)
		curr_attrs = curr_chr & curses.A_ATTRIBUTES
		self.game_window.chgat(y, x, 1, attr | curr_attrs)
