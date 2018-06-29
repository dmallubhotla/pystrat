import heapq

class PriorityQueue:
	def __init__(self):
		self.elements = []
	
	def empty(self):
		return len(self.elements) == 0
	
	def put(self, item, priority):
		heapq.heappush(self.elements, (priority, item))
	
	def get(self):
		return heapq.heappop(self.elements)[1]

def heuristic(a, b):
	(x1, y1) = a
	(x2, y2) = b
	return 0#abs(x1 - x2) + abs(y1 - y2) - 1

def reconstruct_path(came_from, start, goal):
	current = goal
	path = []
	while current != start:
		path.append(current)
		try:
			current = came_from[current]
		except KeyError as e:
			return False
	path.append(start) # optional
	path.reverse() # optional
	return path

def a_star_search(grid, start, goal):
	frontier = PriorityQueue()
	frontier.put(start, 0)
	came_from = {}
	cost_so_far = {}
	came_from[start] = None
	cost_so_far[start] = 0
	
	while not frontier.empty():
		current = frontier.get()
		
		if current == goal:
			break
		
		allowed_next = [n for n in grid.get_neighbouring_points(current) if grid.is_route_allowed(n)]
		for next in allowed_next:
			new_cost = cost_so_far[current] + grid.get_route_cost(next)
			if next not in cost_so_far or new_cost < cost_so_far[next]:
				#print(grid.get_route_cost(next))
				cost_so_far[next] = new_cost
				priority = new_cost + heuristic(goal, next)
				frontier.put(next, priority)
				came_from[next] = current
	
	return reconstruct_path(came_from, start, goal), cost_so_far.get(goal, 123456)