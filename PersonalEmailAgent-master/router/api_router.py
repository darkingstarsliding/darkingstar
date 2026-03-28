from typing import *
from fastapi import *
from pydantic import *
from sqlalchemy.ext.asyncio import *
from sqlalchemy.orm import *
from fastapi import *
from sqlalchemy import *
from object.email_entity import Email
from workflow.email_classify import launch_classify
from fastapi import BackgroundTasks
from object.chat_entity import ChatMsg


app = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )


@app.post("/mail/receive")
async def receive_email(email:Annotated[Email,Body()],
    background_tasks:BackgroundTasks):
    '''
    result=await launch_classify(email)
    print(result)
    '''
    background_tasks.add_task(launch_classify,email)
    return {
        "info":"Email will be proceeded by Agent and stored in your database Later",
        "received-email-content": email.content
    }

@app.post("/chat/")
async def chat(message:Annotated[ChatMsg,Body()]):
    return message


