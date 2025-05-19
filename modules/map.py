# map.py


import numpy as np


# MAX_TIME = 100.0 # 최대 시뮬레이션 시간 (분 단위) #for testingfrom typing import List, Tuple
MAX_TIME = 2880.0  # 최대 시뮬레이션 시간 (분 단위) 
# TIME_STEP = 0.01 # 시뮬레이션 시간 간격 (분 단위)
TIME_STEP = 1.0
MAP_WIDTH = 30  # 맵의 너비
MAP_HEIGHT = 30  # 맵의 높이

# Blueprint: 카테고리별로 영역(사각형)과 소속태그를 매핑
# placement_zones[카테고리][키] = (x_range, y_range, affiliation)
placement_zones = {
    "TANK": {
        "blue": ((0, 10), (0, 30), "FixedDefense"),
        "red_reserve": ((20, 30), (0, 30), "Reserve"),
        # "red_E1":       ((0, 10),  (40, 50), "E1"),
        # "red_E2":       ((0, 10),  (50, 60), "E2"),
        # "red_E3":       ((0, 10),  (60, 70), "E3"),
        # "red_E4":       ((0, 10),  (70, 80), "E4"),
    },
    # "APC": {
    #     "blue":         ((12, 18), (46, 54), "FixedDefense"),
    #     "red_reserve":  ((82, 88), (46, 54), "Reserve"),
    #     "red_E1":       ((1,  9),  (41, 49), "E1"),
    #     "red_E2":       ((1,  9),  (51, 59), "E2"),
    #     "red_E3":       ((1,  9),  (61, 69), "E3"),
    #     "red_E4":       ((1,  9),  (71, 79), "E4"),
    # },
    # "INFANTRY": {
    #     "blue":         ((14, 16), (47, 53), "FixedDefense"),
    #     "red_reserve":  ((84, 86), (47, 53), "Reserve"),
    #     "red_E1":       ((2,  8),  (42, 48), "E1"),
    #     "red_E2":       ((2,  8),  (52, 58), "E2"),
    #     "red_E3":       ((2,  8),  (62, 68), "E3"),
    #     "red_E4":       ((2,  8),  (72, 78), "E4"),
    # },
    "ARTILLERY": {
        "blue": ((0, 10), (0, 30), "FixedDefense"),
        "red_reserve": ((20, 30), (0, 30), "Reserve"),
        # "red_E1":       ((3,  7),  (43, 47), "E1"),
        # "red_E2":       ((3,  7),  (53, 57), "E2"),
        # "red_E3":       ((3,  7),  (63, 67), "E3"),
        # "red_E4":       ((3,  7),  (73, 77), "E4"),
    },
    "AT_WEAPON": {
        "blue": ((0, 10), (0, 30), "FixedDefense"),
        "red_reserve": ((20, 30), (0, 30), "Reserve"),
        # "red_E1":       ((4,  6),  (44, 46), "E1"),
        # "red_E2":       ((4,  6),  (54, 56), "E2"),
        # "red_E3":       ((4,  6),  (64, 66), "E3"),
        # "red_E4":       ((4,  6),  (74, 76), "E4"),
    },
    # "SUPPLY": {
    #     "blue":         ((13, 19), (45, 55), "FixedDefense"),
    #     "red_reserve":  ((83, 89), (45, 55), "Reserve"),
    #     "red_E1":       ((5,  9),  (40, 50), "E1"),
    #     "red_E2":       ((5,  9),  (50, 60), "E2"),
    #     "red_E3":       ((5,  9),  (60, 70), "E3"),
    #     "red_E4":       ((5,  9),  (70, 80), "E4"),
    # },
}


class Velocity:  # Velocity class to store velocity information
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z


class Coord:  # Coordinate class to store x, y, z coordinates
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    def next_coord(self, velocity: Velocity):
        # Update the coordinates based on velocity and time
        self.x += velocity.x * TIME_STEP
        self.y += velocity.y * TIME_STEP
        self.z += velocity.z * TIME_STEP


class Map:  # Map class to store map information
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.zeros((width, height))

        # 0: 평지, 1: 험지, 2: 도로
        self.grid = np.zeros((width, height), dtype=int)
        self.terrain_cost = {0: 1.0, 1: 1.5, 2: 0.8}

    def add_obstacle(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[x][y] = 1  # Mark as obstacle

    def is_obstacle(self, x, y):
        return self.grid[x][y] == 1

    def get_terrain(self, x, y):  # Get terrain type at (x, y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

    def is_road(self, x, y):
        xi, yi = int(x), int(y)
        return 0 <= xi < self.width and 0 <= yi < self.height and self.grid[xi, yi] == 2

    def movement_factor(self, x, y):
        xi, yi = int(x), int(y)
        code = (
            self.grid[xi, yi] if (0 <= xi < self.width and 0 <= yi < self.height) else 0
        )
        return self.terrain_cost.get(code, 1.0)
