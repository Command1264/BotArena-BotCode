from servos.Servos import *
import sqlite3
from pydantic import BaseModel
from typing import Dict

from IsRaspberryPi import is_raspberry_pi

if is_raspberry_pi():
    # from TonyPi.HiwonderSDK import ActionGroupControl as agc
    from TonyPi.HiwonderSDK import Board


left_feet_servo_range = [1, 2, 3, 4, 5]
right_feet_servo_range = [9, 10, 11, 12, 13]
feet_servo_range = left_feet_servo_range + right_feet_servo_range

left_arm_servo_range = [6, 7, 8]
right_arm_servo_range = [14, 15, 16]
arm_servo_range = left_arm_servo_range + right_arm_servo_range


class Action(BaseModel):
    max_interval: int = 100
    min_interval: int = 50

class FeetAction(Action):
    path: str = "./TonyPi/ActionGroups/stand.d6a"

class ArmAction(Action):
    max_delta_angle: int = 100
    min_delta_angle: int = 50
    actions: ServosList
    def __init__(
            self,
            action: str,
            force: float,
            max_delta_angle,
            min_delta_angle,
            max_interval,
            min_interval,
    ):
        super().__init__(max_interval = max_interval, min_interval = min_interval)
        self.max_delta_angle = max_delta_angle
        self.min_delta_angle = min_delta_angle
        self.actions = self.generate_actions(action, force)

    def generate_actions(self, action: str = None, force: float = 0.0) -> ServosList:
        # 沒加會導致在非 raspberrypi 的環境上會出現 Exception
        if not is_raspberry_pi():
            return ServosList(
                servosList = [
                    Servos(
                        servos = []
                    )
                ]
            )
        delta_angle = int(round(map_clamped(
            force,
            0,
            1,
            self.min_delta_angle,
            self.max_delta_angle
        )))
        angles = {
            16: Board.getBusServoPulse(16),
            15: Board.getBusServoPulse(15),
            14: Board.getBusServoPulse(14),
        }

        # 16: 300-850 if 15 > 150 and 14 > 500 else 525-725
        # 15: 175-500 if 16 in 525-725 else 198-500
        # 14: 100-550 if 16 in 525-725 else 426-550
        if action in ("up", "down"):
            return ServosList(
                servosList = [
                    Servos(
                        servos = [
                            Servo(
                                id = 16,
                                angle = min(max(angles[16] + (delta_angle if action == "up" else -delta_angle), 300), 850)
                                    if angles[15] > 150 and angles[14] > 500 else
                                min(max(angles[16] + (delta_angle if action == "up" else -delta_angle), 525), 725)
                            )
                        ],
                    )
                ]
            )
        elif action in ("left", "right"):
            estimated_angles = [
                angles[15] - delta_angle,
                angles[14] - delta_angle
            ] if action == "left" else [
                angles[15] + delta_angle,
                angles[14] + delta_angle
            ]
            return ServosList(
                servosList = [
                    Servos(
                        servos = [
                            Servo(
                                id = 15,
                                angle = min(max(estimated_angles[0], 175), 500) \
                                    if (525 <= angles[16] <= 725) else \
                                    min(max(estimated_angles[0], 200), 500)
                            ),
                            Servo(
                                id = 14,
                                angle = min(max(estimated_angles[0], 100), 550) \
                                        if (525 <= angles[16] <= 725) else \
                                    min(max(estimated_angles[0], 425), 550)
                            ),
                        ],
                    )
                ]
            )
        else:
            return {}



feet_action_map = {
    "up": FeetAction(
        path = "./TonyPi/ActionGroups/go_forward_fast.d6a",
        max_interval = 200,
        min_interval = 45
    ),
    "down": FeetAction(
        path = "./TonyPi/ActionGroups/back_fast.d6a",
        max_interval = 500,
        min_interval = 250
    ),
    "left": FeetAction(
        path = "./TonyPi/ActionGroups/left_move_fast.d6a",
        max_interval = 400,
        min_interval = 100
    ),
    "right": FeetAction(
        path = "./TonyPi/ActionGroups/right_move_fast.d6a",
        max_interval = 400,
        min_interval = 100
    ),
}

def map_clamped(x, in_min, in_max, out_min, out_max):
    x = max(min(x, in_max), in_min)
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def load_servos_from_db(
        db_path: str,
        servo_range: List[int] = None,
) -> ServosList:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 假設資料表叫 servo_table，有18欄 (0~17)
    cursor.execute("SELECT * FROM ActionGroup")
    rows = cursor.fetchall()

    servos_list = []

    for row in rows:
        interval = row[1]  # 第2欄為 interval
        servo_angles = row[2:]  # 第3~18欄為角度值，共16個

        servos_list.append(Servos(
            servos = [
                Servo(id = i + 1, angle = angle)  # id從1開始
                for i, angle in enumerate(servo_angles)
                if servo_range is None or (i + 1) in servo_range
            ],
            interval = interval)
        )

    conn.close()
    return ServosList(servosList = servos_list)


def feet_stand() -> ServosList:
    stand_action = load_servos_from_db(
        "./TonyPi/ActionGroups/stand.d6a",
        feet_servo_range
    )
    for servos in stand_action.servos_list:
        servos.interval = 50
    return stand_action


def get_action_servos_list(
        position: str,
        action: str = "stand",
        force: float = 0.0
) -> ServosList:
    is_feet = position == "feet"
    action = feet_action_map.get(action, lambda _: FeetAction(
        path = "./TonyPi/ActionGroups/stand.d6a",
        max_interval = 50,
        min_interval = 50
    )) if is_feet else ArmAction(
        action = action,
        force = force,
        max_interval = 200,
        min_interval = 50,
        max_delta_angle = 100,
        min_delta_angle = 10,
    )
    interval = int(round(map_clamped(
        force,
        0,
        1,
        action.max_interval,
        action.min_interval,
    )))

    servos_list = load_servos_from_db(
        action.path,
        feet_servo_range,
    ) if is_feet else action.actions

    for servos in servos_list.servos_list:
        servos.interval = interval
    return servos_list

