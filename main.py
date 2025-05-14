import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from enum import Enum
from collections import namedtuple
import math
import random
import matplotlib.pyplot as plt
from typing import List, Tuple
import os
import glob

# MAX_TIME = 100.0 # 최대 시뮬레이션 시간 (분 단위) #for testingfrom typing import List, Tuple
MAX_TIME = 2880.0 # 최대 시뮬레이션 시간 (분 단위) #TODO: 복구 요망
# TIME_STEP = 0.01 # 시뮬레이션 시간 간격 (분 단위)
TIME_STEP = 1.0
BLUE_HIT_PROB_BUFF = 0.8 # BLUE 진영의 명중 확률 버프


# Blueprint: 카테고리별로 영역(사각형)과 소속태그를 매핑
# placement_zones[카테고리][키] = (x_range, y_range, affiliation)
placement_zones = {
    "TANK": {
        "blue": ((0, 30), (45, 55), "FixedDefense"),
        "red_reserve": ((70, 100), (45, 55), "Reserve"),
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
    # "ARTILLERY": {
    #     "blue":         ((15, 17), (48, 52), "FixedDefense"),
    #     "red_reserve":  ((85, 87), (48, 52), "Reserve"),
    #     "red_E1":       ((3,  7),  (43, 47), "E1"),
    #     "red_E2":       ((3,  7),  (53, 57), "E2"),
    #     "red_E3":       ((3,  7),  (63, 67), "E3"),
    #     "red_E4":       ((3,  7),  (73, 77), "E4"),
    # },
    "AT_WEAPON": {
        "blue": ((0, 30), (45, 55), "FixedDefense"),
        "red_reserve": ((70, 100), (45, 55), "Reserve"),
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

# Probability distributions for firing times
def triangular_distribution(M, C):
    return np.random.triangular(M - C, M, M + C)


def normal_distribution(mean, variance):
    return np.random.normal(mean, np.sqrt(variance))


def uniform_distribution(a, b):
    return np.random.uniform(a, b)

def constant_distribution(value):
    return value

def exp_decay(range_limit, p_hit, decay_const):
    return lambda r: (p_hit if r <= range_limit else 0) * math.exp(-r / decay_const)

def constant_func(value):
    return lambda x: value

def direct_fire_pk_func(coeff=1.0):
    return lambda p: HitState.CKILL if p < 0.7*coeff else (
                     HitState.MKILL if p < 0.9*coeff else
                     HitState.FKILL)

def simple_pk_func(pk):
    return lambda p: HitState.CKILL if p < pk else HitState.MISS

class UnitType(Enum):
    TANK = "tank" # 전차
    MORTAR = "mortar"   # 박격포
    HOWITZER = "howitzer"   # 견인포
    SPG = "spg" # 자주포
    MLRS = "mlrs" # 다연장로켓포
    ATGM = "atgm" # 대전차미사일
    RPG = "rpg" # 휴대용 대전차 로켓포
    RECOILLESS = "recoilless"   # 무반동포
    INFANTRY_AT = "infantry_at" # 보병 대전차
    INFANTRY = "infantry" # 보병
    SUPPLY = "supply" # 보급차량
    VEHICLE = "vehicle" # 차량
    APC = "apc" # 장갑차
    DIR_FIRE_UNIT = ["tank", "atgm", "infantry_at"]
    INDIRECT_FIRE_UNIT = ["mortar", "howitzer", "spg", "mlrs"]
    ANTI_TANK = ["atgm", "recoilless", "rpg"]

class UnitStatus(Enum):
    ALIVE = "alive" # 살아있음
    DESTROYED = "destroyed" # 파괴됨
    DAMAGED_MOBILITY = "mobility_damaged" # 기동불능
    DAMAGED_FIREPOWER = "firepower_damaged" # 화력불능
    OUT_OF_RANGE = "out_of_range" # 사거리 초과
    MOVING = "moving" # 이동중
    STATIONARY = "stationary" # 정지중
    RELOADING = "reloading" # 재장전중
    SPOTTED = "spotted" # 발견됨
    UNSPOTTED = "unspotted" # 발견되지 않음
    HIDDEN = "hidden" # 은폐됨
    UNCOVERED = "uncovered" # 은폐되지 않음
    ENGAGED = "engaged" # 교전중
    UNENGAGED = "unengaged" # 비교전중
    MOVEMENT_ORDER = "movement_order" # 이동명령
    ENGAGEMENT_ORDER = "engagement_order" # 교전명령
    RELOAD_ORDER = "reload_order" # 재장전명령
    SPOT_ORDER = "spot_order" # 발견명령
    UNSPOT_ORDER = "unspot_order" # 발견되지 않음 명령
    HIDE_ORDER = "hide_order" # 은폐명령
    UNCOVER_ORDER = "uncover_order" # 은폐되지 않음 명령

class AmmoStatus(Enum):
    FULL = "full" # 완전
    LOW = "low" # 부족
    EMPTY = "empty" # 없음

class UnitAction(Enum):
    MOVE = "move" # 이동
    FIRE = "fire" # 발사
    SPOT = "spot" # 발견
    UNSPOT = "unspot" # 발견되지 않음
    HIDE = "hide" # 은폐
    UNCOVER = "uncover" # 은폐되지 않음
    RELOAD = "reload" # 재장전
    ENGAGE = "engage" # 교전
    UNENGAGE = "unengage" # 비교전
    SUPPLY = "supply" # 보급
    REPAIR = "repair" # 수리

class HitState(Enum):
    CKILL = "catastrophic-kill" # 완전파괴
    MKILL = "mobility-kill" # 기동불능
    FKILL = "firepower-kill" # 화력불능
    MISS = "miss" # 명중하지 않음

# 유닛 세부 정보를 담을 구조체
UnitCategory = namedtuple("UnitCategory", ["blue", "red"])

class UnitComposition(Enum):
    TANK = UnitCategory(
        blue={"Sho't_Kal": 170},
        red={"T-55": 300, "T-62": 200}
    )

    AT_WEAPON = UnitCategory(
        blue={"BGM-71_TOW": 12, "106mm_M40_Recoilless_Rifle": 36, "M72_LAW": 12},
        red={"9M14_Malyutka": 54, "107mm_B-11_Recoilless_Rifle": 36, "RPG-7": 54}
    )

    # TANK = UnitCategory(
    #     blue={"Sho't_Kal": 170},
    #     red={"T-55": 300, "T-62": 200}
    # )

    # # APC = UnitCategory( #TODO: 장갑차 추가, 사격 확률
    # #     blue={"M113": 20},
    # #     red={"BMP/BTR": 200}
    # # )
    # # INFANTRY = UnitCategory(    #TODO: 보병 추가
    # #     blue={"Golani×2 + ATGM중대": 850},
    # #     red={"보병여단3 + 기계화여단3": 4800}
    # # )
    # ARTILLERY = UnitCategory(
    #     blue={"60mm_Mortar": 12, "105mm_Howitzer": 20},
    #     red={"122mm_SPG": 200, "BM-21_MLRS": 200}  # "발" 단위는 맥락상 자주포 수량과 통합 처리
    # )

    # AT_WEAPON = UnitCategory(
    #     blue={"BGM-71_TOW": 12, "106mm_M40_Recoilless_Rifle": 36, "M72_LAW": 12},
    #     red={"9M14_Malyutka": 54, "107mm_B-11_Recoilless_Rifle": 36, "RPG-7": 54}
    # )
    # SUPPLY = UnitCategory(
    #     blue={"Blue_Supply_Truck": 40},
    #     red={"Red_Supply_Truck": 60}
    # )

class UnitSpec:
    def __init__(self, name, team, unit_type, range_km, ph_func, pk_func, target_delay_func=constant_func(2.0), fire_time_func=constant_func(1.0), speed_road_kmh=1000, speed_offroad_kmh=1000):
        self.name = name
        self.team = team  # "blue" or "red"
        self.unit_type = unit_type  # UnitType Enum
        self.range_km = range_km
        self.ph_func = ph_func  # A function that returns hit probability
        self.pk_func = pk_func  # function that returns HitState
        self.target_delay_func = target_delay_func
        self.fire_time_func = fire_time_func

        self.speed_road_kmh = speed_road_kmh
        self.speed_offroad_kmh = speed_offroad_kmh

UNIT_SPECS = {  # TODO: unit ph_func, pk_func 추가
    "Sho't_Kal": UnitSpec(
        name="Sho't_Kal",
        team="blue",
        unit_type=UnitType.TANK,
        range_km=2.5,
        ph_func=exp_decay(2.5, 0.75, 2.5),
        pk_func=direct_fire_pk_func(),
        # target_delay_func=constant_func(1.0),
        # fire_time_func=constant_func(1.0),
        # speed_road_kmh=35, 
        # speed_offroad_kmh=20
    ),
    "T-55": UnitSpec(
        name="T-55",
        team="red",
        unit_type=UnitType.TANK,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.7, 2.0),
        pk_func=direct_fire_pk_func(),
        # speed_road_kmh=50, 
        # speed_offroad_kmh=25
    ),
    "T-62": UnitSpec(
        name="T-62",
        team="red",
        unit_type=UnitType.TANK,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.68, 2.0),
        pk_func=direct_fire_pk_func(),
        # speed_road_kmh=50, 
        # speed_offroad_kmh=30
    ),
    "60mm_Mortar": UnitSpec(
        name="60mm_Mortar",
        team="blue",
        unit_type=UnitType.MORTAR,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.6, 2.0),
        pk_func="exp(-r/2.0)",
    ),
    "105mm_Howitzer": UnitSpec(
        name="105mm_Howitzer",
        team="blue",
        unit_type=UnitType.HOWITZER,
        range_km=11.0,
        ph_func=exp_decay(11.0, 0.8, 11.0),
        pk_func="exp(-r/11.0)",
    ),
    "122mm_SPG": UnitSpec(
        name="122mm_SPG",
        team="red",
        unit_type=UnitType.SPG,
        range_km=15.0,
        ph_func=exp_decay(10.0, 0.75, 10.0),
        pk_func="exp(-r/10.0)",
    ),
    "BM-21_MLRS": UnitSpec(
        name="BM-21_MLRS",
        team="red",
        unit_type=UnitType.MLRS,
        range_km=20.0,
        ph_func=exp_decay(20.0, 0.85, 20.0),
        pk_func="exp(-r/20.0)",
    ),
    "BGM-71_TOW": UnitSpec(
        name="BGM-71_TOW",
        team="blue",
        unit_type=UnitType.ATGM,
        range_km=3.75,
        ph_func=constant_func(0.9),
        pk_func=direct_fire_pk_func(0.9),
        # pk_func=simple_pk_func(0.9),
    ),
    "9M14_Malyutka": UnitSpec(
        name="9M14_Malyutka",
        team="red",
        unit_type=UnitType.ATGM,
        range_km=3.0,
        ph_func=constant_func(0.85),
        pk_func=direct_fire_pk_func(0.85),
        # pk_func=simple_pk_func(0.85),
    ),
    "106mm_M40_Recoilless_Rifle": UnitSpec(
        name="106mm_M40_Recoilless_Rifle",
        team="blue",
        unit_type=UnitType.RECOILLESS,
        range_km=1.2,
        ph_func=constant_func(0.8),
        pk_func=direct_fire_pk_func(),
    ),
    "107mm_B-11_Recoilless_Rifle": UnitSpec(
        name="107mm_B-11_Recoilless_Rifle",
        team="red",
        unit_type=UnitType.RECOILLESS,
        range_km=0.6,
        ph_func=constant_func(0.75),
        pk_func=direct_fire_pk_func(),
    ),
    "M72_LAW": UnitSpec(
        name="M72_LAW",
        team="blue",
        unit_type=UnitType.RPG,
        range_km=0.3,
        ph_func=constant_func(0.6),
        pk_func=direct_fire_pk_func(0.6),
        # pk_func=simple_pk_func(0.6),
    ),
    "RPG-7": UnitSpec(
        name="RPG-7",
        team="red",
        unit_type=UnitType.RPG,
        range_km=0.5,
        ph_func=constant_func(0.65),
        pk_func=direct_fire_pk_func(0.65),
        # pk_func=simple_pk_func(0.65),
    ),
    "M113": UnitSpec(
        name="M113",
        team="blue",
        unit_type=UnitType.APC,
        range_km=2.0,
        ph_func=constant_func(0.30),
        pk_func="exp(-r/2.0)", # TODO
        speed_road_kmh=64, 
        speed_offroad_kmh=np.random.randint(40, 45)
    ),

    "BMP-1": UnitSpec(
        name="BMP-1",
        team="red",
        unit_type=UnitType.APC,
        range_km=0.8,
        ph_func=constant_func(0.60),
        pk_func="exp(-r/2.0)", # TODO
        speed_road_kmh=65, 
        speed_offroad_kmh=45
    ),

    # "BTR-60": UnitSpec(
    #     name="BTR-60",
    #     team="red",
    #     unit_type=UnitType.APC,
    #     range_km=0.8,
    #     ph_func=constant_func(0.60),
    #     pk_func="exp(-r/2.0)", # TODO

    #     speed_road_kmh=80, 
    #     speed_offroad_kmh=50
    # ),

    "Golani×2 + ATGM중대": UnitSpec(
        name="Golani×2 + ATGM중대",
        team="blue",
        unit_type=UnitType.INFANTRY,
        range_km=0.3,  # 예: AK-47 유효사거리 0.3km
        ph_func=constant_func(0.2),  # 예: Ph=0.2 at 300m
        pk_func="exp(-r/0.3)",
        speed_road_kmh=5,
        speed_offroad_kmh=5
    ),
    "보병여단3 + 기계화여단3": UnitSpec(
        name="보병여단3 + 기계화여단3",
        team="red",
        unit_type=UnitType.INFANTRY,
        range_km=0.3,
        ph_func=constant_func(0.2),
        pk_func="exp(-r/0.3)",
        speed_road_kmh=5,
        speed_offroad_kmh=5
    ),

    "Blue_Supply_Truck": UnitSpec(
        name="Blue_Supply_Truck",
        team="blue",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_func="exp(-r/0.1)",
        speed_road_kmh=80, 
        speed_offroad_kmh=40
    ),
    "Red_Supply_Truck": UnitSpec(
        name="Red Supply_Truck",
        team="red",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_func="exp(-r/0.1)",
        speed_road_kmh=80, 
        speed_offroad_kmh=40
    ),
}


class TimelineEvent: # Timeline event types
    def __init__(self, time, time_str, description, t_a, t_f):
        self.time = time  # Event time
        self.time_str = time_str  # Event time as string
        # self.event_type = event_type  # Event type (e.g., "fire", "move")
        self.description = description
        self.t_a = t_a  # Time of action
        self.t_f = t_f  # Time of fire


timeline = [
    TimelineEvent(0, "13:55", "BLUE 전차70대 방어진지 배치 명령", 0.5, 1),
    TimelineEvent(5, "14:00", "BLUE 모든 소대 방어진지 점검 완료", None, None),
    TimelineEvent(30, "14:25", "RED(E1) 교량전차·보병 투입 시도", 1, 1),
    TimelineEvent(60, "14:55", "RED(E1) 실패 후 예비포 지원사격", 0.5, 1),
    TimelineEvent(125, "15:40", "RED(E2) 모로코 여단 돌격 시작", 2, 1.5),
    TimelineEvent(130, "15:45", "BLUE Tel Shaeta·Hermonit 방어 강화", 0.5, 1),
    TimelineEvent(180, "16:35", "RED 중대 E2 후속 기갑 소규모 침투 시도", 1, 1),
    TimelineEvent(300, "18:15", "BLUE Barak여단 65대 증강 완료 보고", None, None),
    TimelineEvent(360, "19:15", "야간 준비: BLUE 은폐·탐지·매복 배치", None, None),
    TimelineEvent(365, "19:20", "RED(E3) 78·82기갑 동시 투입", 1.5, 2),
    TimelineEvent(425, "20:25", "야간 주요 교전 고착", None, None),
    TimelineEvent(1440, "07:00(2일)", "RED 추가 E4 예비포·보병투입", 1, 1),
    TimelineEvent(2880, "13:55(4일)", "종료: 전멸 or 시간만료", None, None),
]

class Velocity: # Velocity class to store velocity information
    def __init__(self, x=0, y=0, z=0):
        self.x=x
        self.y=y
        self.z=z

class Coord: # Coordinate class to store x, y, z coordinates
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x=x
        self.y=y
        self.z=z

    def next_coord(self, velocity:Velocity):
        # Update the coordinates based on velocity and time
        self.x += velocity.x * TIME_STEP
        self.y += velocity.y * TIME_STEP
        self.z += velocity.z * TIME_STEP


class Map: # Map class to store map information
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
    
    def get_terrain(self, x, y): # Get terrain type at (x, y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

    def is_road(self, x, y):
        xi, yi = int(x), int(y)
        return (0 <= xi < self.width and 0 <= yi < self.height and
                self.grid[xi, yi] == 2)

    def movement_factor(self, x, y):
        xi, yi = int(x), int(y)
        code = self.grid[xi, yi] if (0 <= xi < self.width and 0 <= yi < self.height) else 0
        return self.terrain_cost.get(code, 1.0)


class History: # Store history of troop actions and troop status
    def __init__(self, time):
        self.current_time = time
        self.battle_log=[]
        self.status_data = {
            "time": [], 
            }
        
        self.visualization_data = {
            "time": [],
            "unit": [],
            "x": [],
            "y": [],
            "z": []
        }

    def update_time(self, time): # update current time
        if time >= self.current_time:
            self.current_time = time
        else:
            raise ValueError("Time cannot be set to a past value.")
        self.current_time = time

    def init_status_data(self, troop_list): # initialize status data
        for troop in troop_list:
            if f"{troop.id}_status" not in self.status_data:
                self.status_data[f"{troop.id}_status"] = []
                self.status_data[f"{troop.id}_target"] = []
                self.status_data[f"{troop.id}_fire_time"] = []
        self.add_to_status_data(troop_list)

    def add_to_battle_log(self,type_,shooter,target, target_type, result): # add to battle log
        self.battle_log.append([self.current_time,shooter,type_,target, target_type, result])

    def add_to_status_data(self, troop_list): # add to status data
        self.status_data["time"].append(self.current_time)
        for troop in troop_list:
            self.status_data[f"{troop.id}_status"].append(troop.status.value)
            self.status_data[f"{troop.id}_target"].append(troop.target.id if troop.target else None)
            self.status_data[f"{troop.id}_fire_time"].append(troop.next_fire_time if troop.alive else None)

        for troop in troop_list:    
            if troop.alive:
                self.visualization_data["time"].append(self.current_time)
                self.visualization_data["unit"].append(troop.id)
                self.visualization_data["x"].append(troop.coord.x)
                self.visualization_data["y"].append(troop.coord.y)
                self.visualization_data["z"].append(troop.coord.z)

    def get_battle_log(self): # return battle log
        return self.battle_log  

    def get_status_data(self): # return status data
        return self.status_data

    def save_battle_log(self, foldername="res/res0"): # save battle log to file
        columns = ["time", "shooter", "shooter_type", "target", "target_type", "result"]
        df = pd.DataFrame(self.battle_log, columns=columns)
        df.to_csv(foldername + "/battle_log.csv", index=False)
        print("Battle log saved to battle_log.csv")


    def save_status_data(self, foldername="res/res0"): # save status data to file
        df = pd.DataFrame(self.status_data)
        df.to_csv(foldername + "/status_data.csv", index=False)
        print("Status data saved to status_data.csv")

        df_2 = pd.DataFrame(self.visualization_data)
        df_2.to_csv(foldername + "/visualization_data.csv", index=False)
        print("Visualization data saved to visualization_data.csv")
    
    
    def save_status_data_new(self, troop_list, filename="status_data.csv"): # save status data to file
        data = []
        for t_idx, time in enumerate(self.status_data["time"]):
            time_sec = round(time * 60, 2)  # Convert from minutes to seconds
            for troop in troop_list:
                if troop.id in self.status_data:
                    # Get current position
                    x = troop.coord.x
                    y = troop.coord.y
                    z = troop.coord.z
                    data.append([time_sec, troop.id, x, y, z])

        df = pd.DataFrame(data, columns=["time", "unit", "x", "y", "z"])
        df.to_csv(filename, index=False)
        print("Status data saved to status_data.csv")

    def draw_troop_positions(self, troop_list, current_time, save_dir="frames"):
        plt.figure(figsize=(8, 8))
        for troop in troop_list:
            if not troop.alive:
                continue
            color = "blue" if troop.team == "blue" else "red"
            marker = "o" if troop.type == UnitType.TANK else "s"
            plt.scatter(troop.coord.x, troop.coord.y, c=color, marker=marker, label=troop.id, alpha=0.7, s=30)
        plt.title(f"Troop Positions at T={current_time:.0f} min")
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/frame_{int(current_time):05d}.png")
        plt.close()

    def plot_team_strength_over_time(self, foldername="res/res0"):
        df = pd.DataFrame(self.status_data)

        time_col = df["time"]
        blue_cols = [col for col in df.columns if "_status" in col and col.startswith("B")]
        red_cols = [col for col in df.columns if "_status" in col and col.startswith("R")]

        blue_alive = df[blue_cols].apply(lambda row: sum(status == "alive" for status in row), axis=1)
        red_alive = df[red_cols].apply(lambda row: sum(status == "alive" for status in row), axis=1)

        plt.figure(figsize=(10, 5))
        plt.plot(time_col, blue_alive, label="BLUE Troops Alive")
        plt.plot(time_col, red_alive, label="RED Troops Alive")
        plt.xlabel("Time (min)")
        plt.ylabel("Number of Troops Alive")
        plt.title("Team Strength Over Time")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(foldername+"/plot.png", dpi=300)  # ✅ 파일 저장
        plt.show()
        print(f"Graph saved as {foldername}/plot.png")

class Troop: # Troop class to store troop information and actions
    # Static variables to keep track of troop IDs
    counter = {}

    def __init__(self, unit_name, coord=Coord(), affiliation: str = None):
        spec = UNIT_SPECS[unit_name]
        self.spec = spec
        self.team = spec.team
        self.type = spec.unit_type
        self.name = spec.name
        self.range_km = spec.range_km
        self.ph_func = spec.ph_func
        self.pk_func = spec.pk_func
        self.target_delay_func = spec.target_delay_func
        self.fire_time_func = spec.fire_time_func

        self.affiliation = affiliation

        self.id = self.assign_id()
        self.next_fire_time = 0.0  # Initial fire time
        self.target = None
        self.alive = True
        self.coord = coord # Coordinate object to store (x, y, z) coordinates
        self.velocity = Velocity()  # Placeholder for velocity (x, y, z)
        self.status = UnitStatus.ALIVE  # Placeholder for unit status
        self.ammo = 100     # ammo level (0-100%)
        self.supply = 100 # supply level (0-100%)

    @classmethod
    def batch_create(cls, category, side, x_range, y_range, affiliation):
        troops = []
        for unit_name, count in getattr(category.value, side).items():
            if unit_name not in UNIT_SPECS:
                print(f"[ERROR] UNIT_SPECS에 없는 유닛명: {unit_name}")
                continue
            for _ in range(count):
                x = np.random.uniform(*x_range)
                y = np.random.uniform(*y_range)
                troop = cls(unit_name, Coord(x, y, 0), affiliation=affiliation)
                if not isinstance(troop, Troop):
                    print(f"[ERROR] 잘못 생성된 troop: {troop}")
                troops.append(troop)
        return troops

    def assign_id(self):
        key = f"{self.team}_{self.type.value}"
        if key not in Troop.counter:
            Troop.counter[key] = 1
        label = f"{self.team[0].upper()}_{self.type.value[:2].upper()}{Troop.counter[key]}"
        Troop.counter[key] += 1
        return label

    def update_coord(self): # Update coordinates
        self.coord.next_coord(self.velocity)

    def update_velocity(self, new_velocity): # Update velocity
        self.velocity = new_velocity

    def get_distance(self, other_troop): # Calculate distance to another troop
        return math.sqrt(
            (self.coord.x - other_troop.coord.x) ** 2 +
            (self.coord.y - other_troop.coord.y) ** 2 +
            (self.coord.z - other_troop.coord.z) ** 2
        )

    def get_t_a(self):
        return self.target_delay_func(0) if self.target else 0
    def get_t_f(self):
        return self.fire_time_func(0) if self.target else 0
    
        # ---- 역할별 전략: 유형별 타겟팅 로직 ----
    def filter_priority(self, cand_list):
        if self.type == UnitType.TANK:
            return sorted(cand_list, key=lambda c: (
                c[0].type != UnitType.TANK,
                c[0].type != UnitType.ATGM,
                c[0].type != UnitType.APC,
                c[1],  # distance
            ))
        elif self.type == UnitType.APC:
            return sorted(cand_list, key=lambda c: (
                c[0].type != UnitType.INFANTRY,
                c[1],
            ))
        elif self.type in {UnitType.ATGM, UnitType.RPG, UnitType.RECOILLESS, UnitType.INFANTRY_AT}:
            at_targets = [c for c in cand_list if c[0].type in {UnitType.TANK, UnitType.APC}]
            return sorted(at_targets, key=lambda c: (c[2], c[1]))
        elif self.type in {UnitType.MORTAR, UnitType.HOWITZER, UnitType.SPG, UnitType.MLRS}:
            return sorted(cand_list, key=lambda c: (
                c[0].status != UnitStatus.STATIONARY,
                c[1],
            ))
        elif self.type == UnitType.INFANTRY:
            return sorted(cand_list, key=lambda c: (
                c[0].type != UnitType.INFANTRY,
                c[1],
            ))
        elif self.type == UnitType.SUPPLY:
            self.target = None
            self.next_fire_time = float("inf")
            return
        else:
            return sorted(cand_list, key=lambda c: (c[2], c[1]))

    def assign_target(self, current_time, enemy_list): #TODO: Implement target assignment logic
        # 밤 시간대: 19:00 ~ 06:00
        is_night = (360 <= current_time % 1440 <= 1080)

        if enemy_list:
            # 거리 계산 포함 유효 후보 필터링
            candidates = [] 
            for e in enemy_list:
                if not e.alive:
                    continue
                if e.status == UnitStatus.HIDDEN:
                    continue
                distance = self.get_distance(e)
                # if distance > self.range_km:  #TODO: 사거리 제한
                #     continue
                candidates.append((e, distance,1))
            
            if not candidates:
                self.target = None
                self.next_fire_time = float('inf')
                return
            
            priority_list = self.filter_priority(candidates)
            if not priority_list:
                self.target = None
                self.next_fire_time = float("inf")
                return

            # 최종 타겟 지정
            best_target = priority_list[0][0]
            ta = self.get_t_a()
            if is_night:
                ta *= 1.5  # 야간 표적 획득 시간 증가

            self.target = best_target
            self.next_fire_time = round(current_time + ta + self.get_t_f(), 2)

        else:
            self.target = None
            self.next_fire_time = float('inf')
            # print("no more enemy left")
            return
    

    def fire(self, current_time, enemy_list, history): #TODO: Implement firing logic
        if not self.alive:
            return
        
        if self.target.alive == False or self.target is None:
            self.assign_target(current_time, enemy_list)
            return 
        
        if self.status == UnitStatus.DAMAGED_FIREPOWER:
            self.next_fire_time = round(current_time + self.get_t_f(), 2)   
            return

        distance = self.get_distance(self.target)
        result = HitState.MISS
        hit_rand_var = np.random.rand()
        kill_rand_var = np.random.rand()

        # if self.type in UnitType.DIR_FIRE_UNIT:
        ph = self.ph_func(self.get_distance(self.target))
        # 야간 명중률 보정 (19:00 ~ 06:00 = 360~1080분)
        if 360 <= current_time % 1440 <= 1080:
            ph *= 0.8  # 20% 감소
            
        if self.target.team == "blue":
            ph = ph * BLUE_HIT_PROB_BUFF
        if ph < hit_rand_var:
            result = self.pk_func(kill_rand_var)
        else:
            result = HitState.MISS

        # elif self.type in UnitType.INDIRECT_FIRE_UNIT:
        #     ph = self.ph_func(self.get_distance(self.target))
        #     if ph < hit_rand_var:
        #         result = self.pk_func(kill_rand_var)
        #     else:
        #         result = HitState.MISS

        history.add_to_battle_log(
            type_=self.type.value,
            shooter=self.id,
            target=self.target.id if self.target else None,
            target_type=self.target.type.value if self.target else None,
            result=result.value,
        )

        if self.target.type == UnitType.TANK:
            if result == HitState.CKILL:
                self.target.alive = False
                self.target.status = UnitStatus.DESTROYED
                self.target = None
                self.assign_target(current_time, enemy_list)
                return
            elif result == HitState.MKILL:
                if self.target.status == UnitStatus.DAMAGED_FIREPOWER:
                    self.target.alive = False
                    self.target.status = UnitStatus.DESTROYED
                else:
                    self.target.status = UnitStatus.DAMAGED_MOBILITY
            elif result == HitState.FKILL:
                if self.target.status == UnitStatus.DAMAGED_MOBILITY:
                    self.target.alive = False
                    self.target.status = UnitStatus.DESTROYED
                else:
                    self.target.status = UnitStatus.DAMAGED_FIREPOWER

            self.next_fire_time = round(current_time + self.get_t_f(), 2)            

        else:
            if result == HitState.MISS:
                self.next_fire_time = round(current_time + self.get_t_f(), 2)  
                return
            else:
                self.target.alive = False
                self.target.status = UnitStatus.DESTROYED
                self.target = None
                self.assign_target(current_time, enemy_list)
                return

    def compute_velocity(self, dest: Coord, battle_map: Map, current_time: float) -> Velocity:
        # 1) 기본 속도 km/h→km/min
        on_road = battle_map.is_road(self.coord.x, self.coord.y)
        base_speed = (self.spec.speed_road_kmh if on_road else self.spec.speed_offroad_kmh) / 60

        # 2) 지형 가중치
        terrain_factor = battle_map.movement_factor(self.coord.x, self.coord.y)

        # 3) 낮/밤 가중치 (19:00–06:00 야간엔 50% 느려짐)
        hour = int((13*60 + 55 + current_time) // 60) % 24
        daynight = 1.0 if 6 <= hour < 19 else 1.5

        # 4) 실제 per-min 이동량
        speed = base_speed / terrain_factor / daynight

        # 5) 방향 단위 벡터
        dx, dy = dest.x - self.coord.x, dest.y - self.coord.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return Velocity(0,0,0)
        ux, uy = dx/dist, dy/dist

        move = speed * TIME_STEP
        return Velocity(ux * move, uy * move, 0)


def assign_target_all(current_time, troop_list): #TODO: Implement target assignment logic for all troops
    for troop in troop_list:
        enemies = [
            e for e in troop_list if troop.team != e.team and e.alive
        ]
        troop.assign_target(current_time, enemies)

def terminate(troop_list, current_time):
    # Check if all troops are dead or if the time limit is reached
    if current_time >= MAX_TIME:
        return True

    blue_troops = [t for t in troop_list if t.team == "blue"]
    red_troops = [t for t in troop_list if t.team == "red"]
    if not any(t.alive for t in blue_troops) or not any(t.alive for t in red_troops):
        return True

    for troop in troop_list:
        if troop.type==UnitType.TANK and troop.alive:
            return False
        if troop.type==UnitType.APC and troop.alive:
            return False
    return True

def generate_troop_list(troop_list, unit_name, num_units, coord, positions: List[Tuple[float,float,float]], affiliation: str):
    for _ in range(num_units):
        troop = Troop(
            unit_name=unit_name,
            coord=coord
        )
        troop_list.append(troop)

# def generate_all_troops():
#     troop_list = []
#     for category in UnitComposition:
#         unit_group = category.value

#         # BLUE 진영 유닛 생성
#         for unit_name, count in unit_group.blue.items():
#             generate_troop_list(
#                 troop_list,
#                 unit_name=unit_name,
#                 num_units=count,
#                 coord=Coord(1,1,0)
#             )

#         # RED 진영 유닛 생성
#         for unit_name, count in unit_group.red.items():
#             generate_troop_list(
#                 troop_list,
#                 unit_name=unit_name,
#                 num_units=count,
#                 coord=Coord(2,2,0)
#             )

#     return troop_list

def generate_initial_troops(placement_zones):
    troop_list = []
    for category in UnitComposition:
        # BLUE 고정 방어진지
        xr, yr, aff = placement_zones[category.name]["blue"]
        troop_list += Troop.batch_create(category, "blue", xr, yr, aff)

        # RED Reserve + E1~E4
        # for key in ["red_reserve","red_E1","red_E2","red_E3","red_E4"]:
        for key in ["red_reserve"]:
            xr, yr, aff = placement_zones[category.name][key]
            troop_list += Troop.batch_create(category, "red", xr, yr, aff)

    return troop_list

# def update_troop_location(troop_list, map): #TODO: Implement troop out of bounds check logic
#     for troop in troop_list:
#         if troop.alive:
#             # Update the troop's coordinates based on its velocity and time
#             troop.update_coord()
#             # Check if the troop is within the map boundaries
#             if not (0 <= troop.coord.x < map.width and 0 <= troop.coord.y < map.height):
#                 troop.alive = False  # Mark as dead if out of bounds

def update_troop_location(troop_list, battle_map, current_time):
    for troop in troop_list:
        if not troop.alive:
            continue
        dest = troop.target.coord if troop.target else troop.coord
        v = troop.compute_velocity(dest, battle_map, current_time)
        troop.update_velocity(v)
        troop.update_coord()
        if not (0 <= troop.coord.x < battle_map.width and
                0 <= troop.coord.y < battle_map.height):
            troop.alive = False


def clear_frames_folder(folder="frames"):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return
    for file in glob.glob(os.path.join(folder, "*.png")):
        os.remove(file)


def initialize_folders():
    os.makedirs("res", exist_ok=True)
    i=0
    while os.path.exists("res/res"+str(i)):
        i+=1
    os.makedirs("res/res" + str(i), exist_ok=True)
    os.makedirs("res/res" + str(i)+"/frames", exist_ok=True)
    return "res/res" + str(i)


def main():
    # Simulation parameters
    random.seed(42)  # For reproducibility
    np.random.seed(42)  # For reproducibility
    # Initialize simulation variables
    res_loc = initialize_folders()

    current_time = 0.0
    hist_record_time = 0.0
    history = History(time=current_time)
    battle_map = Map(100, 100)  # Create a map of size 100x100

    timeline_index = 0
    timeline_event = timeline[timeline_index]

    # troop_list = generate_all_troops()
    troop_list = generate_initial_troops(placement_zones = placement_zones)

    assign_target_all(current_time, troop_list)
    history.init_status_data(troop_list)

    while True:
        if hist_record_time==1.0:
            history.add_to_status_data(troop_list)  
            hist_record_time = 0.0
            history.draw_troop_positions(troop_list, current_time, save_dir=res_loc+"/frames")

        if terminate(troop_list=troop_list, current_time=current_time):
            history.save_battle_log(res_loc)
            history.save_status_data(res_loc)
            print("Simulation terminated.")
            history.plot_team_strength_over_time(res_loc)
            break

        current_time = round(current_time + TIME_STEP, 2)
        hist_record_time = round(hist_record_time + TIME_STEP, 2)
        history.update_time(current_time)
        # print(f"Current time: {current_time:.2f} min")

        if timeline_index < len(timeline):
            event = timeline[timeline_index]
            if current_time == event.time:
                print(f"[{event.time_str}] TIMELINE EVENT: {event.description}")
                timeline_index += 1

        living_troops = [f for f in troop_list if f.alive]

        # update_troop_location(living_troops, map=battle_map)
        update_troop_location(living_troops, battle_map, current_time)

        next_battle_time = min(f.next_fire_time for f in living_troops)
        # print(f"Next battle time: {next_battle_time:.2f} min")

        if current_time == next_battle_time:
            random.shuffle(living_troops)
            for troop in living_troops: #TODO: iterate randomly
                if troop.next_fire_time <= current_time:
                    enemies = [
                        e for e in troop_list if troop.team != e.team and e.alive
                    ]
                    troop.fire(current_time, enemies, history)

if __name__ == "__main__":

    main()
