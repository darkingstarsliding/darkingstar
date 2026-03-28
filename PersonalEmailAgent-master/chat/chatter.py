import asyncio
from langchain import messages
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models import ChatTongyi
from langgraph.graph import StateGraph, START, END,MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
from langchain_community.embeddings import DashScopeEmbeddings
import uuid
from service import memory_manager
from service.memory_manager import get_memory_manager
from pydantic import BaseModel
from agent.sql_agent import sqlquery
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode

llm=ChatTongyi(model="qwen-max")

class Memories(BaseModel):
    memories:list[str]=[]

def printt(obj):
    for _ in range(15):print("-",end="")
    print("")
    print(obj)
    for _ in range(15):print("-",end="")
    print("")

def get_full_message(state:MessagesState):
    full_message:list[str]=[]
    for message in state["messages"]:
        message_type=message.__class__.__name__
        full_message.append(f"""
        message_type:{message_type}\t
        message_content:{message.content}\t
        """)
    return full_message

async def save_new_memory(state:MessagesState):
    prompt:str=f"""
    你是一个"个人邮件智能体"中的聊天机器人,
    这个智能体具有解析分类邮件，自动起草回复，对话等功能。
    作为聊天机器人，请分析最近一次的HumanMessage，
    如果有任何信息可能对智能体有用，
    注意，不要错过任何可能有用的信息，宁多不少
    返回其列表作为记忆（确保内容一条条简明清晰）。
    没有记忆返回空memories列表即可。
    消息记录：{get_full_message(state)}
    """
    new_mems=await llm.with_structured_output(Memories).ainvoke(prompt)
    mem_manager=get_memory_manager()
    for mem in new_mems.memories:
        await mem_manager.store_memory("global_agent",mem)
    return {"messages":AIMessage(content=f"新保存的记忆:{new_mems.memories}")}

sqlquery_tool=Tool.from_function(
    func=sqlquery,
    name="sqlquery_tool",
    description="输入问题到工具，工具会智能给出综合数据库查询结果的回答"
)

async def chat(state:MessagesState):
    #printt(f"Received Messages:{state["messages"]}")
    llm_with_tools=llm.bind_tools([sqlquery_tool])
    reply=llm_with_tools.invoke(get_full_message(state))

    return {"messages":[reply]}

store = InMemoryStore()
checkpointer = InMemorySaver()
builder = StateGraph(MessagesState)

builder.add_node("chat", chat)
builder.add_node("save_new_memory",save_new_memory)
sqlquery_tool_node=ToolNode([sqlquery_tool],name="sqlquery_tool_node")
builder.add_node("sqlquery_tool_node",sqlquery_tool_node)

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "sqlquery_tool_node"
    else:
        return END

builder.add_edge(START, "save_new_memory")
builder.add_edge("save_new_memory","chat")
builder.add_conditional_edges("chat", should_continue)
builder.add_edge("sqlquery_tool_node",END)


graph = builder.compile(store=store,checkpointer=checkpointer)
config = {
    "configurable": {
        "thread_id": "1",
        "user_id": "1"
    }
}

async def chatbot():
    while True:
        user_input=input("Send to AI:")
        input_state = {"messages": [HumanMessage(content=user_input)]}
        async for update in graph.astream(
            input_state,
            config,
            stream_mode="updates",
        ):
            for node_name, node_output in update.items():
                printt(f"""
                节点名称:{node_name}
                节点输出:{node_output}
                """)
                
async def test():
    input_state = {"messages": [HumanMessage(
        content="我不喜欢吃西红柿")]}
    printt(await save_new_memory(input_state))

if __name__=="__main__":
    #asyncio.run(test())
    asyncio.run(chatbot())
