import requests
import logging

if __name__ == "__main__":
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:  # 注意要 [:] 拷貝，避免疊代時修改原始列表
        logger.removeHandler(handler)

    handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    i = 0
    while True:
        logger.info(i)
        i += 1
        r = requests.post(
            url = "http://raspberrypi:60922/botarena/api/v1/control/stop",
            json = {
                "position": "feet",
                # "direction": "up",
                # "force": 5
            }
        )
        if r.status_code != 200:
            break


