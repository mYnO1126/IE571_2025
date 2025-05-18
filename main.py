# main.py


import numpy as np
import random
import matplotlib.pyplot as plt
from typing import List, Tuple
from modules.history import History
from modules.map import Map, placement_zones
from modules.timeline import TimelineEvent, timeline
from modules.troop import Troop
from modules.unit_definitions import UnitType, UnitComposition, MAX_TIME, TIME_STEP
from modules.utils import initialize_folders


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
