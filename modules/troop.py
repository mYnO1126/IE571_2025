# troop.py


import math
import numpy as np
import random
from .map import Coord, Velocity, Map, MAX_TIME, TIME_STEP
from .unit_definitions import UnitStatus, UnitType, UnitComposition, HitState, UNIT_SPECS, BLUE_HIT_PROB_BUFF, get_landing_data, AMMUNITION_DATABASE, AmmunitionInfo, SUPPLY_DATABASE


class Troop:  # Troop class to store troop information and actions
    # Static variables to keep track of troop IDs
    counter = {}

    def __init__(self, unit_name, coord=Coord(), affiliation: str = None, phase: str = None, fixed_dest=None):
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
        self.active   = False   # 이벤트상 “활성” 여부 (가시/표적 대상 등)
        self.can_move = False   # 이벤트상 “이동 허용” 여부

        self.id = self.assign_id()
        self.next_fire_time = 0.0  # Initial fire time
        self.target = None
        self.target_coord = None
        self.alive = True
        self.coord = coord  # Coordinate object to store (x, y, z) coordinates
        self.velocity = Velocity()  # Placeholder for velocity (x, y, z)
        self.status = UnitStatus.ALIVE  # Placeholder for unit status

        self.affiliation = affiliation
        self.phase = phase
        self.fixed_dest = fixed_dest  # Fixed dest, Coordinate object to store (x, y, z) coordinates

        self.ammo = 100  # ammo level (0-100%)
        self.supply = 100  # supply level (0-100%)
        ammo_info = AMMUNITION_DATABASE.get(unit_name, AmmunitionInfo(0, 0, 0, 0))
        # 적재량
        self.main_ammo = float(ammo_info.main_ammo)
        self.secondary_ammo = float(ammo_info.secondary_ammo)

        # ▶ 분당 사용 속도 (= 하루 예상 사용량 ÷ 1440 분)
        self.main_rate  = ammo_info.daily_main_usage / 1440.0
        self.sec_rate   = ammo_info.daily_sec_usage  / 1440.0

        self.last_ammo_check = 0.0          # 마지막 소모 계산 시각
        self.ammo_restricted_until = 0.0    # 10 % 이하 → 5 분 금지용

        if self.type == UnitType.SUPPLY:
            self.supply_stock = {}  # 예: {"T-55": 129, "AK-47": 12000, ...}
            for k, v in SUPPLY_DATABASE.items():
                self.supply_stock[k] = float(v)

    def dead(self):
        del self  # Explicitly delete the object

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

        # 1) 기본 속도 km/h → km/min
        on_road = battle_map.is_road(self.coord.x, self.coord.y)
        base_speed = (
            self.spec.speed_road_kmh if on_road else self.spec.speed_offroad_kmh
        ) / 60

        # 2) 지형 가중치
        terrain_factor = battle_map.movement_factor(self.coord.x, self.coord.y)

        if not np.isfinite(terrain_factor):
            # impassable cell → 움직이지 않음 #TODO 방향을 돌려서 가도록 전환 필요.
            return Velocity(0,0,0)

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
        
        if dist < self.range_km:
            # 목표 지점이 사거리 이내면 멈춤
            return Velocity(0, 0, 0)
        
        ux, uy = dx / dist, dy / dist

        move = speed * TIME_STEP

        # move (km) → move_m (m)
        move_m  = move * 1000  
        
        # print(f"[{self.id}] move = {move_m:.1f} m/min ("f"{speed:.3f} km/min)")
        
        # move_m (m) → move_px (pixels), given 1 px = 10 m
        move_px = move_m / battle_map.resolution_m
    
        # 로그 출력
        # direction unit vector stays the same:
        ux, uy = dx/dist, dy/dist

        # now return pixel‐per‐step velocity instead of km‐per‐step
        # return Velocity(ux * move_px, uy * move_px, 0) # 방향 탐색 안하면 아래 코멘트 처리 후 여기서 그만하기.
        return Velocity(ux * move, uy * move, 0)

        # # 3) 후보 방향들(θ 범위 ±45°, 5° 간격)
        # thetas = np.deg2rad(np.linspace(-45, 45, 19))

        # best = None  # (cost, dir_x, dir_y)
        # for θ in thetas:
        #     cos_t, sin_t = math.cos(θ), math.sin(θ)
        #     rx = ux * cos_t - uy * sin_t
        #     ry = ux * sin_t + uy * cos_t
            
        #     # 정규화
        #     rnorm = math.hypot(rx, ry)
        #     if rnorm == 0: continue
        #     rx, ry = rx/rnorm, ry/rnorm

        #     # 한 픽셀만 가봤을 때의 좌표
        #     test_x = self.coord.x + rx * 1.0
        #     test_y = self.coord.y + ry * 1.0
        #     cost = battle_map.movement_factor(test_x, test_y)

        #     # impassable 은 아주 높은 코스트로 취급
        #     if not np.isfinite(cost) or cost <= 0:
        #         continue

        #     if best is None or cost < best[0]:
        #         best = (cost, rx, ry)

        # # 4) 최종 방향 선택
        # if best:
        #     _, fx, fy = best
        #     return Velocity(fx * move_px, fy * move_px, 0)

        # # 후보가 하나도 유효하지 않으면 멈춤
        # return Velocity(0,0,0)


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
        
        # ▶ 경과 시간만큼 탄약을 자동 소모
    def consume_ammo(self, current_time):
        dt = current_time - self.last_ammo_check
        if dt <= 0:
            return

        # 저장해두고
        prev_main = int(self.main_ammo)
        prev_sec = int(self.secondary_ammo)

        # 감소
        self.main_ammo = max(0.0, self.main_ammo - self.main_rate * dt)
        self.secondary_ammo = max(0.0, self.secondary_ammo - self.sec_rate * dt)

        # 현재 정수 단위
        curr_main = int(self.main_ammo)
        curr_sec = int(self.secondary_ammo)

        # 정수 단위 탄약 감소 여부 저장
        self.main_ammo_int_changed = (curr_main < prev_main)
        self.secondary_ammo_int_changed = (curr_sec < prev_sec)

        self.last_ammo_check = current_time

    def fire(self, current_time, enemy_list, history):  # TODO: Implement firing logic
        #TODO 에러 발생
        # # ▶ 경과 분만큼 탄약 소모
        # self.consume_ammo(current_time)

        # total_ammo = self.main_ammo + self.secondary_ammo

        # # 10 % 이하 → 5 분 금지
        # if total_ammo <= 0.1 * (
        #      AMMUNITION_DATABASE[self.name].main_ammo +
        #      AMMUNITION_DATABASE[self.name].secondary_ammo):
        #     self.ammo_restricted_until = current_time + 5.0

        # # ▶ 탄약 없거나 제한 시간이면 발사 불가
        # if total_ammo <= 0 or current_time < self.ammo_restricted_until:
        #     self.next_fire_time = round(current_time + 1.0, 2)  # 1 분 뒤 재시도
        #     return

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
        print("Result", result, self.team, self.type, self.name)
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
        
        #TODO: 에러 발생
        # if not self.main_ammo_int_changed and not self.secondary_ammo_int_changed:
        #     self.next_fire_time = round(current_time + 1.0, 2)
        #     return
        
    def resupply(self, current_time):
        supply_trucks = [t for t in self.troops
                        if t.alive and t.type == UnitType.SUPPLY]

        for supply in supply_trucks:
            for unit in self.troops:
                if not unit.alive or unit.team != supply.team or unit.type == UnitType.SUPPLY:
                    continue
                if supply.get_distance(unit) < 0.3:
                    unit_name = unit.name
                    if unit_name not in SUPPLY_DATABASE or unit_name not in supply.supply_stock:
                        continue

                    max_ammo = AMMUNITION_DATABASE[unit_name].main_ammo + AMMUNITION_DATABASE[unit_name].secondary_ammo
                    curr_ammo = unit.main_ammo + unit.secondary_ammo
                    missing_ammo = max(0.0, max_ammo - curr_ammo)

                    available = supply.supply_stock[unit_name]
                    given = min(missing_ammo, available)

                    if given <= 0:
                        continue

                    # 보급 수행
                    unit_total = unit.main_ammo + unit.secondary_ammo
                    ratio_main = unit.main_ammo / unit_total if unit_total > 0 else 1.0

                    unit.main_ammo += given * ratio_main
                    unit.secondary_ammo += given * (1 - ratio_main)

                    # 보급 트럭 잔여량 감소
                    supply.supply_stock[unit_name] -= given

                    # 사격 제한 시간 갱신
                    unit.ammo_restricted_until = current_time + 5.0


def update_troop_location(troop_list, battle_map, current_time):
    for troop in troop_list:
        if not troop.alive:
            continue
        
        # “active” 플래그가 꺼져 있으면 아예 움직이지도, 표적 탐색도 하지 않음
        if not troop.active or not troop.can_move:
            troop.update_velocity(Velocity(0,0,0))
            continue

        # fixed_dest 가 있으면 그쪽으로, 없으면 (target or 자기 위치)
        if troop.fixed_dest:
            dest = troop.fixed_dest
            # print(troop.fixed_dest)
        else:
            dest = troop.target.coord if troop.target else troop.coord
            # print(dest)

        # dest = troop.target.coord if troop.target else troop.coord
        v = troop.compute_velocity(dest, battle_map, current_time)
        troop.update_velocity(v)
        troop.update_coord()

        # z 값을 DEM 에서 직접 가져오기
        xi, yi = int(troop.coord.x), int(troop.coord.y)
        if 0 <= yi < battle_map.height and 0 <= xi < battle_map.width:
            troop.coord.z = battle_map.dem_arr[yi, xi]

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