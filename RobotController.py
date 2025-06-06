import threading
import time
import logging

from actions.ActionControl import ActionControl
from actions.StopAction import StopAction
from servos.ServosControl import *
from actions.ActionThread import ActionThread
from IsRaspberryPi import is_raspberry_pi


if is_raspberry_pi():
    from TonyPi.HiwonderSDK import Board

class RobotController:
    logger: logging.Logger
    def __init__(self):
        self.is_raspberry_pi = is_raspberry_pi()
        self.log = True
        self.last_log_times = {}
        self.last_start_time = {}
        self.log_interval = 2

        self.action_threads = {
            "arm": ActionThread(),
            "feet": ActionThread(),
        }
        self.logger = self.__setup_logging()

    def check_interval_time(self, action_thread: ActionThread):
        now = time.time()
        if abs(now - action_thread.last_start_time) < 0.1:
            self.logger.warning(f"[Debounce] 忽略過快的 start_actions 呼叫")
            return False

        action_thread.last_start_time = now
        return True

    def __setup_logging(self):
        logger = logging.getLogger("robot")
        logger.setLevel(logging.INFO)
        for handler in logger.handlers[:]:  # 注意要 [:] 拷貝，避免疊代時修改原始列表
            logger.removeHandler(handler)

        if self.log:
            handler = logging.StreamHandler()
        else:
            handler = logging.NullHandler()  # 不輸出任何東西

        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def _run_action(self, action_thread: ActionThread, servos_list: ServosList):
        try:
            if self.is_raspberry_pi:
                self.control_json(action_thread, servos_list)
            else:
                self.logger.info(f"[Sim] 模擬動作: {action_thread.last_direction}")
                time.sleep(1.0)
        finally:
            with action_thread.lock:
                action_thread.running_action = False
                action_thread.stop_event.set()
                self.logger.info(f"[End] 動作 {action_thread.last_direction} 停止")


    def start_actions(
            self,
            action_thread: ActionThread,
            position: str,
            direction: str,
            force: float = 0.0
    ):
        if not self.check_interval_time(action_thread):
            return
        with action_thread.lock:
            if action_thread.running_action:
                self.logger.info(f"[Lock] 已在執行 start_actions（方向：{action_thread.last_direction}），忽略此次：{direction}")
                return  # 忽略新的 start_feet_actions 請求

            action_thread.running_action = True  # 上鎖，表示開始執行
            action_thread.stop_event.clear()

            action_thread.last_direction = direction

            action_thread.action_thread = threading.Thread(
                target = self._run_action,
                kwargs = {
                    "action_thread": action_thread,
                    "servos_list": get_action_servos_list(position, direction, force)
                }
            )
            action_thread.action_thread.start()




    def stop_action(self, stop_action: StopAction):
        action_thread = self.action_threads.get(stop_action.position, ActionThread())
        action_thread.stop_event.set()  # 中斷 control_json
        if action_thread.action_thread and action_thread.action_thread.is_alive():
            self.logger.info("[Stop] 強制結束動作執行緒")
            action_thread.action_thread.join(timeout=0.5)

        action_thread.action_thread = None
        action_thread.running_action = False
        action_thread.last_dir = None
        self.logger.info("[Stop] 動作中止，開始回到 stand")

        # 執行 stand 動作（獨立執行，不再遞迴呼叫 stop_action）
        self._run_stand_action(action_thread)

    def _run_stand_action(self, action_thread: ActionThread):
        with action_thread.lock:
            action_thread.running_action = True  # 鎖定，避免被其他 start_actions 插入
            action_thread.stop_event.clear()
            action_thread.action_thread = threading.Thread(
                target = self._run_action,
                kwargs = {
                    "action_thread": action_thread,
                    "servos_list": feet_stand()
                }
            )
            action_thread.action_thread.start()


    def control_group_action_control(self, action_control: ActionControl) -> bool:
        return self.control_group(
            action_control.position,
            action_control.direction,
            action_control.force
        )

    def control_group(
            self,
            position: str,
            direction: str,
            force: float = 0.0
    ) -> bool:
        action_thread = self.action_threads.get(position, ActionThread())
        self.start_actions(
            action_thread,
            position,
            direction,
            force,
        )

        return True

    def control_json(self, action_thread: ActionThread, servos_list: ServosList) -> bool:
        if action_thread.stop_event.is_set():
            self.logger.info("[Interrupt] 控制中斷，停止動作")
            return False

        for servos in servos_list.servos_list:
            max_interval = 0
            for servo in servos.servos:

                if self.is_raspberry_pi:
                    angle = min(max((
                            servo.angle or
                            Board.getBusServoPulse(servo.id) + (servo.delta_angle or 0)
                    ), 0), 1000)
                    Board.setBusServoPulse(
                        servo.id,
                        angle,
                        servo.interval or servos.interval
                    )
                max_interval = max(max_interval, servo.interval or servos.interval)
            time.sleep(max_interval / 1000.0)

        return True