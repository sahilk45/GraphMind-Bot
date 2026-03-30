from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages #it's specially for adding msgs only and optimized with  
# BaseMessage rather than operator.add
from dotenv import load_dotenv
import sqlite3


load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)


class ChatState(TypedDict):
    #All 4 types of message inherits from BaseMessage- Human,AI,System(role assign),ToolMessage
    messages:Annotated[list[BaseMessage],add_messages]  

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}


#Creating Sqlite Database:
conn = sqlite3.connect(database='chatbot.db',check_same_thread=False) #beac sqlite3 works on single thread 

# Checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


#Now will check in db how many threads already exists to show in frontend:
def retrieve_all_threads():
    all_threads=set()   #beac each thread appears 3 times beac 3 checkpts in each time graph execution.so, don't want redundant thread_ids
    for checkpoint in checkpointer.list(None):  #beac this is a generator obj
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)