from flask import Flask, request, jsonify

from actions.ActionControl import ActionControl
from actions.ReturnStatus import ReturnStatus
from actions.StopAction import StopAction
from RobotController import RobotController

app = Flask(__name__)
robot = RobotController()

@app.route("/botarena/api/v1/control/group", methods=["POST"])
def group_control():
    try:
        action_control = ActionControl.model_validate(request.get_json())
    except Exception as e:
        return jsonify({"error": e}), 400

    return jsonify(ReturnStatus(
        success = robot.control_group_action_control(action_control)
    ).model_dump())

@app.route("/botarena/api/v1/control/stop", methods=["POST"])
def stop_control():
    try:
        stop_action = StopAction.model_validate(request.get_json())
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    robot.stop_action(stop_action)
    return jsonify(ReturnStatus(
        success = True,
        status = "stopped"
    ).model_dump())


@app.route("/")
def index():
    return jsonify(ReturnStatus(
        success = True,
        status = "Hiwonder robot HTTP class-based control ready!",
    ).model_dump())

if __name__ == "__main__":
    app.run(
        host = "0.0.0.0",
        debug = True,
        port = 60922,
    )
