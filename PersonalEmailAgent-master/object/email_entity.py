from pydantic import *
from object.tag_entity import Tag

class Email(BaseModel):
    #raw
    title:str="default title"
    content:str="default content"
    sender_email:str="default sender-email"
    sender:str="default sender"

    #added
    id:str="default email-id"

    #gened
    summary: str="default summary"
    response:str="default response"

    #tags
    tags:list[Tag] = Field(default_factory=list)
