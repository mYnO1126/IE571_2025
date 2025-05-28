# main.py


import numpy as np
import random
import signal
import sys
from modules.history import History
# from modules.map import Map, placement_zones, MAX_TIME, TIME_STEP, MAP_WIDTH, MAP_HEIGHT
from modules.map import Map, Coord, MAX_TIME, TIME_STEP # MAP_WIDTH, MAP_HEIGHT, 
from modules.placement import PLACEMENT, grid_sample_no_overlap
from modules.timeline import TimelineEvent, TIMELINE
from modules.troop import Troop, TroopList, update_troop_location, terminate, UNIT_SPECS
from modules.unit_definitions import UnitType, UnitComposition
from modules.utils import initialize_folders


# 전역 변수로 접근 가능하게
terminate_flag = False

# simulation state
active_on   = set()   # 현재 “활성화” 된 (team,phase) 쌍
move_on     = set()   # 현재 “이동 허용” 된 (team,phase) 쌍

def create_from_positions(unit_positions):
    troops = []
    for team, affs in unit_positions.items():
        for affiliation, feat in affs.items():
            phase = feat['phase']
            dest  = feat.get('goals', None)
            # comp별로 리스트를 늘려서, locs와 1:1 매칭할 준비
            comp_list = []
            for comp, cnt in feat['comp'].items():
                comp_list += [comp] * cnt

            # comp_list[i] 와 feat['locs'][i] 를 짝지어 Troop 생성
            for comp, (x, y, z) in zip(comp_list, feat['locs']):
                t = Troop(comp, Coord(x, y, z), affiliation=affiliation, phase=phase,
                          fixed_dest=Coord(dest[0], dest[1], dest[2]) if dest else None)
                troops.append(t)
    return troops


def handle_sigint(signum, frame):
    global terminate_flag
    print("\n[Ctrl+C] Interrupt received! Preparing to terminate gracefully...")
    terminate_flag = True

# def handle_event(event, troop_list, battle_map):

#     return
#     # if event.type == "reinforcement":
#     #     # event.params에 증원 정보가 들어 있다고 가정
#     #     troop_list.add_troops(event.params)
#     # elif event.type == "fortify":
#     #     battle_map.build_defenses(event.params)

def handle_event(event, troop_list, battle_map):
    global active_on, move_on

    # # 1) 모든 부대 플래그 초기화
    # for t in troop_list.troops:
    #     t.active   = False
    #     t.can_move = False

    # 2) active_on 에 속하는 부대만 active=True
    for team, phase in getattr(event, 'active_on', []):
        for t in troop_list.troops:
            if t.team == team and t.phase == phase:
                t.active = True

    # 3) move_on 에 속하는 부대만 can_move=True
    for team, phase in getattr(event, 'move_on', []):
        for t in troop_list.troops:
            if t.team == team and t.phase == phase:
                t.can_move = True

    print(f">>> After event {event.description}:")
    # print("    active:",  [(t.id, t.team, t.phase) for t in troop_list.troops if t.active])
    # print("    can_move:",[(t.id, t.team, t.phase) for t in troop_list.troops if t.can_move])


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
    print("Map Size", battle_map.dem_arr.shape)

    timeline_index = 0

    # --- PLACEMENT 전체를 순회하며 locs 채우기 ---
    used = set()
    for team, affs in PLACEMENT.items():
        for affiliation, feat in affs.items():
            x_range, y_range = feat['loc']
            feat['locs'] = []

            # goal_loc 필드가 있으면 goals 리스트도 초기화
            has_goal = 'goal_loc' in feat
            if has_goal:
                gx_range, gy_range = feat['goal_loc']
                feat['goals'] = []

            for comp, cnt in feat['comp'].items():
                if comp == 'AK-47' or comp == 'RPG':
                    min_gap = 2
                else:
                    min_gap = 4
                coords = grid_sample_no_overlap(
                    x_range, y_range, cnt, 
                    min_gap=min_gap, used=used
                    )
                coords_xyz = [
                    (x, y, battle_map.dem_arr[y, x])
                    for x, y, _ in coords
                ]
                feat['locs'].extend(coords_xyz)

            # 2) goal_loc 이 정의되어 있을 때만 목적지 샘플링
            if has_goal:
                min_gap = 4
                goals = grid_sample_no_overlap(
                    gx_range, gy_range, cnt,
                    min_gap=min_gap, used=used
                )
                goals_xyz = [
                    (x, y, battle_map.dem_arr[y, x])
                    for x, y, _ in goals
                ]
                feat['goals'].extend(goals_xyz)

    # troop_list = generate_all_troops()
    # spawned_troops = generate_initial_troops(placement_zones = placement_zones)
    # troop_list = TroopList(spawned_troops)
    # assign_target_all(current_time, troop_list)
    # history.init_status_data(troop_list)

    spawned_troops = create_from_positions(PLACEMENT)
    troop_list = TroopList(troop_list = spawned_troops)

    # assign_target_all(current_time, troop_list)
    history.init_status_data(troop_list)

    while True:
        if timeline_index < len(TIMELINE):
            event = TIMELINE[timeline_index]
            if current_time == event.time:
                print(f"[{event.time_str}] TIMELINE EVENT: {event.description}")
                handle_event(event, troop_list, battle_map)
                timeline_index += 1

        if hist_record_time==1.0:
            history.add_to_status_data(troop_list)  
            hist_record_time = 0.0
            history.draw_troop_positions(battle_map, troop_list, current_time, save_dir=res_loc+"/frames")

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

        if next_battle_time <= current_time:
            troop_list.fire(current_time, history)

if __name__ == "__main__":
    main()
