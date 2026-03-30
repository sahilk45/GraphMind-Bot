from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages #it's specially for adding msgs only and optimized with  
# BaseMessage rather than operator.add
from dotenv import load_dotenv


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

# Checkpointer
checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)