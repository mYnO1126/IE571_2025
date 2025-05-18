# history.py

import pandas as pd
import matplotlib.pyplot as plt
from .unit_definitions import UnitType
from .troop import Troop, TroopList

class History:  # Store history of troop actions and troop status
    def __init__(self, time):
        self.current_time = time
        self.battle_log = []
        self.status_data = {
            "time": [],
        }

        self.visualization_data = {"time": [], "unit": [], "x": [], "y": [], "z": []}

    def update_time(self, time):  # update current time
        if time >= self.current_time:
            self.current_time = time
        else:
            raise ValueError("Time cannot be set to a past value.")
        self.current_time = time

    def init_status_data(self, troop_list: TroopList):  # initialize status data
        troops = troop_list.troops
        for troop in troops:
            if f"{troop.id}_status" not in self.status_data:
                self.status_data[f"{troop.id}_status"] = []
                self.status_data[f"{troop.id}_target"] = []
                self.status_data[f"{troop.id}_fire_time"] = []
        self.add_to_status_data(troop_list)

    def add_to_battle_log(
        self, type_, shooter, target, target_type, result
    ):  # add to battle log
        self.battle_log.append(
            [self.current_time, shooter, type_, target, target_type, result]
        )

    def add_to_status_data(self, troop_list: TroopList):  # add to status data
        troops = troop_list.troops
        troop_ids = troop_list.troop_ids

        self.status_data["time"].append(self.current_time)
        troop_dict = {t.id: t for t in troops}
        s_data = self.status_data

        for tid in troop_ids:
            status_key = s_data[f"{tid}_status"]
            target_key = s_data[f"{tid}_target"]
            fire_key = s_data[f"{tid}_fire_time"]

            troop = troop_dict.get(tid)
            if troop:
                status_key.append(troop.status.value)
                target_key.append(troop.target.id if troop.target else None)
                fire_key.append(troop.next_fire_time if troop.alive else None)
            else:
                status_key.append("destroyed")
                target_key.append(None)
                fire_key.append(None)

        for troop in troops:
            if troop.alive:
                self.visualization_data["time"].append(self.current_time)
                self.visualization_data["unit"].append(troop.id)
                self.visualization_data["x"].append(troop.coord.x)
                self.visualization_data["y"].append(troop.coord.y)
                self.visualization_data["z"].append(troop.coord.z)

    def get_battle_log(self):  # return battle log
        return self.battle_log

    def get_status_data(self):  # return status data
        return self.status_data

    def save_battle_log(self, foldername="res/res0"):  # save battle log to file
        columns = ["time", "shooter", "shooter_type", "target", "target_type", "result"]
        df = pd.DataFrame(self.battle_log, columns=columns)
        df.to_csv(foldername + "/battle_log.csv", index=False)
        print("Battle log saved to battle_log.csv")

    def save_status_data(self, foldername="res/res0"):  # save status data to file
        df = pd.DataFrame(self.status_data)
        df.to_csv(foldername + "/status_data.csv", index=False)
        print("Status data saved to status_data.csv")

        df_2 = pd.DataFrame(self.visualization_data)
        df_2.to_csv(foldername + "/visualization_data.csv", index=False)
        print("Visualization data saved to visualization_data.csv")

    def save_status_data_new(
        self, troop_list, filename="status_data.csv"
    ):  # save status data to file
        data = []
        for t_idx, time in enumerate(self.status_data["time"]):
            time_sec = round(time * 60, 2)  # Convert from minutes to seconds
            for troop in troop_list:
                if troop.id in self.status_data:
                    # Get current position
                    x = troop.coord.x
                    y = troop.coord.y
                    z = troop.coord.z
                    data.append([time_sec, troop.id, x, y, z])

        df = pd.DataFrame(data, columns=["time", "unit", "x", "y", "z"])
        df.to_csv(filename, index=False)
        print("Status data saved to status_data.csv")

    def draw_troop_positions(self, troop_list, current_time, save_dir="frames"):
        plt.figure(figsize=(8, 8))
        for troop in troop_list:
            if not troop.alive:
                continue
            color = "blue" if troop.team == "blue" else "red"
            marker = "o" if troop.type == UnitType.TANK else "s"
            plt.scatter(
                troop.coord.x,
                troop.coord.y,
                c=color,
                marker=marker,
                label=troop.id,
                alpha=0.7,
                s=30,
            )
        plt.title(f"Troop Positions at T={current_time:.0f} min")
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{save_dir}/frame_{int(current_time):05d}.png")
        plt.close()

    def plot_team_strength_over_time(self, foldername="res/res0"):
        df = pd.DataFrame(self.status_data)

        time_col = df["time"]
        blue_cols = [
            col for col in df.columns if "_status" in col and col.startswith("B")
        ]
        red_cols = [
            col for col in df.columns if "_status" in col and col.startswith("R")
        ]

        blue_alive = df[blue_cols].apply(
            lambda row: sum(status == "alive" for status in row), axis=1
        )
        red_alive = df[red_cols].apply(
            lambda row: sum(status == "alive" for status in row), axis=1
        )

        plt.figure(figsize=(10, 5))
        plt.plot(time_col, blue_alive, label="BLUE Troops Alive")
        plt.plot(time_col, red_alive, label="RED Troops Alive")
        plt.xlabel("Time (min)")
        plt.ylabel("Number of Troops Alive")
        plt.title("Team Strength Over Time")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(foldername + "/plot.png", dpi=300)  # ✅ 파일 저장
        plt.show()
        print(f"Graph saved as {foldername}/plot.png")
