# history.py
import matplotlib

matplotlib.use("Agg")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import matplotlib.patches as mpatches

from .unit_definitions import UnitType
from .troop import Troop, TroopList
import numpy as np
# from .map import MAP_WIDTH, MAP_HEIGHT

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

    def init_status_data(self, troop_list: TroopList, reference_altitude, height):  # initialize status data
        troops = troop_list.troops
        for troop in troops:
            if f"{troop.id}_status" not in self.status_data:
                self.status_data[f"{troop.id}_status"] = []
                self.status_data[f"{troop.id}_target"] = []
                self.status_data[f"{troop.id}_fire_time"] = []
        self.add_to_status_data(troop_list, reference_altitude, height)

    def add_to_battle_log(
        self, type_, shooter, target, target_type, result
    ):  # add to battle log
        self.battle_log.append(
            [self.current_time, shooter, type_, target, target_type, result]
        )

    def add_to_status_data(self, troop_list: TroopList, reference_altitude, height):  # add to status data
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
                self.visualization_data["x"].append(troop.coord.x) # x -> 가로축
                # self.visualization_data["y"].append(troop.coord.y)
                # self.visualization_data["z"].append(troop.coord.z) 
                self.visualization_data["y"].append(troop.coord.z - reference_altitude) # y -> 높이
                self.visualization_data["z"].append(height - troop.coord.y) # z -> 세로축

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
        self, troop_list, battle_map, filename="status_data.csv"
    ):  # save status data to file
        data = []
        for t_idx, time in enumerate(self.status_data["time"]):
            time_sec = round(time * 60, 2)  # Convert from minutes to seconds
            for troop in troop_list:
                if troop.id in self.status_data:
                    # Get current position
                    x = troop.coord.x # x -> 가로축
                    # y = troop.coord.y
                    # z = troop.coord.z
                    y = troop.coord.z - battle_map.reference_altitude # y -> 높이
                    z = battle_map.height - troop.coord.y # z -> 세로축
                    data.append([time_sec, troop.id, x, y, z])

        df = pd.DataFrame(data, columns=["time", "unit", "x", "y", "z"])
        df.to_csv(filename, index=False)
        print("Status data saved to status_data.csv")

    def draw_troop_positions(self, Map, troop_list: TroopList, current_time, save_dir="frames", 
                           show_attack_lines=True, show_ranges=True, show_paths=False):
        # plt.figure(figsize=(16, 8))

        # --- 입력 데이터 ---
        def binarize(mask):
            return (mask > 0).astype(int)

        dem_arr = Map.dem_arr
        road_mask = binarize(Map.road_mask)
        lake_mask = binarize(Map.lake_mask)
        wood_mask = binarize(Map.wood_mask)
        stream_mask = binarize(Map.stream_mask)

        H, W = dem_arr.shape
        road_mask = road_mask[:H, :W]
        lake_mask = lake_mask[:H, :W]
        wood_mask = wood_mask[:H, :W]
        stream_mask = stream_mask[:H, :W]

        # --- 컬러맵 정의 ---
        road_cmap = ListedColormap(['none', 'red'])
        lake_cmap = ListedColormap(['none', 'blue'])
        wood_cmap = ListedColormap(['none', 'green'])
        stream_cmap = ListedColormap(['none', 'purple'])

        # --- 시각화 ---
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(dem_arr, cmap="terrain", origin="upper", alpha = 0.2)

        ax.imshow(road_mask, cmap=road_cmap, alpha=0.6, origin="upper")
        ax.imshow(lake_mask, cmap=lake_cmap, alpha=0.5, origin="upper")
        ax.imshow(wood_mask, cmap=wood_cmap, alpha=0.5, origin="upper")
        ax.imshow(stream_mask, cmap=stream_cmap, alpha=0.5, origin="upper")
        # --- 지형 시각화 추가 ---

        # 🟢 1. 사거리 원 그리기 (공격선보다 먼저 그려서 뒤에 위치)
        if show_ranges:
            self._draw_weapon_ranges(ax, troop_list)

        # 🟢 2. 공격선 그리기
        if show_attack_lines:
            self._draw_attack_lines(ax, troop_list)

        # 🟢 3. 이동 경로 그리기 (선택사항)
        if show_paths:
            self._draw_movement_paths(ax, troop_list)

        # 🟢 4. 부대 위치 그리기 (맨 위에 표시)
        self._draw_troop_markers(ax, troop_list)
        for troop in troop_list.troops:
            if not troop.alive:
                continue
            color = "blue" if troop.team == "blue" else "red"
            color = "grey" if not troop.active else color
            marker = "o" if troop.type == UnitType.TANK else "s"
            ax.scatter(
                np.float32(troop.coord.x),
                np.float32(troop.coord.y),
                c=color,
                marker=marker,
                label=troop.id,
                alpha=0.7,
                s=10,
            )
        plt.title(f"Troop Positions at T={current_time:.0f} min")
        # plt.xlim(0, MAP_WIDTH)
        # plt.ylim(0, MAP_HEIGHT)
        # plt.xlabel("X")
        # plt.ylabel("Y")
        # plt.grid(True)
        # --- 설정 ---

        # ----지형 시각화 추가 ----
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.set_title(f"Tactical Situation Board - T={current_time:.0f}Min", fontsize=14, fontweight='bold')
        ax.set_xlabel("X (10m)")
        ax.set_ylabel("Y (10m)")
        ax.grid(True, alpha=0.3)

        # 범례 (지형용)
        legend_elements = [
            Patch(facecolor='red', edgecolor='r', label='Road'),
            Patch(facecolor='blue', edgecolor='b', label='Lake'),
            Patch(facecolor='green', edgecolor='g', label='River'),
            Patch(facecolor='purple', edgecolor='purple', label='Stream'),
            Patch(facecolor='blue', edgecolor='k', label='Blue Troop'),
            Patch(facecolor='red', edgecolor='k', label='Red Troop'),
            # 부대
            mpatches.Circle((0,0), 1, facecolor='blue', edgecolor='k', label='Blue'),
            mpatches.Circle((0,0), 1, facecolor='red', edgecolor='k', label='Red'),
            mpatches.Circle((0,0), 1, facecolor='grey', edgecolor='k', label='Inactive'),
            # 전술 요소
            plt.Line2D([0], [0], color='red', linewidth=2, alpha=0.7, label='FireLine'),
            mpatches.Circle((0,0), 1, facecolor='none', edgecolor='orange', 
                          alpha=0.3, label='AttackRange'),
        ]

        if show_paths:
            legend_elements.append(
                plt.Line2D([0], [0], color='cyan', linewidth=1, 
                          linestyle='--', alpha=0.6, label='Path')
            )

        ax.legend(handles=legend_elements, loc='lower right', bbox_to_anchor=(1.2, 0.0))
        # ----지형 시각화 추가 ----

        fig.tight_layout()
        plt.savefig(f"{save_dir}/frame_{int(current_time):05d}.png")
        plt.close()

    def _draw_attack_lines(self, ax, troop_list):
        """공격선 그리기"""
        for troop in troop_list:
            if not troop.alive or not troop.active:
                continue
            
            if troop.target and troop.target.alive:
                # 공격선 색상 결정
                line_color = 'darkred' if troop.team == 'red' else 'darkblue'
                
                # 무기 유형별 선 스타일
                if UnitType.is_indirect_fire(troop.type):
                    # 간접화력: 곡선 스타일
                    linestyle = ':'
                    linewidth = 1.5
                    alpha = 0.6
                elif UnitType.is_anti_tank(troop.type):
                    # 대전차: 굵은 실선
                    linestyle = '-'
                    linewidth = 2.5
                    alpha = 0.8
                elif troop.type == UnitType.TANK:
                    # 전차: 실선
                    linestyle = '-'
                    linewidth = 2.0
                    alpha = 0.7
                else:
                    # 기타: 얇은 실선
                    linestyle = '-'
                    linewidth = 1.0
                    alpha = 0.5

                # 공격선 그리기
                ax.plot([troop.coord.x, troop.target.coord.x],
                       [troop.coord.y, troop.target.coord.y],
                       color=line_color, linestyle=linestyle, 
                       linewidth=linewidth, alpha=alpha)
                
                # 🟢 화살표 추가 (공격 방향 표시)
                self._add_attack_arrow(ax, troop, line_color, alpha)

    def _add_attack_arrow(self, ax, troop, color, alpha):
        """공격 방향 화살표 추가"""
        dx = troop.target.coord.x - troop.coord.x
        dy = troop.target.coord.y - troop.coord.y
        
        # 화살표 크기 조정
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            # 타겟 근처에 화살표 배치 (80% 지점)
            arrow_x = troop.coord.x + 0.8 * dx
            arrow_y = troop.coord.y + 0.8 * dy
            
            # 화살표 크기 정규화
            arrow_dx = (dx / length) * 8  # 8픽셀 크기
            arrow_dy = (dy / length) * 8
            
            ax.arrow(arrow_x, arrow_y, arrow_dx, arrow_dy,
                    head_width=3, head_length=4, 
                    fc=color, ec=color, alpha=alpha, linewidth = 1)

    def _draw_weapon_ranges(self, ax, troop_list):
        """무기 사거리 원 그리기"""
        for troop in troop_list:
            if not troop.alive or not troop.active:
                continue
            
            if troop.range_km > 0:
                # 사거리를 픽셀로 변환 (1km = 100픽셀)
                range_pixels = troop.range_km * 100
                
                # 무기 유형별 색상
                if UnitType.is_indirect_fire(troop.type):
                    color = 'purple'
                    alpha = 0.15
                elif UnitType.is_anti_tank(troop.type):
                    color = 'orange'
                    alpha = 0.2
                elif troop.type == UnitType.TANK:
                    color = 'yellow'
                    alpha = 0.2
                else:
                    color = 'gray'
                    alpha = 0.1
                
                # 사거리 원 그리기
                circle = plt.Circle((troop.coord.x, troop.coord.y), 
                                  range_pixels, 
                                  fill=False, edgecolor=color, 
                                  alpha=alpha, linewidth=1)
                ax.add_patch(circle)

    def _draw_movement_paths(self, ax, troop_list):
        """이동 경로 그리기"""
        for troop in troop_list:
            if not troop.alive or not troop.can_move:
                continue
            
            # 경로가 있는 경우
            if hasattr(troop, 'path') and troop.path:
                path_x = [troop.coord.x] + [p[0] for p in troop.path]
                path_y = [troop.coord.y] + [p[1] for p in troop.path]
                
                ax.plot(path_x, path_y, 
                       color='cyan', linestyle='--', 
                       linewidth=1, alpha=0.6)
            
            # 고정 목적지가 있는 경우
            elif troop.fixed_dest:
                ax.plot([troop.coord.x, troop.fixed_dest.x],
                       [troop.coord.y, troop.fixed_dest.y],
                       color='lime', linestyle='-.', 
                       linewidth=1, alpha=0.5)

    def _draw_troop_markers(self, ax, troop_list):
        """부대 마커 그리기"""
        for troop in troop_list:
            if not troop.alive:
                continue
            
            # 색상 결정
            if not troop.active:
                color = "grey"
                alpha = 0.5
            else:
                color = "blue" if troop.team == "blue" else "red"
                alpha = 0.8
            
            # 마커 모양 결정
            if troop.type == UnitType.TANK:
                marker = "o"
                size = 25
            elif troop.type == UnitType.APC:
                marker = "s"
                size = 20
            elif UnitType.is_indirect_fire(troop.type):
                marker = "^"
                size = 20
            elif UnitType.is_anti_tank(troop.type):
                marker = "D"
                size = 15
            else:
                marker = "s"
                size = 10
            
            ax.scatter(troop.coord.x, troop.coord.y,
                      c=color, marker=marker, 
                      s=size, alpha=alpha,
                      edgecolors='black', linewidths=0.5)

    def create_tactical_overview(self, Map, troop_list, current_time, save_dir="frames"):
        """🟢 전술 개요 시각화 (별도 파일)"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 좌측: 전체 전술 상황
        self._create_overview_plot(ax1, Map, troop_list, current_time)
        
        # 우측: 교전 강도 히트맵
        self._create_engagement_heatmap(ax2, troop_list, current_time)
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/tactical_{int(current_time):05d}.png", dpi=150)
        plt.close()

    def _create_overview_plot(self, ax, Map, troop_list, current_time):
        """전체 전술 상황 플롯"""
        # 간단한 지형 표시
        ax.imshow(Map.dem_arr, cmap="terrain", origin="upper", alpha=0.3)
        
        # 부대 위치만 표시 (공격선 없이)
        self._draw_troop_markers(ax, troop_list)
        
        ax.set_title(f"Overall Situation - T={current_time:.0f} min")
        ax.set_xlim(0, Map.width)
        ax.set_ylim(Map.height, 0)

    def _create_engagement_heatmap(self, ax, troop_list, current_time):
        """교전 강도 히트맵"""
        # 활성 교전 중인 부대들의 위치를 기반으로 히트맵 생성
        engagement_data = []
        
        for troop in troop_list:
            if troop.alive and troop.active and troop.target:
                engagement_data.append([troop.coord.x, troop.coord.y])
        
        if engagement_data:
            engagement_data = np.array(engagement_data)
            
            # 2D 히스토그램으로 교전 밀도 계산
            hist, xedges, yedges = np.histogram2d(
                engagement_data[:, 0], engagement_data[:, 1], 
                bins=50, range=[[0, 800], [0, 600]]
            )
            
            # 히트맵 표시
            im = ax.imshow(hist.T, origin='lower', cmap='Reds', alpha=0.7,
                          extent=[0, 800, 0, 600])
            
            ax.set_title(f"intensity of engagement - T={current_time:.0f} min")
            plt.colorbar(im, ax=ax, label='engagement density')
        else:
            ax.text(0.5, 0.5, 'No Active Engagement', 
                   transform=ax.transAxes, ha='center', va='center')
            ax.set_title(f"intensity of engagement - T={current_time:.0f} min")


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
