import curses
import time

import game_map
import display_constants
import display_handler
import input_retrieval
import game_state
from game_parameters import FPS

class Game(object):
	def __init__(self, xm, ym):
		self.game_xm = xm
		self.game_ym = ym
		cursor = (0, 0)
		grid = game_map.get_grid(xm, ym)
		cursor = grid.player_cells[0].position
		self.game_state = game_state.GameState(cursor, grid)

	def gameLoop(self, main_scr):
		curses.start_color()
		
		curses.init_pair(display_constants.STANDARD_COLOR_PAIR_INDEX, curses.COLOR_WHITE, curses.COLOR_BLACK)
		curses.init_pair(display_constants.ENEMY_COLOR_PAIR_INDEX, curses.COLOR_RED, curses.COLOR_BLACK)
		curses.init_pair(display_constants.PLAYER_COLOR_PAIR_INDEX, curses.COLOR_GREEN, curses.COLOR_BLACK)
		curses.init_pair(display_constants.INJURED_PLAYER_COLOR_PAIR_INDEX, curses.COLOR_GREEN, curses.COLOR_YELLOW)
		curses.init_pair(display_constants.RESOURCE_COLOR_PAIR_INDEX, curses.COLOR_CYAN, curses.COLOR_BLACK)
		
		curses.curs_set(0)
		main_scr.nodelay(1)
		currtime = time.time()
		
		game_border = main_scr.subwin(self.game_ym + 2, self.game_xm + 2, 0, 0)
		game_border.box()
		game_window = main_scr.subwin(self.game_ym, self.game_xm, 1, 1)
		#self.game_window = game_window

		detail_border = main_scr.subwin(10, self.game_xm + 2, self.game_ym + 2, 0)
		detail_border.box()
		detail_window = main_scr.subwin(8, self.game_xm, self.game_ym + 3, 1)
		#self.detail_window = detail_window
		dh = display_handler.DisplayHandler(self.game_state, game_window, detail_window)

		# Game Loop
		while True:
			lastFrame = currtime
			currtime = time.time()
			
			op = input_retrieval.get_input_op()
			if op == input_retrieval.QUIT:
				break
			
			self.game_state.update(op)

			#game_window.erase()
			#detail_window.erase()
			#Display updates
			dh.display_update()
			
			main_scr.refresh()
			sleepTime = 1./FPS - (time.time() - lastFrame)
			if sleepTime > 0:
				time.sleep(sleepTime)


def startGame():
	game = Game(90, 20)
	curses.wrapper(game.gameLoop)


if __name__=="__main__":
	startGame()