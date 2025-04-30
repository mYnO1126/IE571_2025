import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


# Probability distributions for firing times
def triangular_distribution(M, C):
    return np.random.triangular(M - C, M, M + C)


def normal_distribution(mean, variance):
    return np.random.normal(mean, np.sqrt(variance))


def uniform_distribution(a, b):
    return np.random.uniform(a, b)

def constant_distribution(value):
    return value

unit_type = {
    "tank":1,
    "anti_tank":2,
    "apc":3,
    "artilary":4,
    "supply":5,
}

prob_list = {
    "blue_tank_red_anti_tank" : 0.4,
    "blue_tank_red_tank" : 0.3,
    "blue_anti_tank_red_tank" : 0.1,

    "red_tank_blue_anti_tank" : 0.3,
    "red_tank_blue_tank" : 0.3,
    "red_anti_tank_blue_tank" : 0.2,
}

# Hit probabilities
blue_tank_red_anti_tank = 0.4
blue_tank_red_tank = 0.3
blue_anti_tank_red_tank = 0.1

red_tank_blue_anti_tank = 0.3
red_tank_blue_tank = 0.3
red_anti_tank_blue_tank = 0.2

class Coord: # Coordinate class to store x, y, z coordinates
    def __init__(self, x,y,z):
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
    counter = {"blue_tank": 1, "blue_anti": 1, "red_tank": 1, "red_anti": 1}

    def __init__(self, team, type_, fire_time_func, target_delay_func, location):
        self.team = team
        self.type = type_
        self.fire_time_func = fire_time_func
        self.target_delay_func = target_delay_func
        self.id = self.assign_id()
        self.next_fire_time = fire_time_func()
        self.target = None
        self.alive = True
        self.location = location

    def assign_id(self):
        if self.team == "blue" and self.type == "tank":
            label = f"B{Troop.counter['blue_tank']}"
            Troop.counter["blue_tank"] += 1
        elif self.team == "blue":
            label = f"BA{Troop.counter['blue_anti']}"
            Troop.counter["blue_anti"] += 1
        elif self.team == "red" and self.type == "tank":
            label = f"R{Troop.counter['red_tank']}"
            Troop.counter["red_tank"] += 1
        else:
            label = f"RA{Troop.counter['red_anti']}"
            Troop.counter["red_anti"] += 1
        return label

    def assign_target(self, current_time, enemy_list):
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


def assign_target_all(troop_list):
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


def main():
    # Initialize forces
    blue_tanks = 20
    blue_anti_tanks = 13
    red_tanks = 30
    red_anti_tanks = 14

    # # Hit probabilities
    # blue_tank_red_anti_tank = 0.4
    # blue_tank_red_tank = 0.3
    # blue_anti_tank_red_tank = 0.1

    # red_tank_blue_anti_tank = 0.3
    # red_tank_blue_tank = 0.3
    # red_anti_tank_blue_tank = 0.2

    # Mode values and configuration for distributions
    M_blue_tank = 4
    C_blue_tank = 2
    M_red_tank = 6
    C_red_tank = 2
    mean_blue_anti_tank = 30
    stddev_blue_anti_tank = 16
    mean_red_anti_tank = 20
    stddev_red_anti_tank = 10

    a_blue_tank = 2
    b_blue_tank = 6
    a_red_tank = 3
    b_red_tank = 8

    history = []
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