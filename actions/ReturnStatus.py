from pydantic import BaseModel


class ReturnStatus(BaseModel):
    request_id: str
    success: bool
    status: str = "ok"