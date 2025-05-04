import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from enum import Enum
from collections import namedtuple
import math


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

class UnitStatus(Enum):
    ALIVE = "alive" # 살아있음
    DESTROYED = "destroyed" # 파괴됨
    DAMAGED = "damaged" # 손상됨
    OUT_OF_AMMO = "out_of_ammo" # 탄약 없음
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

# 유닛 세부 정보를 담을 구조체
UnitCategory = namedtuple("UnitCategory", ["blue", "red"])

class UnitComposition(Enum):
    TANK = UnitCategory(
        blue={"Sho't_Kal": 170},
        red={"T-55": 300, "T-62": 200}
    )
    APC = UnitCategory( #TODO: 장갑차 추가, 사격 확률
        blue={"M113": 20},
        red={"BMP/BTR": 200}
    )
    INFANTRY = UnitCategory(    #TODO: 보병 추가
        blue={"Golani×2 + ATGM중대": 850},
        red={"보병여단3 + 기계화여단3": 4800}
    )
    ARTILLERY = UnitCategory(
        blue={"60mm_Mortar": 12, "105mm_Howitzer": 20},
        red={"122mm_SPG": 200, "BM-21_MLRS": 200}  # "발" 단위는 맥락상 자주포 수량과 통합 처리
    )
    AT_WEAPON = UnitCategory(
        blue={"BGM-71_TOW": 12, "106mm_M40_Recoilless_Rifle": 36, "M72_LAW": 12},
        red={"9M14_Malyutka": 54, "107mm_B-11_Recoilless_Rifle": 36, "RPG-7": 54}
    )
    SUPPLY = UnitCategory(
        blue={"Blue_Supply_Truck": 40},
        red={"Red_Supply_Truck": 60}
    )

class UnitSpec:
    def __init__(self, name, team, unit_type, range_km, ph_func, pk_model):
        self.name = name
        self.team = team  # "blue" or "red"
        self.unit_type = unit_type  # UnitType Enum
        self.range_km = range_km
        self.ph_func = ph_func  # A function that returns hit probability
        self.pk_model = pk_model  # Description or function of kill model


UNIT_SPECS = {
    "Sho't_Kal": UnitSpec(
        name="Sho't_Kal",
        team="blue",
        unit_type=UnitType.TANK,
        range_km=2.5,
        ph_func=exp_decay(2.5, 0.75, 2.5),
        pk_model="exp(-r/2.5)"
    ),
    "T-55": UnitSpec(
        name="T-55",
        team="red",
        unit_type=UnitType.TANK,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.7, 2.0),
        pk_model="exp(-r/2.0)"
    ),
    "T-62": UnitSpec(
        name="T-62",
        team="red",
        unit_type=UnitType.TANK,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.68, 2.0),
        pk_model="exp(-r/2.0)"
    ),
    "60mm_Mortar": UnitSpec(
        name="60mm_Mortar",
        team="blue",
        unit_type=UnitType.MORTAR, 
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.6, 2.0),
        pk_model="exp(-r/2.0)"
    ),
    "105mm_Howitzer": UnitSpec(
        name="105mm_Howitzer",
        team="blue",
        unit_type=UnitType.HOWITZER,
        range_km=11.0,
        ph_func=exp_decay(11.0, 0.8, 11.0),
        pk_model="exp(-r/11.0)"
    ),
    "122mm_SPG": UnitSpec(
        name="122mm_SPG",
        team="red",
        unit_type=UnitType.SPG,
        range_km=15.0,
        ph_func=exp_decay(10.0, 0.75, 10.0),
        pk_model="exp(-r/10.0)"
    ),
    "BM-21_MLRS": UnitSpec(
        name="BM-21_MLRS",
        team="red",
        unit_type=UnitType.MLRS,
        range_km=20.0,
        ph_func=exp_decay(20.0, 0.85, 20.0),
        pk_model="exp(-r/20.0)"
    ),
    "BGM-71_TOW": UnitSpec(
        name="BGM-71_TOW",
        team="blue",
        unit_type=UnitType.ATGM,
        range_km=3.75,
        ph_func=exp_decay(3.75, 0.9, 3.75),
        pk_model="exp(-r/3.75)"
    ),
    "9M14_Malyutka": UnitSpec(
        name="9M14_Malyutka",
        team="red",
        unit_type=UnitType.ATGM,
        range_km=3.0,
        ph_func=exp_decay(3.0, 0.85, 3.0),
        pk_model="exp(-r/3.0)"
    ),
    "106mm_M40_Recoilless_Rifle": UnitSpec(
        name="106mm_M40_Recoilless_Rifle",
        team="blue",
        unit_type=UnitType.RECOILLESS,
        range_km=1.2,
        ph_func=exp_decay(1.5, 0.7, 1.5),
        pk_model="exp(-r/1.5)"
    ),
    "107mm_B-11_Recoilless_Rifle": UnitSpec(
        name="107mm_B-11_Recoilless_Rifle",
        team="red",
        unit_type=UnitType.RECOILLESS,
        range_km=0.6,
        ph_func=exp_decay(1.5, 0.75, 1.5),
        pk_model="exp(-r/1.5)"
    ),
    "M72_LAW": UnitSpec(
        name="M72_LAW",
        team="blue",
        unit_type=UnitType.RPG,
        range_km=0.3,
        ph_func=exp_decay(0.2, 0.8, 0.2),
        pk_model="exp(-r/0.2)"
    ),
    "RPG-7": UnitSpec(
        name="RPG-7",
        team="red",
        unit_type=UnitType.RPG,
        range_km=0.5,
        ph_func=exp_decay(0.2, 0.75, 0.2),
        pk_model="exp(-r/0.2)"
    ),
    "Blue_Supply_Truck": UnitSpec(
        name="Blue_Supply_Truck",
        team="blue",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_model="exp(-r/0.1)"
    ),
    "Red_Supply_Truck": UnitSpec(
        name="Red Supply_Truck",
        team="red",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_model="exp(-r/0.1)"
    ),
}


class Coord: # Coordinate class to store x, y, z coordinates
    def __init__(self, x=0, y=0, z=0):
        self.x=x
        self.y=y
        self.z=z

    def next_coord(self, velocity, time):
        # Update the coordinates based on velocity and time
        self.x += velocity.x * time
        self.y += velocity.y * time
        self.z += velocity.z * time


class Velocity: # Velocity class to store velocity information
    def __init__(self, x=0, y=0, z=0):
        self.x=x
        self.y=y
        self.z=z

class Map: # Map class to store map information
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.zeros((width, height))

    # def add_obstacle(self, x, y):
    #     if 0 <= x < self.width and 0 <= y < self.height:
    #         self.grid[x][y] = 1  # Mark as obstacle

    # def is_obstacle(self, x, y):
    #     return self.grid[x][y] == 1
    
    def get_terrain(self, x, y): # Get terrain type at (x, y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

class History: # Store history of troop actions and troop status
    def __init__(self, time):
        self.current_time = time
        self.battle_log=[]
        self.status_data = {
            "time": [], 
            }

    def update_time(self, time): # update current time
        if time > self.current_time:
            self.current_time = time
        else:
            raise ValueError("Time cannot be set to a past value.")
        self.current_time = time

    def add_to_battle_log(self,team,type_,shooter,target,fire_time,result): # add to battle log
        self.battle_log.append([self.current_time,team,type_,shooter,target,fire_time,result])
    
    def add_to_status_data(self,team,type_,shooter,target,fire_time,result): # add to status data
        self.status_data["time"].append(self.current_time)
        if team not in self.status_data:
            self.status_data[team] = {}
        if type_ not in self.status_data[team]:
            self.status_data[team][type_] = {}
        if shooter not in self.status_data[team][type_]:
            self.status_data[team][type_][shooter] = {}
        if target not in self.status_data[team][type_][shooter]:
            self.status_data[team][type_][shooter][target] = {}
        if fire_time not in self.status_data[team][type_][shooter][target]:
            self.status_data[team][type_][shooter][target][fire_time] = result

    def get_battle_log(self): # return battle log
        return self.battle_log  
    
    def get_status_data(self): # return status data
        return self.status_data

    def save_battle_log(self, filename): # save battle log to file
        with open(filename, 'w') as f:
            for entry in self.battle_log:
                f.write(','.join(map(str, entry)) + '\n')
    
    def save_status_data(self, filename): # save status data to file
        with open(filename, 'w') as f:
            for entry in self.status_data:
                f.write(','.join(map(str, entry)) + '\n')

class Troop: # Troop class to store troop information and actions
    # Static variables to keep track of troop IDs
    counter = {}

    def __init__(self, unit_name, fire_time_func, target_delay_func, coord):
        spec = UNIT_SPECS[unit_name]
        self.spec = spec
        self.team = spec.team
        self.type = spec.unit_type
        self.name = spec.name
        self.range_km = spec.range_km
        self.ph_func = spec.ph_func
        self.pk_model = spec.pk_model

        self.fire_time_func = fire_time_func
        self.target_delay_func = target_delay_func
        self.id = self.assign_id()
        self.next_fire_time = fire_time_func()
        self.target = None
        self.alive = True
        self.coord = coord # Coordinate object to store (x, y, z) coordinates
        self.velocity = Velocity()  # Placeholder for velocity (x, y, z)
        self.status = UnitStatus.ALIVE  # Placeholder for unit status

    def assign_id(self):
        key = f"{self.team}_{self.type.value}"
        if key not in Troop.counter:
            Troop.counter[key] = 1
        label = f"{self.team[0].upper()}{self.type.value[:2].upper()}{Troop.counter[key]}"
        Troop.counter[key] += 1
        return label
    
    def update_coord(self, new_coord): # Update coordinates
        self.coord = new_coord
    def update_velocity(self, new_velocity): # Update velocity
        self.velocity = new_velocity

    def assign_target(self, current_time, enemy_list): #TODO: Implement target assignment logic
        if enemy_list:
            self.target = np.random.choice(enemy_list)
            if self.type == "anti_tank":
                non_anti_tanks = [e for e in enemy_list if e.type != "anti_tank"]
                if non_anti_tanks:
                    self.target = np.random.choice(non_anti_tanks)
                    self.next_fire_time = (
                        current_time + self.target_delay_func()
                    )
                else:
                    self.next_fire_time = float('inf')  # Set fire time to infinity (never fire)
            elif self.type == "tank":
                self.next_fire_time = current_time + self.target_delay_func()
        else:
            self.target = None
            self.next_fire_time = float('inf')
            print("----------------------should not happen----------------------")

    def fire(self, current_time, enemy_list, prob_list):
        if not self.alive:
            return

        if self.target not in enemy_list or self.target is None:
            self.assign_target(enemy_list)
            return

        result = "miss"
        if self.type == "tank":
            if self.target.type == "tank" and np.random.rand() < (
                blue_tank_red_tank if self.team == "blue" else red_tank_blue_tank
            ):
                self.target.alive = False
                result = "hit"
            elif self.target.type == "anti_tank" and np.random.rand() < (
                blue_tank_red_anti_tank
                if self.team == "blue"
                else red_tank_blue_anti_tank
            ):
                self.target.alive = False
                result = "hit"
        elif self.type == "anti_tank":
            if self.target.type == "anti_tank": print("Problem firing at a non-tank target")
            if np.random.rand() < (
                blue_anti_tank_red_tank
                if self.team == "blue"
                else red_anti_tank_blue_tank
            ):
                self.target.alive = False
                result = "hit"

        # history.append(
        #     [
        #         round(current_time, 2),
        #         self.team,
        #         self.type,
        #         self.id,
        #         self.target.id,
        #         round(self.next_fire_time, 2),
        #         result,
        #     ]
        # )
        if result == "hit":
            self.assign_target(enemy_list)
        else:
            self.next_fire_time = current_time + self.fire_time_func()


def assign_target_all(troop_list): #TODO: Implement target assignment logic for all troops
    for troop in troop_list:
        enemies = [
            e for e in troop_list if troop.team != e.team and e.alive
        ]
        troop.assign_target(enemies)

def terminate(troop_list):
    blue_tanks = [t for t in troop_list if t.type == "tank" and t.team == "blue"]
    red_tanks = [t for t in troop_list if t.type == "tank" and t.team == "red"]

    if blue_tanks and red_tanks:
        return False

def generate_troop_list(troop_list, unit_name, fire_time_func, target_delay_func, num_units):
    for _ in range(num_units):
        troop = Troop(
            unit_name=unit_name,
            fire_time_func=lambda: fire_time_func,
            target_delay_func=lambda: target_delay_func,
            coord=Coord()
        )
        troop_list.append(troop)

def generate_all_troops():
    troop_list = []

    # 기본 함수 예시 (나중에 유닛별로 다르게 설정 가능)
    default_fire_time_func = lambda: 0  # 예: 최초 발사까지 시간
    default_target_delay_func = lambda: 0  # 예: 목표 식별 시간

    for category in UnitComposition:
        unit_group = category.value

        # BLUE 진영 유닛 생성
        for unit_name, count in unit_group.blue.items():
            generate_troop_list(
                troop_list,
                unit_name=unit_name,
                fire_time_func=default_fire_time_func(),
                target_delay_func=default_target_delay_func(),
                num_units=count
            )

        # RED 진영 유닛 생성
        for unit_name, count in unit_group.red.items():
            generate_troop_list(
                troop_list,
                unit_name=unit_name,
                fire_time_func=default_fire_time_func(),
                target_delay_func=default_target_delay_func(),
                num_units=count
            )

    return troop_list


def main():

    troop_list = generate_all_troops()



    troop_status = []
    time_history = {
        "time": [],
        "blue_tanks": [],
        "blue_anti_tanks": [],
        "red_tanks": [],
        "red_anti_tanks": [],
    }

    # Create initial forces
    blue_forces = [
        Troop(
            "blue",
            "tank",
            lambda: triangular_distribution(M_blue_tank, C_blue_tank),
            lambda: uniform_distribution(a_blue_tank, b_blue_tank),
        )
        for _ in range(blue_tanks)
    ] + [
        Troop(
            "blue",
            "anti_tank",
            lambda: normal_distribution(mean_blue_anti_tank, stddev_blue_anti_tank),
            lambda: normal_distribution(mean_blue_anti_tank, stddev_blue_anti_tank),
        )
        for _ in range(blue_anti_tanks)
    ]
    red_forces = [
        Troop(
            "red",
            "tank",
            lambda: triangular_distribution(M_red_tank, C_red_tank),
            lambda: uniform_distribution(a_red_tank, b_red_tank),
        )
        for _ in range(red_tanks)
    ] + [
        Troop(
            "red",
            "anti_tank",
            lambda: normal_distribution(mean_red_anti_tank, stddev_red_anti_tank),
            lambda: normal_distribution(mean_red_anti_tank, stddev_red_anti_tank),
        )
        for _ in range(red_anti_tanks)
    ]

    all_forces = blue_forces + red_forces
    current_time = 0.0
    history = History(current_time)

    assign_target_all(all_forces)

    while True:
        history.update_time(current_time)
        # history.add_to_history(
        #     "blue",
        #     "tank",
        #     "shooter",
        #     "target",
        #     "fire_time",
        #     "result"
        # )
        if terminate(all_forces):
            break
        
        current_time +=0.01
        living_forces = [f for f in all_forces if f.alive]
        next_battle_time = min(f.next_fire_time for f in living_forces)

        if current_time == next_battle_time


        # print(current_time)
        # row = [round(current_time, 2)]
        # for troop in all_forces:
        #     row.extend(
        #         [
        #             troop.alive,
        #             troop.target.id if troop.target else None,
        #             round(troop.next_fire_time, 2) if troop.alive else None,
        #         ]
        #     )
        # troop_status.append(row)

        # # End if only anti-tanks remain
        # if all(t.type == "anti_tank" for t in blue_forces if t.alive) and all(
        #     t.type == "anti_tank" for t in red_forces if t.alive
        # ):
        #     break

        

        for troop in living_forces:
            if troop.next_fire_time <= current_time:
                enemies = [
                    e
                    for e in (red_forces if troop.team == "blue" else blue_forces)
                    if e.alive
                ]
                troop.fire(enemies)

        # time_history["time"].append(current_time)
        # time_history["blue_tanks"].append(
        #     sum(1 for t in blue_forces if t.alive and t.type == "tank")
        # )
        # time_history["blue_anti_tanks"].append(
        #     sum(1 for t in blue_forces if t.alive and t.type == "anti_tank")
        # )
        # time_history["red_tanks"].append(
        #     sum(1 for t in red_forces if t.alive and t.type == "tank")
        # )
        # time_history["red_anti_tanks"].append(
        #     sum(1 for t in red_forces if t.alive and t.type == "anti_tank")
        # )

if __name__ == "__main__":
    max_time = 2880.0
    main()