# troop.py


import math
import numpy as np
import random
from .map import Coord, Velocity, Map, MAX_TIME, TIME_STEP
from .unit_definitions import UnitStatus, UnitType, UnitComposition, HitState, UNIT_SPECS, BLUE_HIT_PROB_BUFF, get_landing_data


class Troop:  # Troop class to store troop information and actions
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
        self.damage_func = spec.damage_func
        self.target_delay_func = spec.target_delay_func
        self.fire_time_func = spec.fire_time_func

        self.affiliation = affiliation

        self.id = self.assign_id()
        self.next_fire_time = 0.0  # Initial fire time
        self.target = None
        self.target_coord = None
        self.alive = True
        self.coord = coord  # Coordinate object to store (x, y, z) coordinates
        self.velocity = Velocity()  # Placeholder for velocity (x, y, z)
        self.status = UnitStatus.ALIVE  # Placeholder for unit status
        self.ammo = 100  # ammo level (0-100%)
        self.supply = 100  # supply level (0-100%)

    def dead(self):
        del self  # Explicitly delete the object

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
        label = (
            f"{self.team[0].upper()}_{self.type.value[:2].upper()}{Troop.counter[key]}"
        )
        Troop.counter[key] += 1
        return label

    def update_coord(self):  # Update coordinates
        self.coord.next_coord(self.velocity)

    def update_velocity(self, new_velocity):  # Update velocity
        self.velocity = new_velocity

    def get_distance(self, other_troop):  # Calculate distance to another troop
        return math.sqrt(
            (self.coord.x - other_troop.coord.x) ** 2
            + (self.coord.y - other_troop.coord.y) ** 2
            + (self.coord.z - other_troop.coord.z) ** 2
        )

    def get_t_a(self):
        return self.target_delay_func(0) if self.target else 0

    def get_t_f(self):
        return self.fire_time_func(0) if self.target else 0

    def compute_velocity(
        self, dest: Coord, battle_map: Map, current_time: float
    ) -> Velocity: # TODO: stop if in range, hour/minute check
        # 1) 기본 속도 km/h→km/min
        on_road = battle_map.is_road(self.coord.x, self.coord.y)
        base_speed = (
            self.spec.speed_road_kmh if on_road else self.spec.speed_offroad_kmh
        ) / 60

        # 2) 지형 가중치
        terrain_factor = battle_map.movement_factor(self.coord.x, self.coord.y)

        # 3) 낮/밤 가중치 (19:00–06:00 야간엔 50% 느려짐)
        hour = int((13 * 60 + 55 + current_time) // 60) % 24
        daynight = 1.0 if 6 <= hour < 19 else 1.5

        # 4) 실제 per-min 이동량
        speed = base_speed / terrain_factor / daynight

        # 5) 방향 단위 벡터
        dx, dy = dest.x - self.coord.x, dest.y - self.coord.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return Velocity(0, 0, 0)
        ux, uy = dx / dist, dy / dist

        move = speed * TIME_STEP
        return Velocity(ux * move, uy * move, 0)

    # ---- 역할별 전략: 유형별 타겟팅 로직 ----
    def filter_priority(self, cand_list): # TODO: unit type 간소화 가능
        if self.type == UnitType.TANK:
            return sorted(
                cand_list,
                key=lambda c: (
                    c[0].type != UnitType.TANK,
                    c[0].type != UnitType.ATGM,
                    c[0].type != UnitType.APC,
                    c[1],  # distance
                ),
            )
        elif self.type == UnitType.APC:
            return sorted(
                cand_list,
                key=lambda c: (
                    c[0].type != UnitType.INFANTRY,
                    c[1],
                ),
            )
        elif UnitType.is_anti_tank(self.type):
            at_targets = [
                c for c in cand_list if c[0].type in {UnitType.TANK, UnitType.APC}
            ]
            return sorted(at_targets, key=lambda c: (c[2], c[1]))
        elif UnitType.is_indirect_fire(self.type):
            return sorted(
                cand_list,
                key=lambda c: (
                    c[0].status != UnitStatus.STATIONARY,
                    c[1],
                ),
            )
        elif self.type == UnitType.INFANTRY:
            return sorted(
                cand_list,
                key=lambda c: (
                    c[0].type != UnitType.INFANTRY,
                    c[1],
                ),
            )
        elif self.type == UnitType.SUPPLY:
            self.target = None
            self.next_fire_time = float("inf")
            return
        else:
            return sorted(cand_list, key=lambda c: (c[2], c[1]))

    def assign_target(
        self, current_time, enemy_list
    ):  # TODO: Implement target assignment logic, indirect fire logic
        # 밤 시간대: 19:00 ~ 06:00
        is_night = 360 <= current_time % 1440 <= 1080

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
                candidates.append((e, distance, 1))

            if not candidates:
                self.target = None
                self.next_fire_time = float("inf")
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
            self.next_fire_time = float("inf")
            # print("no more enemy left")
            return

    def fire(self, current_time, enemy_list, history):  # TODO: Implement firing logic
        if not self.alive:
            return

        if self.target.alive == False or self.target is None:
            self.assign_target(current_time, enemy_list)
            return

        if self.status == UnitStatus.DAMAGED_FIREPOWER:
            self.next_fire_time = round(current_time + self.get_t_f(), 2)
            return

        distance = self.get_distance(self.target)
        if distance > self.range_km:  #TODO: 사거리 제한
            self.next_fire_time = round(current_time + self.get_t_f(), 2)
            return
        result = HitState.MISS
        hit_rand_var = np.random.rand()
        kill_rand_var = np.random.rand()

        if UnitType.is_indirect_fire(self.type):
            landing_x, landing_y, lethal_r = get_landing_data(self.name, self.target.coord, distance)
            landing_dist = math.sqrt(
                (self.target.coord.x - landing_x) ** 2
                + (self.target.coord.y - landing_y) ** 2
            )
            pk = self.damage_func(landing_dist, lethal_r)
            result = self.pk_func(kill_rand_var, pk)

        else:
            # if self.type in UnitType.DIR_FIRE_UNIT:
            ph = self.ph_func(self.get_distance(self.target))
            # 야간 명중률 보정 (19:00 ~ 06:00 = 360~1080분)
            if 360 <= current_time % 1440 <= 1080:
                ph *= 0.8  # 20% 감소

            if self.target.team == "blue":
                ph = ph * BLUE_HIT_PROB_BUFF
            if ph > hit_rand_var:
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


class TroopList:  # Troop list to manage all troops
    def __init__(self, troop_list):
        self.troops = []
        self.blue_troops = []
        self.red_troops = []
        self.troop_ids = []
        for troop in troop_list:
            self.troops.append(troop)
            if troop.id in self.troop_ids:
                print(f"[ERROR] Duplicate id: {troop.id}")
                continue
            else:
                self.troop_ids.append(troop.id)            
            if troop.team == "blue":
                self.blue_troops.append(troop)
            elif troop.team == "red":
                self.red_troops.append(troop)
        self.assign_targets(0.0)

    def remove_troop(self, troop: Troop):
        if troop in self.troops:
            self.troops.remove(troop)
            if troop.team == "blue":
                self.blue_troops.remove(troop)
            elif troop.team == "red":
                self.red_troops.remove(troop)

    def remove_dead_troops(self):
        for troop in self.troops:
            if not troop.alive:
                self.remove_troop(troop)
                troop.dead()

    def assign_targets(self, current_time):
        for troop in self.troops:
            if troop.alive:
                if troop.team == "blue":
                    troop.assign_target(current_time, self.red_troops)
                elif troop.team == "red":
                    troop.assign_target(current_time, self.blue_troops)

    def get_enemy_list(self, troop):
        if troop.team == "blue":
            return self.red_troops
        elif troop.team == "red":
            return self.blue_troops
        else:
            print(f"[ERROR] wrong team affiliation: {troop.team}")
            return None

    def get_next_battle_time(self):
        next_battle_time = float("inf")
        for troop in self.troops:
            if troop.alive:
                if troop.next_fire_time < next_battle_time:
                    next_battle_time = troop.next_fire_time
        return next_battle_time

    def shuffle_troops(self):
        random.shuffle(self.troops)
        random.shuffle(self.blue_troops)
        random.shuffle(self.red_troops)

    def fire(self, current_time, history):
        self.shuffle_troops()
        for troop in self.troops: 
            if troop.next_fire_time <= current_time:
                enemies = self.get_enemy_list(troop)
                troop.fire(current_time, enemies, history)


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


def update_troop_location(troop_list, battle_map, current_time):
    for troop in troop_list:
        if not troop.alive:
            continue
        dest = troop.target.coord if troop.target else troop.coord
        v = troop.compute_velocity(dest, battle_map, current_time)
        troop.update_velocity(v)
        troop.update_coord()
        if not (
            0 <= troop.coord.x < battle_map.width
            and 0 <= troop.coord.y < battle_map.height
        ):
            troop.alive = False


def terminate(troop_list:TroopList, current_time):
    # Check if all troops are dead or if the time limit is reached
    if current_time >= MAX_TIME:
        return True

    if not any(t.alive for t in troop_list.blue_troops) or not any(t.alive for t in troop_list.red_troops):
        return True

    for troop in troop_list.troops:
        if troop.type == UnitType.TANK and troop.alive:
            return False
        if troop.type == UnitType.APC and troop.alive:
            return False
    return True
