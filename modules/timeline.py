# timeline.py


class TimelineEvent:  # Timeline event types
    def __init__(self, time, time_str, description, t_a, t_f):
        self.time = time  # Event time
        self.time_str = time_str  # Event time as string
        # self.event_type = event_type  # Event type (e.g., "fire", "move")
        self.description = description
        self.t_a = t_a  # Time of action
        self.t_f = t_f  # Time of fire


TIMELINE = [
    TimelineEvent(0, "13:55", "BLUE 전차70대 방어진지 배치 명령", 0.5, 1),
    TimelineEvent(5, "14:00", "BLUE 모든 소대 방어진지 점검 완료", None, None),
    TimelineEvent(30, "14:25", "RED(E1) 교량전차·보병 투입 시도", 1, 1),
    TimelineEvent(60, "14:55", "RED(E1) 실패 후 예비포 지원사격", 0.5, 1),
    TimelineEvent(125, "15:40", "RED(E2) 모로코 여단 돌격 시작", 2, 1.5),
    TimelineEvent(130, "15:45", "BLUE Tel Shaeta·Hermonit 방어 강화", 0.5, 1),
    TimelineEvent(180, "16:35", "RED 중대 E2 후속 기갑 소규모 침투 시도", 1, 1),
    TimelineEvent(300, "18:15", "BLUE Barak여단 65대 증강 완료 보고", None, None),
    TimelineEvent(360, "19:15", "야간 준비: BLUE 은폐·탐지·매복 배치", None, None),
    TimelineEvent(365, "19:20", "RED(E3) 78·82기갑 동시 투입", 1.5, 2),
    TimelineEvent(425, "20:25", "야간 주요 교전 고착", None, None),
    TimelineEvent(1440, "07:00(2일)", "RED 추가 E4 예비포·보병투입", 1, 1),
    TimelineEvent(2880, "13:55(4일)", "종료: 전멸 or 시간만료", None, None),
]
