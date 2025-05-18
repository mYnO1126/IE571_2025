# troop.py


import math
import numpy as np
from .map import Coord, Velocity, Map
from .unit_definitions import UnitStatus, UnitType, HitState, UNIT_SPECS, TIME_STEP, BLUE_HIT_PROB_BUFF


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
        self.target_delay_func = spec.target_delay_func
        self.fire_time_func = spec.fire_time_func

        self.affiliation = affiliation

        self.id = self.assign_id()
        self.next_fire_time = 0.0  # Initial fire time
        self.target = None
        self.alive = True
        self.coord = coord  # Coordinate object to store (x, y, z) coordinates
        self.velocity = Velocity()  # Placeholder for velocity (x, y, z)
        self.status = UnitStatus.ALIVE  # Placeholder for unit status
        self.ammo = 100  # ammo level (0-100%)
        self.supply = 100  # supply level (0-100%)

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

        # ---- 역할별 전략: 유형별 타겟팅 로직 ----

    def filter_priority(self, cand_list):
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
        elif self.type in {
            UnitType.ATGM,
            UnitType.RPG,
            UnitType.RECOILLESS,
            UnitType.INFANTRY_AT,
        }:
            at_targets = [
                c for c in cand_list if c[0].type in {UnitType.TANK, UnitType.APC}
            ]
            return sorted(at_targets, key=lambda c: (c[2], c[1]))
        elif self.type in {
            UnitType.MORTAR,
            UnitType.HOWITZER,
            UnitType.SPG,
            UnitType.MLRS,
        }:
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
    ):  # TODO: Implement target assignment logic
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

    def compute_velocity(
        self, dest: Coord, battle_map: Map, current_time: float
    ) -> Velocity:
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
