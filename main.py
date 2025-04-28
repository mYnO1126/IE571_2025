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


# Initialize troop status and targeting
class Troop:
    counter = {"blue_tank": 1, "blue_anti": 1, "red_tank": 1, "red_anti": 1}

    def __init__(self, team, type_, fire_time_func, target_delay_func):
        self.team = team
        self.type = type_
        self.fire_time_func = fire_time_func
        self.target_delay_func = target_delay_func
        self.id = self.assign_id()
        self.next_fire_time = fire_time_func()
        self.target = None
        self.alive = True

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

    def assign_target(self, enemy_list):
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

    def fire(self, enemy_list):
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

        history.append(
            [
                round(current_time, 2),
                self.team,
                self.type,
                self.id,
                self.target.id,
                round(self.next_fire_time, 2),
                result,
            ]
        )
        if result == "hit":
            self.assign_target(enemy_list)
        else:
            self.next_fire_time = current_time + self.fire_time_func()


def main():
    # Initialize forces
    blue_tanks = 20
    blue_anti_tanks = 13
    red_tanks = 30
    red_anti_tanks = 14

    # Hit probabilities
    blue_tank_red_anti_tank = 0.4
    blue_tank_red_tank = 0.3
    blue_anti_tank_red_tank = 0.1

    red_tank_blue_anti_tank = 0.3
    red_tank_blue_tank = 0.3
    red_anti_tank_blue_tank = 0.2

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
    current_time = 0

if __name__ == "__main__":
    main()