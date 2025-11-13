from pydantic import BaseModel


class CreateBotIn(BaseModel):
    name: str
    token: str


class CreateBotOut(BaseModel):
    id: int
    name: str
    channel: str
