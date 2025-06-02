# map.py

import numpy as np

import math
from heapq import heappush, heappop
from typing import List, Tuple, Optional
from .unit_definitions import UnitType #, UnitStatus, UnitType, UnitComposition, HitState, UNIT_SPECS, BLUE_HIT_PROB_BUFF, get_landing_data, AMMUNITION_DATABASE, AmmunitionInfo, SUPPLY_DATABASE


# MAX_TIME = 100.0 # 최대 시뮬레이션 시간 (분 단위) #for testingfrom typing import List, Tuple
MAX_TIME = 500 # 2880.0 # 500.0  # 최대 시뮬레이션 시간 (분 단위) 
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
        # self.x += velocity.x * TIME_STEP
        # self.y += velocity.y * TIME_STEP
        # self.z += velocity.z * TIME_STEP

        self.x += velocity.x
        self.y += velocity.y
        self.z += velocity.z

class Map:  # Map class to store map information
    def __init__(self, filename = "map/golan_full_dataset_cropped.npz"): #, width, height):
        self.resolution_m = 10
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
        self.reference_altitude = self.dem_arr[-1][0] # min([min(s) for s in self.dem_arr])
        
        # terrain_cost 맵 (필요에 따라 값 조정)
        # 0: 평지, 1: 험지, 2: 도로, 3: 호수, 4: 숲, 5: 개울
        self.terrain_cost = {
            0: 1.0,  # plain
            1: 2.0,  # rugged (slope 10)
            2: 3.0,  # rugged (slope 15)
            3: np.inf,  # rugged (slope 20)
            4: np.inf,  # rugged (slope 30)
            5: 0.8,  # road
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
        slope_threshold = 25.0  # degree 단위 예시 값
        self.grid[self.slope_arr > slope_threshold] = 3
        slope_threshold = 30.0  # degree 단위 예시 값
        self.grid[self.slope_arr > slope_threshold] = 4

        # 3) 도로, 호수, 숲, 개울 덮어쓰기
        #    (마스크가 True/1인 곳에 해당 코드 적용)
        self.grid[self.road_mask.astype(bool)]   = 5
        self.grid[self.lake_mask.astype(bool)]   = 6
        self.grid[self.wood_mask.astype(bool)]   = 7
        self.grid[self.stream_mask.astype(bool)] = 8
        
        #!TEMP 비용 맵과 플로우 필드 생성 >>>>
        self.cost_map = self.build_cost_map()
        self.flow_fields = {}  # 목표별 플로우 필드 캐시
        #!TEMP 비용 맵과 플로우 필드 생성 <<<<

    #!TEMP >>>>
    def build_cost_map(self, slope_weight=0.1, min_cost=0.1):
        """각 셀의 이동 비용 계산"""
        h, w = self.slope_arr.shape
        cost_map = np.zeros((h, w), dtype=float)
        
        for i in range(h):
            for j in range(w):
                terrain_type = self.grid[i, j]
                base_cost = self.terrain_cost.get(terrain_type, 1.0)
                
                if base_cost == np.inf:
                    cost_map[i, j] = np.inf
                else:
                    # 경사도 추가 비용
                    slope = float(self.slope_arr[i, j])
                    slope_cost = 1.0 + slope * slope_weight
                    cost_map[i, j] = max(min_cost, base_cost * slope_cost)
                    
        return cost_map
    
    def is_passable(self, x: int, y: int) -> bool:
        """해당 위치가 통과 가능한지 확인"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.cost_map[y, x] != np.inf

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        """8방향 이웃 셀과 이동 비용 반환"""
        neighbors = []
        directions = [
            (-1, -1, 1.414), (-1, 0, 1.0), (-1, 1, 1.414),
            (0, -1, 1.0),                   (0, 1, 1.0),
            (1, -1, 1.414),  (1, 0, 1.0),  (1, 1, 1.414)
        ]
        
        for dx, dy, base_dist in directions:
            nx, ny = x + dx, y + dy
            if self.is_passable(nx, ny):
                cost = self.cost_map[ny, nx] * base_dist
                neighbors.append((nx, ny, cost))
        
        return neighbors
    #!TEMP <<<<
    
    # def is_impassable(self, x, y) -> bool:
    #     xi, yi = int(x), int(y)
    #     if not (0 <= yi < self.height and 0 <= xi < self.width):
    #         return True
    #     # 호수는 통과 불가
    #     if self.lake_mask[yi, xi]:
    #         return True
    #     return False
    
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

    def is_road(self, x, y) -> bool:
        xi, yi = int(x), int(y)
        return (0 <= yi < self.height and 0 <= xi < self.width
                and self.road_mask[yi, xi])

    def add_obstacle(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = 1  # Mark as obstacle

    def is_obstacle(self, x, y):
        return self.grid[y][x] == 1

    def movement_factor(self, x, y):
        xi, yi = int(x), int(y)
        code = (
            self.grid[yi, xi] if (0 <= xi < self.width and 0 <= yi < self.height) else 0
        )
        return self.terrain_cost.get(code, 1.0)
    
    # def get_terrain(self, x, y):  # Get terrain type at (x, y)
    #     if 0 <= x < self.width and 0 <= y < self.height:
    #         return self.grid[x][y]
    #     return None

    # def is_road(self, x, y):
    #     xi, yi = int(x), int(y)
    #     return 0 <= xi < self.width and 0 <= yi < self.height and self.grid[xi, yi] == 2

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
        
#!TEMP >>>>
def astar_pathfinding(battle_map: Map, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    """A* 알고리즘으로 최적 경로 탐색"""
    def heuristic(a, b):
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    
    open_set = []
    heappush(open_set, (0, start))
    
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_set:
        current = heappop(open_set)[1]
        
        if current == goal:
            # 경로 재구성
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        
        for neighbor_x, neighbor_y, move_cost in battle_map.get_neighbors(*current):
            neighbor = (neighbor_x, neighbor_y)
            tentative_g = g_score[current] + move_cost
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heappush(open_set, (f_score[neighbor], neighbor))
    
    return []  # 경로를 찾을 수 없음

def build_flow_field(battle_map: Map, goal: Tuple[int, int]) -> np.ndarray:
    """플로우 필드 생성 - 모든 셀에서 목표로의 최적 방향"""
    h, w = battle_map.height, battle_map.width
    flow_field = np.zeros((h, w, 2), dtype=float)
    distance_field = np.full((h, w), np.inf)
    
    # Dijkstra 알고리즘으로 최단 거리 계산
    pq = []
    goal_x, goal_y = goal
    distance_field[goal_y, goal_x] = 0
    heappush(pq, (0, goal_x, goal_y))
    
    while pq:
        dist, x, y = heappop(pq)
        
        if dist > distance_field[y, x]:
            continue
            
        for nx, ny, cost in battle_map.get_neighbors(x, y):
            new_dist = dist + cost
            if new_dist < distance_field[ny, nx]:
                distance_field[ny, nx] = new_dist
                heappush(pq, (new_dist, nx, ny))
    
    # 각 셀에서 가장 가까운 이웃으로의 방향 계산
    for y in range(h):
        for x in range(w):
            if distance_field[y, x] == np.inf:
                continue
                
            best_dir = (0, 0)
            best_dist = distance_field[y, x]
            
            for nx, ny, _ in battle_map.get_neighbors(x, y):
                if distance_field[ny, nx] < best_dist:
                    best_dist = distance_field[ny, nx]
                    best_dir = (nx - x, ny - y)
            
            # 방향 벡터 정규화
            if best_dir != (0, 0):
                length = math.sqrt(best_dir[0]**2 + best_dir[1]**2)
                flow_field[y, x] = [best_dir[0]/length, best_dir[1]/length]
    
    return flow_field

# 전술적 이동 패턴 추가
class TacticalManager:
    """전술적 이동 패턴 관리"""
    
    @staticmethod
    def get_tactical_destination(troop, target, battle_map: Map, allied_troops: List):
        """부대 유형과 상황에 따른 전술적 목적지 계산"""
        
        if not target:
            return troop.coord
        
        # 전차: 측면 공격 시도
        if troop.type == UnitType.TANK:
            return TacticalManager.get_flanking_position(troop, target, battle_map)
        
        # 대전차 무기: 매복 위치 선택
        elif UnitType.is_anti_tank(troop.type):
            return TacticalManager.get_ambush_position(troop, target, battle_map)
        
        # 보병: 엄폐물 활용
        elif troop.type == UnitType.INFANTRY:
            return TacticalManager.get_cover_position(troop, target, battle_map)
        
        # 간접화력: 화력지원 위치
        elif UnitType.is_indirect_fire(troop.type):
            return TacticalManager.get_fire_support_position(troop, target, battle_map)
        
        # 기본: 직접 접근
        else:
            return target.coord
    
    @staticmethod
    def get_flanking_position(troop, target, battle_map: Map):
        """측면 공격 위치 계산"""
        target_x, target_y = target.coord.x, target.coord.y
        
        # 목표 주변 90° 좌우 측면 위치들 검사
        flank_positions = []
        for angle in range(-90, 91, 30):  # -90°~90°, 30° 간격
            rad = math.radians(angle)
            
            # 500m 거리의 측면 위치
            distance = 50  # 픽셀 단위 (500m)
            flank_x = target_x + distance * math.cos(rad)
            flank_y = target_y + distance * math.sin(rad)
            
            # 지형이 통과 가능하고 유리한 위치인지 확인
            if battle_map.is_passable(int(flank_x), int(flank_y)):
                # 고도가 높은 위치 선호
                elevation = battle_map.dem_arr[int(flank_y), int(flank_x)]
                target_elevation = battle_map.dem_arr[int(target_y), int(target_x)]
                
                score = elevation - target_elevation  # 고도 차이
                
                # 숲이나 엄폐물 가까이 있으면 추가 점수
                if battle_map.wood_mask[int(flank_y), int(flank_x)]:
                    score += 10
                
                flank_positions.append((Coord(flank_x, flank_y, elevation), score))
        
        # 가장 유리한 위치 선택
        if flank_positions:
            best_pos = max(flank_positions, key=lambda x: x[1])
            return best_pos[0]
        
        return target.coord
    
    @staticmethod
    def get_ambush_position(troop, target, battle_map: Map):
        """매복 위치 계산 - 엄폐물과 사거리 고려"""
        target_x, target_y = target.coord.x, target.coord.y
        weapon_range = troop.range_km * 100  # km를 픽셀로 변환
        
        ambush_positions = []
        
        # 무기 사거리 내에서 엄폐 가능한 위치 탐색
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            
            # 사거리의 80% 거리에서 매복
            distance = weapon_range * 0.8
            amb_x = target_x + distance * math.cos(rad)
            amb_y = target_y + distance * math.sin(rad)
            
            if not battle_map.is_passable(int(amb_x), int(amb_y)):
                continue
            
            score = 0
            
            # 숲이나 높은 곳 선호
            if battle_map.wood_mask[int(amb_y), int(amb_x)]:
                score += 20
            
            elevation = battle_map.dem_arr[int(amb_y), int(amb_x)]
            target_elevation = battle_map.dem_arr[int(target_y), int(target_x)]
            if elevation > target_elevation:
                score += 15
            
            # 도로에서 멀수록 좋음 (은밀성)
            if not battle_map.road_mask[int(amb_y), int(amb_x)]:
                score += 10
            
            ambush_positions.append((Coord(amb_x, amb_y, elevation), score))
        
        if ambush_positions:
            best_pos = max(ambush_positions, key=lambda x: x[1])
            return best_pos[0]
        
        return target.coord
    
    @staticmethod
    def get_cover_position(troop, target, battle_map: Map):
        """엄폐 위치 계산"""
        # 목표와의 중간 지점에서 엄폐물 찾기
        mid_x = (troop.coord.x + target.coord.x) / 2
        mid_y = (troop.coord.y + target.coord.y) / 2
        
        cover_positions = []
        
        # 중간 지점 주변에서 엄폐 가능한 위치 탐색
        for dx in range(-20, 21, 5):
            for dy in range(-20, 21, 5):
                cover_x, cover_y = mid_x + dx, mid_y + dy
                
                if not battle_map.is_passable(int(cover_x), int(cover_y)):
                    continue
                
                score = 0
                
                # 숲, 건물, 높은 지형 선호
                if battle_map.wood_mask[int(cover_y), int(cover_x)]:
                    score += 25
                
                # 고도 차이
                elevation = battle_map.dem_arr[int(cover_y), int(cover_x)]
                if elevation > battle_map.dem_arr[int(target.coord.y), int(target.coord.x)]:
                    score += 10
                
                cover_positions.append((Coord(cover_x, cover_y, elevation), score))
        
        if cover_positions:
            best_pos = max(cover_positions, key=lambda x: x[1])
            return best_pos[0]
        
        return target.coord
    
    @staticmethod
    def get_fire_support_position(troop, target, battle_map: Map):
        """화력지원 위치 계산"""
        # 간접화력은 목표에서 멀리, 높은 곳에서 사격
        target_x, target_y = target.coord.x, target.coord.y
        weapon_range = troop.range_km * 100  # km를 픽셀로 변환
        
        support_positions = []
        
        # 사거리 내에서 가장 높은 위치 찾기
        for distance in [weapon_range * 0.7, weapon_range * 0.8, weapon_range * 0.9]:
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                sup_x = target_x + distance * math.cos(rad)
                sup_y = target_y + distance * math.sin(rad)
                
                if not battle_map.is_passable(int(sup_x), int(sup_y)):
                    continue
                
                elevation = battle_map.dem_arr[int(sup_y), int(sup_x)]
                
                # 고도가 높을수록, 도로 접근성이 좋을수록 선호
                score = elevation
                if battle_map.road_mask[int(sup_y), int(sup_x)]:
                    score += 20
                
                support_positions.append((Coord(sup_x, sup_y, elevation), score))
        
        if support_positions:
            best_pos = max(support_positions, key=lambda x: x[1])
            return best_pos[0]
        
        return target.coord
#!TEMP <<<<