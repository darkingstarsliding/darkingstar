from pydantic import BaseModel


class ChatMsg(BaseModel):
    message:str="default message"