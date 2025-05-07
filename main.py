import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from enum import Enum
from collections import namedtuple
import math

MAX_TIME = 2880.0 # 최대 시뮬레이션 시간 (분 단위)
TIME_STEP = 0.01 # 시뮬레이션 시간 간격 (분 단위)

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

class hitState(Enum):
    HIT = "hit" # 명중
    MISS = "miss" # 빗나감
    DESTROYED = "destroyed" # 파괴됨
    DAMAGED = "damaged" # 손상됨
    OUT_OF_AMMO = "out_of_ammo" # 탄약 없음
    OUT_OF_RANGE = "out_of_range" # 사거리 초과
    MOVING = "moving" # 이동중
    STATIONARY = "stationary" # 정지중
    RELOADING = "reloading" # 재장전중
    SPOTTED = "spotted" # 발견됨
    UNSPOTTED = "unspotted" # 발견되지 않음

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
    def __init__(self, name, team, unit_type, range_km, ph_func, pk_func, target_delay_func, fire_time_func):
        self.name = name
        self.team = team  # "blue" or "red"
        self.unit_type = unit_type  # UnitType Enum
        self.range_km = range_km
        self.ph_func = ph_func  # A function that returns hit probability
        self.pk_func = pk_func  # Description or function of kill model
        self.target_delay_func = target_delay_func
        self.fire_time_func = fire_time_func


UNIT_SPECS = {  #TODO: unit ph_func, pk_func 추가
    "Sho't_Kal": UnitSpec(
        name="Sho't_Kal",
        team="blue",
        unit_type=UnitType.TANK,
        range_km=2.5,
        ph_func=exp_decay(2.5, 0.75, 2.5),
        pk_func="exp(-r/2.5)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "T-55": UnitSpec(
        name="T-55",
        team="red",
        unit_type=UnitType.TANK,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.7, 2.0),
        pk_func="exp(-r/2.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "T-62": UnitSpec(
        name="T-62",
        team="red",
        unit_type=UnitType.TANK,
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.68, 2.0),
        pk_func="exp(-r/2.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "60mm_Mortar": UnitSpec(
        name="60mm_Mortar",
        team="blue",
        unit_type=UnitType.MORTAR, 
        range_km=2.0,
        ph_func=exp_decay(2.0, 0.6, 2.0),
        pk_func="exp(-r/2.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "105mm_Howitzer": UnitSpec(
        name="105mm_Howitzer",
        team="blue",
        unit_type=UnitType.HOWITZER,
        range_km=11.0,
        ph_func=exp_decay(11.0, 0.8, 11.0),
        pk_func="exp(-r/11.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "122mm_SPG": UnitSpec(
        name="122mm_SPG",
        team="red",
        unit_type=UnitType.SPG,
        range_km=15.0,
        ph_func=exp_decay(10.0, 0.75, 10.0),
        pk_func="exp(-r/10.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "BM-21_MLRS": UnitSpec(
        name="BM-21_MLRS",
        team="red",
        unit_type=UnitType.MLRS,
        range_km=20.0,
        ph_func=exp_decay(20.0, 0.85, 20.0),
        pk_func="exp(-r/20.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "BGM-71_TOW": UnitSpec(
        name="BGM-71_TOW",
        team="blue",
        unit_type=UnitType.ATGM,
        range_km=3.75,
        ph_func=exp_decay(3.75, 0.9, 3.75),
        pk_func="exp(-r/3.75)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "9M14_Malyutka": UnitSpec(
        name="9M14_Malyutka",
        team="red",
        unit_type=UnitType.ATGM,
        range_km=3.0,
        ph_func=exp_decay(3.0, 0.85, 3.0),
        pk_func="exp(-r/3.0)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "106mm_M40_Recoilless_Rifle": UnitSpec(
        name="106mm_M40_Recoilless_Rifle",
        team="blue",
        unit_type=UnitType.RECOILLESS,
        range_km=1.2,
        ph_func=exp_decay(1.5, 0.7, 1.5),
        pk_func="exp(-r/1.5)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "107mm_B-11_Recoilless_Rifle": UnitSpec(
        name="107mm_B-11_Recoilless_Rifle",
        team="red",
        unit_type=UnitType.RECOILLESS,
        range_km=0.6,
        ph_func=exp_decay(1.5, 0.75, 1.5),
        pk_func="exp(-r/1.5)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "M72_LAW": UnitSpec(
        name="M72_LAW",
        team="blue",
        unit_type=UnitType.RPG,
        range_km=0.3,
        ph_func=exp_decay(0.2, 0.8, 0.2),
        pk_func="exp(-r/0.2)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "RPG-7": UnitSpec(
        name="RPG-7",
        team="red",
        unit_type=UnitType.RPG,
        range_km=0.5,
        ph_func=exp_decay(0.2, 0.75, 0.2),
        pk_func="exp(-r/0.2)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "Blue_Supply_Truck": UnitSpec(
        name="Blue_Supply_Truck",
        team="blue",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_func="exp(-r/0.1)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
    ),
    "Red_Supply_Truck": UnitSpec(
        name="Red Supply_Truck",
        team="red",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_func="exp(-r/0.1)",
        target_delay_func=lambda: 0,
        fire_time_func=lambda: 0,
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



class Coord: # Coordinate class to store x, y, z coordinates
    def __init__(self, x=0, y=0, z=0):
        self.x=x
        self.y=y
        self.z=z

    def next_coord(self, velocity):
        # Update the coordinates based on velocity and time
        self.x += velocity.x * TIME_STEP
        self.y += velocity.y * TIME_STEP
        self.z += velocity.z * TIME_STEP

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

    def init_status_data(self, troop_list): # initialize status data
        for troop in troop_list:
            if f"{troop.id}_status" not in self.status_data:
                self.status_data[f"{troop.id}_status"] = {}
                self.status_data[f"{troop.id}_target"] = {}
                self.status_data[f"{troop.id}_fire_time"] = {}
    
    def add_to_battle_log(self,team,type_,shooter,target,fire_time,result): # add to battle log
        self.battle_log.append([self.current_time,team,type_,shooter,target,fire_time,result])
    
    def add_to_status_data(self, troop_list): # add to status data
        self.status_data["time"].append(self.current_time)
        for troop in troop_list:
            self.status_data[f"{troop.id}_status"].append(troop.status.value)
            self.status_data[f"{troop.id}_target"].append(troop.target.id if troop.target else None)
            self.status_data[f"{troop.id}_fire_time"].append(troop.next_fire_time if troop.alive else None)

    def get_battle_log(self): # return battle log
        return self.battle_log  
    
    def get_status_data(self): # return status data
        return self.status_data

    def save_battle_log(self, filename="battle_log.csv"): # save battle log to file
        columns = ["time", "team", "type", "shooter", "target", "fire_time", "result"]
        df = pd.DataFrame(self.battle_log, columns=columns)
        df.to_csv(filename, index=False)
        print("Battle log saved to battle_log.csv")
    
    def save_status_data(self, filename="status_data.csv"): # save status data to file
        df = pd.DataFrame(self.status_data)
        df.to_csv(filename, index=False)
        print("Status data saved to status_data.csv")

class Troop: # Troop class to store troop information and actions
    # Static variables to keep track of troop IDs
    counter = {}

    def __init__(self, unit_name, coord=Coord()):
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

        self.id = self.assign_id()
        self.next_fire_time = 0.0  # Initial fire time
        self.target = None
        self.alive = True
        self.coord = coord # Coordinate object to store (x, y, z) coordinates
        self.velocity = Velocity()  # Placeholder for velocity (x, y, z)
        self.status = UnitStatus.ALIVE  # Placeholder for unit status
        self.ammo = 100     # ammo level (0-100%)
        self.supply = 100 # supply level (0-100%)

    def assign_id(self):
        key = f"{self.team}_{self.type.value}"
        if key not in Troop.counter:
            Troop.counter[key] = 1
        label = f"{self.team[0].upper()}{self.type.value[:2].upper()}{Troop.counter[key]}"
        Troop.counter[key] += 1
        return label
    
    def update_coord(self): # Update coordinates
        self.coord = self.coord.next_coord(self.velocity)

    def update_velocity(self, new_velocity): # Update velocity
        self.velocity = new_velocity

    def get_distance(self, other_troop): # Calculate distance to another troop
        return math.sqrt(
            (self.coord.x - other_troop.coord.x) ** 2 +
            (self.coord.y - other_troop.coord.y) ** 2 +
            (self.coord.z - other_troop.coord.z) ** 2
        )
    
    def assign_target(self, current_time, enemy_list): #TODO: Implement target assignment logic
        if enemy_list:
            self.target = np.random.choice(enemy_list)
            if self.type == "anti_tank":
                non_anti_tanks = [e for e in enemy_list if e.type != "anti_tank"]
                if non_anti_tanks:
                    self.target = np.random.choice(non_anti_tanks)
                    self.next_fire_time = (
                        current_time + self.t_a()
                    )
                else:
                    self.next_fire_time = float('inf')  # Set fire time to infinity (never fire)
            elif self.type == "tank":
                self.next_fire_time = current_time + self.t_a()
        else:
            self.target = None
            self.next_fire_time = float('inf')
            print("----------------------should not happen----------------------")

    def fire(self, current_time, enemy_list): #TODO: Implement firing logic
        if not self.alive:
            return

        if self.target not in enemy_list or self.target is None:
            self.assign_target(enemy_list)
            return

        result = hitState.MISS
        rand_var = np.random.rand()
        ph = self.ph_func(self.get_distance(self.target))
        pk = self.pk_func(self.get_distance(self.target))

        # if self.type == "tank":
        #     pk_func = self.pk_func

        # elif self.type == "mortar":
        #     pk_func = self.pk_func

        # elif self.type == "howitzer":
        #     pk_func = self.pk_func

        # elif self.type == "spg":
        #     pk_func = self.pk_func

        # elif self.type == "mlrs":
        #     pk_func = self.pk_func

        # elif self.type == "atgm":
        #     pk_func = self.pk_func

        # elif self.type == "rpg":
        #     pk_func = self.pk_func

        # elif self.type == "recoilless":

        # elif self.type == "infantry_at":

        # elif self.type == "infantry":

        # elif self.type == "vehicle":
            # Vehicle-specific logic (if any)

        

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
            self.next_fire_time = current_time + self.t_f()


def assign_target_all(troop_list): #TODO: Implement target assignment logic for all troops
    for troop in troop_list:
        enemies = [
            e for e in troop_list if troop.team != e.team and e.alive
        ]
        troop.assign_target(enemies)

def terminate(troop_list, current_time):
    # Check if all troops are dead or if the time limit is reached
    if current_time >= MAX_TIME:
        return True

    for troop in troop_list:
        if troop.type==UnitType.TANK and troop.alive:
            return False
        if troop.type==UnitType.APC and troop.alive:
            return False
    return True

def generate_troop_list(troop_list, unit_name, num_units):
    for _ in range(num_units):
        troop = Troop(
            unit_name=unit_name,
            coord=Coord()
        )
        troop_list.append(troop)

def generate_all_troops():
    troop_list = []
    for category in UnitComposition:
        unit_group = category.value

        # BLUE 진영 유닛 생성
        for unit_name, count in unit_group.blue.items():
            generate_troop_list(
                troop_list,
                unit_name=unit_name,
                num_units=count
            )

        # RED 진영 유닛 생성
        for unit_name, count in unit_group.red.items():
            generate_troop_list(
                troop_list,
                unit_name=unit_name,
                num_units=count
            )

    return troop_list

def update_troop_location(troop_list, map): #TODO: Implement troop out of bounds check logic
    for troop in troop_list:
        if troop.alive:
            # Update the troop's coordinates based on its velocity and time
            troop.update_coord()
            # Check if the troop is within the map boundaries
            if not (0 <= troop.coord.x < map.width and 0 <= troop.coord.y < map.height):
                troop.alive = False  # Mark as dead if out of bounds

def main():
    # Simulation parameters
    current_time = 0.0
    history = History(current_time=current_time)
    battle_map = Map(100, 100)  # Create a map of size 100x100

    troop_list = generate_all_troops()
    assign_target_all(troop_list)
    history.init_status_data(troop_list)

    while True:
        history.update_time(current_time)
        history.add_to_status_data(troop_list)

        if terminate(troop_list=troop_list, current_time=current_time):
            history.save_battle_log()
            history.save_status_data()
            print("Simulation terminated.")
            break
        
        current_time +=TIME_STEP
        living_troops = [f for f in troop_list if f.alive]
        update_troop_location(living_troops, map=battle_map)
        next_battle_time = min(f.next_fire_time for f in living_troops)

        if current_time == next_battle_time:
            for troop in living_troops: #TODO: iterate randomly
                if troop.next_fire_time <= current_time:
                    enemies = [
                        e for e in troop_list if troop.team != e.team and e.alive
                    ]
                    troop.fire(current_time, enemies)


if __name__ == "__main__":
    main()