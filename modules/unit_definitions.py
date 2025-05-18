# unit_definitions.py


from enum import Enum
from collections import namedtuple
import numpy as np
import math


# MAX_TIME = 100.0 # 최대 시뮬레이션 시간 (분 단위) #for testingfrom typing import List, Tuple
MAX_TIME = 2880.0  # 최대 시뮬레이션 시간 (분 단위) #TODO: 복구 요망
# TIME_STEP = 0.01 # 시뮬레이션 시간 간격 (분 단위)
TIME_STEP = 1.0
BLUE_HIT_PROB_BUFF = 0.8  # BLUE 진영의 명중 확률 버프


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
    return lambda p: (
        HitState.CKILL
        if p < 0.7 * coeff
        else (HitState.MKILL if p < 0.9 * coeff else HitState.FKILL)
    )


def simple_pk_func(pk):
    return lambda p: HitState.CKILL if p < pk else HitState.MISS


class UnitType(Enum):
    TANK = "tank"  # 전차
    MORTAR = "mortar"  # 박격포
    HOWITZER = "howitzer"  # 견인포
    SPG = "spg"  # 자주포
    MLRS = "mlrs"  # 다연장로켓포
    ATGM = "atgm"  # 대전차미사일
    RPG = "rpg"  # 휴대용 대전차 로켓포
    RECOILLESS = "recoilless"  # 무반동포
    INFANTRY_AT = "infantry_at"  # 보병 대전차
    INFANTRY = "infantry"  # 보병
    SUPPLY = "supply"  # 보급차량
    VEHICLE = "vehicle"  # 차량
    APC = "apc"  # 장갑차
    DIR_FIRE_UNIT = ["tank", "atgm", "infantry_at"]
    INDIRECT_FIRE_UNIT = ["mortar", "howitzer", "spg", "mlrs"]
    ANTI_TANK = ["atgm", "recoilless", "rpg"]


class UnitStatus(Enum):
    ALIVE = "alive"  # 살아있음
    DESTROYED = "destroyed"  # 파괴됨
    DAMAGED_MOBILITY = "mobility_damaged"  # 기동불능
    DAMAGED_FIREPOWER = "firepower_damaged"  # 화력불능
    OUT_OF_RANGE = "out_of_range"  # 사거리 초과
    MOVING = "moving"  # 이동중
    STATIONARY = "stationary"  # 정지중
    RELOADING = "reloading"  # 재장전중
    SPOTTED = "spotted"  # 발견됨
    UNSPOTTED = "unspotted"  # 발견되지 않음
    HIDDEN = "hidden"  # 은폐됨
    UNCOVERED = "uncovered"  # 은폐되지 않음
    ENGAGED = "engaged"  # 교전중
    UNENGAGED = "unengaged"  # 비교전중
    MOVEMENT_ORDER = "movement_order"  # 이동명령
    ENGAGEMENT_ORDER = "engagement_order"  # 교전명령
    RELOAD_ORDER = "reload_order"  # 재장전명령
    SPOT_ORDER = "spot_order"  # 발견명령
    UNSPOT_ORDER = "unspot_order"  # 발견되지 않음 명령
    HIDE_ORDER = "hide_order"  # 은폐명령
    UNCOVER_ORDER = "uncover_order"  # 은폐되지 않음 명령


class AmmoStatus(Enum):
    FULL = "full"  # 완전
    LOW = "low"  # 부족
    EMPTY = "empty"  # 없음


class UnitAction(Enum):
    MOVE = "move"  # 이동
    FIRE = "fire"  # 발사
    SPOT = "spot"  # 발견
    UNSPOT = "unspot"  # 발견되지 않음
    HIDE = "hide"  # 은폐
    UNCOVER = "uncover"  # 은폐되지 않음
    RELOAD = "reload"  # 재장전
    ENGAGE = "engage"  # 교전
    UNENGAGE = "unengage"  # 비교전
    SUPPLY = "supply"  # 보급
    REPAIR = "repair"  # 수리


class HitState(Enum):
    CKILL = "catastrophic-kill"  # 완전파괴
    MKILL = "mobility-kill"  # 기동불능
    FKILL = "firepower-kill"  # 화력불능
    MISS = "miss"  # 명중하지 않음


# 유닛 세부 정보를 담을 구조체
UnitCategory = namedtuple("UnitCategory", ["blue", "red"])


class UnitComposition(Enum):
    TANK = UnitCategory(blue={"Sho't_Kal": 170}, red={"T-55": 300, "T-62": 200})

    AT_WEAPON = UnitCategory(
        blue={"BGM-71_TOW": 12, "106mm_M40_Recoilless_Rifle": 36, "M72_LAW": 12},
        red={"9M14_Malyutka": 54, "107mm_B-11_Recoilless_Rifle": 36, "RPG-7": 54},
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
    def __init__(
        self,
        name,
        team,
        unit_type,
        range_km,
        ph_func,
        pk_func,
        target_delay_func=constant_func(2.0),
        fire_time_func=constant_func(1.0),
        speed_road_kmh=1000,
        speed_offroad_kmh=1000,
    ):
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
        pk_func="exp(-r/2.0)",  # TODO
        speed_road_kmh=64,
        speed_offroad_kmh=np.random.randint(40, 45),
    ),
    "BMP-1": UnitSpec(
        name="BMP-1",
        team="red",
        unit_type=UnitType.APC,
        range_km=0.8,
        ph_func=constant_func(0.60),
        pk_func="exp(-r/2.0)",  # TODO
        speed_road_kmh=65,
        speed_offroad_kmh=45,
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
        speed_offroad_kmh=5,
    ),
    "보병여단3 + 기계화여단3": UnitSpec(
        name="보병여단3 + 기계화여단3",
        team="red",
        unit_type=UnitType.INFANTRY,
        range_km=0.3,
        ph_func=constant_func(0.2),
        pk_func="exp(-r/0.3)",
        speed_road_kmh=5,
        speed_offroad_kmh=5,
    ),
    "Blue_Supply_Truck": UnitSpec(
        name="Blue_Supply_Truck",
        team="blue",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_func="exp(-r/0.1)",
        speed_road_kmh=80,
        speed_offroad_kmh=40,
    ),
    "Red_Supply_Truck": UnitSpec(
        name="Red Supply_Truck",
        team="red",
        unit_type=UnitType.SUPPLY,
        range_km=0.0,
        ph_func=exp_decay(0.1, 0.6, 0.1),
        pk_func="exp(-r/0.1)",
        speed_road_kmh=80,
        speed_offroad_kmh=40,
    ),
}
