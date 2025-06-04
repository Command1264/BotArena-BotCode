import threading

class ActionThread:
    def __init__(self):
        self.last_direction = None
        self.lock = threading.Lock()  # 保護多執行緒共享資源
        self.stop_event = threading.Event() # 新增：可中斷的旗標
        self.running_action = False  # 表示目前是否正在執行 start_action
        self.action_thread = None