from pydantic import BaseModel


class ActionControl(BaseModel):
    position: str
    direction: str
    force: float = 0.0

    model_config = {
        "validate_by_name": True,
        "populate_by_name": True  # 讓 alias 和實際欄位名稱都可以使用
    }