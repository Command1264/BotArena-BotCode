from pydantic import BaseModel, Field
from typing import List, Optional


class StopAction(BaseModel):
    position: str

    model_config = {
        "validate_by_name": True,
        "populate_by_name": True  # 讓 alias 和實際欄位名稱都可以使用
    }