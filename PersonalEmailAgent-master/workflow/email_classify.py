import asyncio
from typing import *
import uuid
from langgraph.graph import *
from langgraph.types import *
from langchain.messages import *
from langchain_community.chat_models import *
from langgraph.checkpoint.memory import *
from sqlalchemy import desc
from object.email_entity import Email
from object.tag_entity import Tag
from service import memory_manager
from service.database_service import load_tag_definitions
from service.memory_manager import MemoryManager, get_memory_manager
from langchain_core.tools import Tool
from datetime import datetime
import json

RAG_LIMIT=10

class EmailAgentState(TypedDict):
    #email object (with classification)
    email:Email
    
    # Generated content
    draft_response: str | None
    new_tags: list[Tag]|None


llm=ChatTongyi(model="qwen-max")

def print_with_gap(obj):
    for _ in range(20):
        print("-",end="")
    print("")
    print(obj)
    for _ in range(20):
        print("-",end="")
    print("")

def serialize(obj):
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    return str(obj)  

def read_email(state: EmailAgentState):
    email=state["email"]
    email.id=str(uuid.uuid4())
    return Command(
        update={"email":email},
        goto="fill"
    )

def build_fill_prompt(email:Email):
    prompt:str=f"""
    分析邮件并且补全Email中的：
    summary属性。
    当前邮件内容: {email}
    """
    return prompt

def fill(state: EmailAgentState):
    """generate info like summary"""
    structured_llm = llm.with_structured_output(Email)
    prompt=build_fill_prompt(state["email"])
    email = structured_llm.invoke(prompt)

    return Command(
        update={"email": email},
        goto="classify"
    )

async def build_classify_prompt(email:Email):
    #read existing tags definition from DB
    tags=await load_tag_definitions()
    prompt:str=f"""
    根据如下的标签定义，给邮件加上标签。
    只修改邮件的标签列表，其他不要修改。
    尽量使用标签定义中每个标签现有的标签值。
    邮件内容：{email}
    标签定义：{tags}
    """
    return prompt

async def classify(state:EmailAgentState):
    structured_llm = llm.with_structured_output(Email)
    prompt=await build_classify_prompt(state["email"])
    email = structured_llm.invoke(prompt)
    return Command(
        update={"email":email},
        goto="draft_response"
    )


async def retrieve_memory_by_email(query:str) -> str:
    print_with_gap(f"接受到的查询请求：{query}")
    mem_manager=get_memory_manager()
    result=await mem_manager.search_memories("global_agent",query,limit=RAG_LIMIT)
    if result["relevant_memories"]:
        memories = [mem["content"] for mem in result["relevant_memories"]]
        return "\n\n".join(memories)
    else:
        return "未找到相关记忆"

retrieve_memory_by_email_tool=Tool.from_function(
    func=retrieve_memory_by_email,
    name="retrieve_memory_by_email_tool",
    description="""根据给定的内容查找记忆"""
)


def get_tag_value(email:Email,tag_name:str):
    if email.tags:
        for tag in email.tags:
            if tag.name==tag_name:
                return getattr(tag,"value","")
    return ""

def build_tool_call_prompt(email:Email):
    prompt:str=f"""
    使用"retrieve_memory_by_email_tool"工具，
    来检索用于回复的记忆。
    从回信者的角度，多向记忆检索工具提问题，
    其中一个问题必须是当前email的summary（summary内容如下
    ，照搬即可）。
    邮件:{email}\n\n
    """
    return prompt

def build_draft_response_prompt(email:Email,material:str):
    prompt:str=f"""
    根据邮件的内容和相关信息起草回复。
    直接给出回复，不要多余废话。
    邮件内容：{email}\n\n
    相关信息（越靠前的越新）：{material}\n\n
    """
    return prompt

async def draft_response(state: EmailAgentState):

    email = state.get('email',{})
    #是否需要起草回复
    reponse_or_not=get_tag_value(email,"need_response")
    if reponse_or_not=="no":
        return Command(goto="save_email")

    
    tool_call_prompt = build_tool_call_prompt(email)
    response =await llm.bind_tools([retrieve_memory_by_email_tool]).ainvoke(tool_call_prompt)

    queries:list[str]=[]
    print_with_gap(f"工具调用情况:\n{response.tool_calls}")
    for tool_call in response.tool_calls:
        if tool_call["name"]=="retrieve_memory_by_email_tool":
            queries.extend(tool_call["args"].values())
    materials=[await retrieve_memory_by_email(q) for q in queries]
    
    #结果保持原顺序（新记忆在前）去重
    seen = set()
    ordered_unique_materials = []
    for m in materials:
        if m not in seen:
            seen.add(m)
            ordered_unique_materials.append(m)

    material = "\n\n".join(ordered_unique_materials)

    print_with_gap(f"查询到的记忆：{material}")
    draft_response_prompt=build_draft_response_prompt(email,material)
    draft_response=llm.invoke(draft_response_prompt).content
    email.response=draft_response

    return Command(
        update={
            "draft_response": draft_response,
            "email":email
        },
        goto="save_email"
    )

def save_email(state:EmailAgentState):
    pass


# For Test 
cur_state = EmailAgentState(
    email=Email(
        title="下周六来我家做客",
        content="""
        我给你准备了蛋糕，点心，
        另外想问问你有什么喜欢的水果吗？
        """,
        sender_email="Jennifer1996@example.com",
        sender="Jennifer" 
    ),
    draft_response=None,
    new_tags=None
)



async def test():
    result=read_email(cur_state)
    cur_state["email"]=result.update["email"]
    print_with_gap(cur_state)
    result=fill(cur_state)
    cur_state["email"]=result.update["email"]
    print_with_gap(cur_state)
    result=await classify(cur_state)
    cur_state["email"]=result.update["email"]
    print_with_gap(cur_state)
    result=await draft_response(cur_state)
    #cur_state["email"]=result.update["email"]
    print_with_gap(result.update["draft_response"])

async def overall_test():
    # Create the graph
    workflow = StateGraph(EmailAgentState)

    # Add nodes 
    workflow.add_node("read_email", read_email)
    workflow.add_node("fill",fill)
    workflow.add_node("classify", classify)
    workflow.add_node("draft_response", draft_response)
    workflow.add_node("save_email",save_email)

    # Add only the essential edges
    workflow.add_edge(START, "read_email")
    workflow.add_edge("save_email", END)

    app = workflow.compile()
    result =await app.ainvoke(cur_state)
    print("工作流结果:", result)

async def launch_classify(email:Email) :
    workflow = StateGraph(EmailAgentState)

    workflow.add_node("read_email", read_email)
    workflow.add_node("fill",fill)
    workflow.add_node("classify", classify)
    workflow.add_node("draft_response", draft_response)
    workflow.add_node("save_email",save_email)

    workflow.add_edge(START, "read_email")
    workflow.add_edge("save_email", END)

    initial_state = EmailAgentState(
        email=email,
        draft_response=None,
        new_tags=None
    )
    app = workflow.compile()
    
    result =await app.ainvoke(initial_state)
    print_with_gap(f"工作流结果:{result}")
    
    with open("result_log.txt","a",encoding="utf-8") as file:
        file.write(str(uuid.uuid4())+"\n")
        file.write(datetime.now().isoformat()+"\n")
        file.write(json.dumps(result, default=serialize,ensure_ascii=False, indent=4))
        file.write("\n\n")

    return result


if __name__=="__main__":
    asyncio.run(overall_test())
    #asyncio.run(step_test())