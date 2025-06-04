from pydantic import BaseModel, Field
from typing import Optional, List

class Servo(BaseModel):
    id: int
    delta_angle: Optional[int] = Field(default = None, alias = "deltaAngle")
    angle: Optional[int] = None
    interval: Optional[int] = None

    model_config = {
        "validate_by_name": True,
        "populate_by_name": True  # 讓 alias 和實際欄位名稱都可以使用
    }

class Servos(BaseModel):
    servos: List[Servo]
    interval: Optional[int] = 1000
    model_config = {
        "validate_by_name": True,
        "populate_by_name": True  # 讓 alias 和實際欄位名稱都可以使用
    }


class ServosList(BaseModel):
    servos_list: List[Servos] = Field(default = False, alias = "servosList")
    model_config = {
        "validate_by_name": True,
        "populate_by_name": True  # 讓 alias 和實際欄位名稱都可以使用
    }