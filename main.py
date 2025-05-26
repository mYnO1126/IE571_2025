# main.py


import numpy as np
import random
import signal
import sys
from modules.history import History
# from modules.map import Map, placement_zones, MAX_TIME, TIME_STEP, MAP_WIDTH, MAP_HEIGHT
from modules.map import Map, Coord, MAX_TIME, TIME_STEP, compute_all_positions # MAP_WIDTH, MAP_HEIGHT, 
from modules.placement import RED_PLACEMENT, BLUE_PLACEMENT
from modules.timeline import TimelineEvent, TIMELINE
from modules.troop import Troop, TroopList, generate_initial_troops, update_troop_location, terminate
from modules.unit_definitions import UnitType, UnitComposition
from modules.utils import initialize_folders


# 전역 변수로 접근 가능하게
terminate_flag = False

def create_from_positions(unit_positions):
    troops = []
    for team, zones in unit_positions.items():
        for zone_name, comps in zones.items():
            for unit_name, coords in comps.items():
                if unit_name not in UNIT_SPECS:
                    continue
                for x,y in coords:
                    t = Troop(unit_name, Coord(x,y,0), affiliation=zone_name)
                    troops.append(t)
    return troops

def handle_sigint(signum, frame):
    global terminate_flag
    print("\n[Ctrl+C] Interrupt received! Preparing to terminate gracefully...")
    terminate_flag = True


def main():
    # Simulation parameters
    random.seed(42)  # For reproducibility
    np.random.seed(42)  # For reproducibility

    global terminate_flag
    signal.signal(signal.SIGINT, handle_sigint)
    # Initialize simulation variables
    res_loc = initialize_folders()

    current_time = 0.0
    hist_record_time = 0.0
    history = History(time=current_time)
    # battle_map = Map(MAP_WIDTH, MAP_HEIGHT)  # Create a map of size 100x100
    battle_map = Map() #MAP_WIDTH, MAP_HEIGHT)  # Create a map of size 100x100

    # ← 1회만: 목표 지점(예: 적 사령부) 그리드 좌표 정의
    goal_coord = Coord(500, 550, 0)  
    goal_cell  = (int(goal_coord.y), int(goal_coord.x))
    battle_map.build_flow_field(goal_cell)

    timeline_index = 0

    # troop_list = generate_all_troops()
    # spawned_troops = generate_initial_troops(placement_zones = placement_zones)
    # troop_list = TroopList(spawned_troops)
    # # assign_target_all(current_time, troop_list)
    # history.init_status_data(troop_list)
    # spawned_troops = generate_initial_troops(placement_zones = placement_zones)
    red_unit_positions = compute_all_positions(RED_PLACEMENT, team = 'red', phase = 'P1')
    blue_unit_positions = compute_all_positions(BLUE_PLACEMENT, team = 'blue', phase = 'P1')
    red_spawned_troops = create_from_positions(red_unit_positions)
    blue_spawned_troops = create_from_positions(blue_unit_positions)
    
    troop_list = TroopList()
    troop_list.add_troop(red_spawned_troops)
    troop_list.add_troop(blue_spawned_troops)

    # assign_target_all(current_time, troop_list)
    history.init_status_data(troop_list)
    
    while True:
        if timeline_index < len(TIMELINE):
            event = TIMELINE[timeline_index]
            if current_time == event.time:
                print(f"[{event.time_str}] TIMELINE EVENT: {event.description}")
                timeline_index += 1

        if hist_record_time==1.0:
            history.add_to_status_data(troop_list)  
            hist_record_time = 0.0
            history.draw_troop_positions(troop_list.troops, current_time, save_dir=res_loc+"/frames")
            # history.draw_troop_positions(battle_map, troop_list.troops, current_time, save_dir=res_loc+"/frames")

        troop_list.remove_dead_troops()

        if terminate_flag or terminate(troop_list=troop_list, current_time=current_time):
            history.save_battle_log(res_loc)
            history.save_status_data(res_loc)
            print("Simulation terminated.")
            history.plot_team_strength_over_time(res_loc)
            break

        current_time = round(current_time + TIME_STEP, 2)
        hist_record_time = round(hist_record_time + TIME_STEP, 2)
        history.update_time(current_time)
        # print(f"Current time: {current_time:.2f} min")
        # livingtroops = [f for f in troop_list if f.alive]

        # update_troop_location(living_troops, map=battle_map)
        update_troop_location(troop_list.troops, battle_map, current_time)

        next_battle_time = troop_list.get_next_battle_time()
        # print(f"Current time: {current_time:.2f} min")
        # print(f"Next battle time: {next_battle_time:.2f} min")

        if current_time == next_battle_time:
            troop_list.fire(current_time, history)

if __name__ == "__main__":
    main()
