from langchain_community.chat_models import ChatTongyi
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Literal
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
import uuid
from service.database_service import load_tag_definitions
import asyncio

db = SQLDatabase.from_uri("postgresql://postgres:darking151060@localhost:5432/emailagent")

model=ChatTongyi(model="qwen-max")
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
run_query_node = ToolNode([run_query_tool], name="run_query")

class SQLAgentState(MessagesState):
    query_limit:int=5

def print_with_gap(obj):
    for _ in range(20):
        print("-",end="")
    print("")
    print(obj)
    for _ in range(20):
        print("-",end="")
    print("")

_tag_definitions_cache = None
 
def get_cached_tag_definitions():
    global _tag_definitions_cache
    if _tag_definitions_cache is None:
        _tag_definitions_cache = asyncio.run(load_tag_definitions())
    return _tag_definitions_cache

def get_query_prompt(limit:int=5):
    query_system_prompt = """
    你是一个"个人邮件智能体"中负责与数据库交互的子智能体。
    给你一个和邮件相关的问题，你需要给出对应的postgres查询语句。
    请调用"run_query"工具进行SQL查询。
    如果你发现已经没有必要的查询，就不调用工具。
    以下是数据库表结构:
    {table_structure}
    已有的标签如下：
    {tag_defs}
    """
    with open("SQL/init.sql",encoding="utf-8") as file:
        table_structure=file.read()
    tag_defs=get_cached_tag_definitions()
    query_system_prompt=query_system_prompt.format(
        table_structure=table_structure,
        tag_defs=tag_defs
    )
    return query_system_prompt

def generate_query(state: SQLAgentState):
    system_message = {
        "role": "system",
        "content": get_query_prompt(state.get("query_limit")),
    }
    llm_with_tools = model.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message] + state["messages"])
    
    return {"messages": [response]}


check_query_system_prompt = """
你是一个对细节苛刻的SQL专家。
检查Postgres SQL语句是否有问题，如果有，给出修正后的SQL语句。
如果没有，原样回复即可。
在做完检查后，你还需要调用"run_query"工具来执行SQL语句。
"""

def check_query(state: SQLAgentState):
    system_message = {
        "role": "system",
        "content": check_query_system_prompt,
    }

    # Generate an artificial user message to check
    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = model.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id

    return {"messages": [response]}

def should_continue(state: SQLAgentState) -> Literal[END, "check_query"]:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "check_query"

def sqlquery(question:str=""):

    builder = StateGraph(SQLAgentState)
    builder.add_node(generate_query,"generate_query")
    builder.add_node(check_query,"check_query")
    builder.add_node(run_query_node, "run_query")

    builder.add_edge(START, "generate_query")
    builder.add_conditional_edges(
        "generate_query",
        should_continue,
    )
    builder.add_edge("check_query", "run_query")
    builder.add_edge("run_query", "generate_query")

    agent = builder.compile()

    result=agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content


if __name__=="__main__":
    #print(asyncio.run(load_tag_definitions()))
    #print_with_gap(get_query_prompt())
    '''
    sqlquery("""
    新增一个标签，名字叫"mood"，取值有"happy","sad","no"
    三种，描述是"邮件内容包含的情绪"，启用该标签。
    """)
    '''
    #print(sqlquery("帮我查所有重要程度为中等的邮件"))
