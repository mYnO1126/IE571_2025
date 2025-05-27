# map.py
import numpy as np

# MAX_TIME = 100.0 # 최대 시뮬레이션 시간 (분 단위) #for testingfrom typing import List, Tuple
MAX_TIME = 2880.0  # 최대 시뮬레이션 시간 (분 단위) 
# TIME_STEP = 0.01 # 시뮬레이션 시간 간격 (분 단위)
TIME_STEP = 1.0
# MAP_WIDTH = 30  # 맵의 너비
# MAP_HEIGHT = 30  # 맵의 높이

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
    def __init__(self, filename = "map/golan_full_dataset_cropped.npz"): #, width, height):
        self.resolution_m = 10  # 한 칸당 10m
        
        # (1) 데이터 로드
        data = np.load(filename, allow_pickle=True)

        # 1) 래스터/마스크 레이어
        self.dem_arr       = data["dem"]
        self.aspect_arr    = data["aspect"]
        self.slope_arr     = data["slope"]
        self.road_mask     = data["road_mask"]
        self.lake_mask     = data["lake_mask"]
        self.stream_mask   = data["stream_mask"]
        self.wood_mask     = data["wood_mask"]
        
        # 3) 메타정보 복원
        transform_arr = data["transform"]            # (6,) 배열
        # transform     = Affine.from_gdal(*transform_arr)
        crs_str       = str(data["crs"].item())      # e.g. "EPSG:3857"
        # crs           = CRS.from_string(crs_str)

        self.height, self.width = self.dem_arr.shape

        # terrain_cost 맵 (필요에 따라 값 조정)
        # 0: 평지, 1: 험지, 2: 도로, 3: 호수, 4: 숲, 5: 개울
        self.terrain_cost = {
            0: 1.0,  # plain
            1: 1.5,  # rugged (slope 15)
            2: 3.0,  # rugged (slope 20)
            3: 5.0,  # rugged (slope 30)
            4: np.inf,  # rugged (slope 45)
            5: 0.5,  # road
            6: np.inf,  # lake
            7: 1.5,  # wood (forest)
            8: 2.0,  # stream (smaller water)
        }

        # 1) 빈 grid 생성 (height x width)
        self.grid = np.zeros((self.height, self.width), dtype=int)

        # 2) slope 기준으로 험지 마킹 (optional)
        slope_threshold = 15.0  # degree 단위 예시 값
        self.grid[self.slope_arr > slope_threshold] = 1
        # 2) slope 기준으로 험지 마킹 (optional)
        slope_threshold = 20.0  # degree 단위 예시 값
        self.grid[self.slope_arr > slope_threshold] = 2
        slope_threshold = 30.0  # degree 단위 예시 값
        self.grid[self.slope_arr > slope_threshold] = 3
        slope_threshold = 45.0  # degree 단위 예시 값
        self.grid[self.slope_arr > slope_threshold] = 4

        # 3) 도로, 호수, 숲, 개울 덮어쓰기
        #    (마스크가 True/1인 곳에 해당 코드 적용)
        self.grid[self.road_mask.astype(bool)]   = 5
        self.grid[self.lake_mask.astype(bool)]   = 6
        self.grid[self.wood_mask.astype(bool)]   = 7
        self.grid[self.stream_mask.astype(bool)] = 8
        
        # self.cost_map = self.build_cost_map()

    def get_slope(self, x, y) -> float:
        """현재 좌표(x,y)의 경사(도 단위)를 반환."""
        xi, yi = int(x), int(y)
        if 0 <= yi < self.height and 0 <= xi < self.width:
            return float(self.slope_arr[yi, xi])
        return 0.0

    def get_aspect(self, x, y) -> float:
        """
        경사 방향(방위각, degree 단위: 0°=북, 90°=동, 180°=남, 270°=서)
        """
        xi, yi = int(x), int(y)
        if 0 <= yi < self.height and 0 <= xi < self.width:
            return float(self.aspect_arr[yi, xi])
        return 0.0
    
    # def is_impassable(self, x, y) -> bool:
    #     xi, yi = int(x), int(y)
    #     if not (0 <= yi < self.height and 0 <= xi < self.width):
    #         return True
    #     # 호수는 통과 불가
    #     if self.lake_mask[yi, xi]:
    #         return True
    #     return False

    def is_road(self, x, y) -> bool:
        xi, yi = int(x), int(y)
        return (0 <= yi < self.height and 0 <= xi < self.width
                and self.road_mask[yi, xi])
    
    # def local_mask_density(self, mask, x, y, radius=1) -> float:
    #     """
    #     주어진 마스크 배열(mask: 2D boolean)에서 근방 밀도 계산
    #     """
    #     xi, yi = int(x), int(y)
    #     x0, x1 = max(0, xi-radius), min(self.width, xi+radius+1)
    #     y0, y1 = max(0, yi-radius), min(self.height, yi+radius+1)
    #     window = mask[y0:y1, x0:x1]
    #     return window.mean() if window.size else 0.0

    # def wood_density(self,x,y,radius=1)->float:
    #     i,j=int(y),int(x)
    #     y0,y1=max(0,i-radius),min(self.height,i+radius+1)
    #     x0,x1=max(0,j-radius),min(self.width,j+radius+1)
    #     window=self.wood_mask[y0:y1,x0:x1]
    #     return float(window.mean()) if window.size else 0.0
    
    def add_obstacle(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = 1  # Mark as obstacle

    def is_obstacle(self, x, y):
        return self.grid[y][x] == 1

    # def get_terrain(self, x, y):  # Get terrain type at (x, y)
    #     if 0 <= x < self.width and 0 <= y < self.height:
    #         return self.grid[x][y]
    #     return None

    # def is_road(self, x, y):
    #     xi, yi = int(x), int(y)
    #     return 0 <= xi < self.width and 0 <= yi < self.height and self.grid[xi, yi] == 2

    def movement_factor(self, x, y):
        xi, yi = int(x), int(y)
        code = (
            self.grid[yi, xi] if (0 <= xi < self.width and 0 <= yi < self.height) else 0
        )
        return self.terrain_cost.get(code, 1.0)
    
#     def build_cost_map(self, slope_weight=5.0, obstacle_cost=np.inf):
#         """
#         각 셀에 대한 이동 비용(cost map)을 생성합니다.
#         slope_weight: 경사도(°)당 추가 비용 계수
#         obstacle_cost: 통과 불가(호수 등) 셀의 비용
#         """
#         h, w = self.slope_arr.shape
#         cost_map = np.zeros((h, w), dtype=float)
#         for i in range(h):
#             for j in range(w):
#                 if self.lake_mask[i, j] or self.grid[i, j] == 1:
#                     cost_map[i, j] = obstacle_cost
#                 else:
#                     base = self.terrain_cost.get(self.grid[i, j], 1.0)
#                     slope = float(self.slope_arr[i, j])
#                     cost_map[i, j] = base + slope * slope_weight
#         return cost_map

#     def build_flow_field(self, goal_cell):
#         """
#         goal_cell: (i, j) 튜플 — 목표 지점의 그리드 좌표
#         self.flow_dir: 각 셀에서 다음으로 이동할 (di,dj) 방향 벡터를 담은 배열
#         """
#         h, w = self.cost_map.shape
#         dist = np.full((h, w), np.inf)
#         flow_dir = np.zeros((h, w, 2), dtype=int)
#         DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        
#         pq = []
#         dist[goal_cell] = 0
#         heappush(pq, (0, goal_cell))

#         while pq:
#             d,(i,j) = heappop(pq)
#             if d > dist[i,j]:
#                 continue
#             for di,dj in DIRS:
#                 ni, nj = i+di, j+dj
#                 if not (0 <= ni < h and 0 <= nj < w): 
#                     continue
#                 cost = self.cost_map[ni, nj]
#                 if cost == np.inf: 
#                     continue
#                 nd = d + cost
#                 if nd < dist[ni, nj]:
#                     dist[ni, nj] = nd
#                     # (ni,nj) 셀에서 최적 경로 따라가려면 다음에 (di,dj)만큼 이동
#                     flow_dir[ni, nj] = np.array([ di * -1, dj * -1 ], dtype=int)
#                     heappush(pq, (nd, (ni, nj)))

#         self.flow_field = flow_dir
#         self.flow_dist  = dist

# def astar(cost_map, start, goal):
#     """
#     cost_map: 2D numpy array, inf => 통과불가
#     start, goal: (i, j) tuple
#     returns: list of (i, j) 경로
#     """
#     h, w = cost_map.shape
#     DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
#     open_set = []
#     heappush(open_set, (0 + _heuristic(start, goal), 0, start, None))
#     came_from = {}
#     g_score = {start: 0}
#     while open_set:
#         f, g, current, parent = heappop(open_set)
#         if current == goal:
#             path = [current]
#             while parent:
#                 path.append(parent)
#                 parent = came_from[parent]
#             return path[::-1]
#         if current in came_from:
#             continue
#         came_from[current] = parent
#         for di, dj in DIRS:
#             ni, nj = current[0] + di, current[1] + dj
#             if not (0 <= ni < h and 0 <= nj < w):
#                 continue
#             tentative = g + cost_map[ni, nj]
#             if tentative < g_score.get((ni, nj), float('inf')):
#                 g_score[(ni, nj)] = tentative
#                 heappush(open_set, (tentative + _heuristic((ni, nj), goal), tentative, (ni, nj), current))
#     return []


# def _heuristic(a, b):
#     return math.hypot(a[0] - b[0], a[1] - b[1])