from pydantic import BaseModel


class ReturnStatus(BaseModel):
    success: bool
    status: str = "ok"