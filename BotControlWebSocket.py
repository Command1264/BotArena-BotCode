import asyncio
from typing import Optional
import websockets
from pydantic import BaseModel

from actions.ReturnStatus import ReturnStatus
from actions.ActionControl import ActionControl
from actions.StopAction import StopAction
from RobotController import RobotController

robot = RobotController()

class WebSocketAction(BaseModel):
    request_id: str
    action: str
    position: Optional[str] = ""
    direction: Optional[str] = ""
    force: Optional[float] = 0.0

    def to_action_control(self):
        return ActionControl(
            position = self.position,
            direction = self.direction,
            force = self.force
        )

    def to_stop_action(self) -> StopAction:
        return StopAction(position = self.position)

async def handle_connection(websocket):
    try:
        try:
            async for message in websocket:
                web_socket_action = WebSocketAction.model_validate_json(message)
                # 控制
                if web_socket_action.action == "checkControl":
                    (success, can_use) = robot.check_action_can_use(
                        web_socket_action.to_action_control()
                    )
                    await websocket.send(
                        ReturnStatus(
                            request_id = web_socket_action.request_id,
                            success = success,
                            status = str(can_use)
                        ).model_dump_json()
                    )
                elif web_socket_action.action == "control":
                    await websocket.send(
                        ReturnStatus(
                            request_id = web_socket_action.request_id,
                            success = robot.control_group_action_control(
                                web_socket_action.to_action_control()
                            ),
                            status = "ok"
                        ).model_dump_json()
                    )
                # 停止
                elif web_socket_action.action == "stop":
                    robot.stop_action(web_socket_action.to_stop_action())
                    await websocket.send(
                        ReturnStatus(
                            request_id = web_socket_action.request_id,
                            success = True,
                            status = "stopped"
                        ).model_dump_json()
                    )
                # ping
                elif web_socket_action.action == "ping":
                    await websocket.send(
                        ReturnStatus(
                            request_id = web_socket_action.request_id,
                            success = True,
                            status = "pong"
                        ).model_dump_json()
                    )
                # 未知
                else:
                    await websocket.send(
                        ReturnStatus(
                            request_id = web_socket_action.request_id,
                            success = False,
                            status = "未知指令"
                        ).model_dump_json()
                    )

        except Exception as e:
            print(e)
            await websocket.send(
                ReturnStatus(
                    request_id = "null",
                    success = False,
                    status = str(e)
                ).model_dump_json()
            )
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"⚠️ WebSocket 意外關閉: {e}")
    except Exception as e:
        print(f"❌ 意外錯誤: {e}")
    finally:
        print("🔌 連接已退出")

async def main(host, port):
    async with websockets.serve(
            handle_connection,
            host,
            port,
    ):
        print(f"✅ WebSocket 伺服器正在監聽 ws://{host}:{port}")
        await asyncio.Future()  # 永遠等待，直到被手動中止

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 60922
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # # ssl_context.load_cert_chain(
    # #     certfile='/home/pi/fullchain.pem',
    # #     keyfile='/home/pi/privkey.pem'
    # # )
    # ssl_context.load_cert_chain(
    #     certfile='./cert.pem',
    #     keyfile='./key.pem'
    # )
    asyncio.run(main(host, port))


# if __name__ == "__main__":
#     host = "0.0.0.0"
#     port = 8765
#     server = websockets.serve(
#         handle_connection,
#         host,
#         port,
#         # ssl = ssl_context
#     )
#     asyncio.get_event_loop().run_until_complete(server)
#     print(f"✅ WebSocket server listening on ws://{host}:{port}")
#     asyncio.get_event_loop().run_forever()
