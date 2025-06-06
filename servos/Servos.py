from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class Servo(BaseModel):
    id: int = -1
    delta_angle: Optional[int] = Field(default = None, alias = "deltaAngle")
    angle: Optional[int] = None
    interval: Optional[int] = None

    model_config = ConfigDict(
        validate_by_name=True,
        populate_by_name=True,
    )

class Servos(BaseModel):
    servos: List[Servo] = Field(default_factory = list)
    interval: Optional[int] = 1000

    model_config = ConfigDict(
        validate_by_name=True,
        populate_by_name=True,
    )


class ServosList(BaseModel):
    servos_list: List[Servos] = Field(default_factory = list, alias = "servosList")

    model_config = ConfigDict(
        validate_by_name=True,
        populate_by_name=True,
    )