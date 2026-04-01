import streamlit as st
from langgraph_tool_backend import chatbot,retrieve_all_threads
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import uuid

# ****************************Utility Functions ********************

def generate_thread_id():
    thread = uuid.uuid4()
    return thread

def reset_chat():
    thread_id=generate_thread_id()
    st.session_state['thread_id']=thread_id
    #2 on clicking New Chat also have to save:
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history']=[]

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages', [])

# **************************** Session Setup ***********************

if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]

if 'thread_id' not in st.session_state:
    st.session_state['thread_id']= generate_thread_id()

#can't initialize this from empty list, instead have to go and ask db, how many threads already exist
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads']=retrieve_all_threads()

#1) add thread_id in chat_threads on page reload:
add_thread(st.session_state['thread_id'])

# **************************** Sidebar Title ***********************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages = load_conversation(thread_id)

        #to prevent compactibility break b/w chat_history and loading conversation
        temp_messages=[]
        for msg in messages:
            if isinstance(msg,HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role':role,'content':msg.content})

        st.session_state['message_history']=temp_messages



# **************************** Main UI *****************************

for messages in st.session_state['message_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])


user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    #display current msg:
    with st.chat_message('user'):
        st.text(user_input)

    
    # CONFIG = {'configurable':{'thread_id':st.session_state['thread_id']}} 
    # To tell LangSmith about thread_id so to store traces according to it:
    CONFIG={'configurable':{'thread_id':st.session_state['thread_id']},
            'metadata':{'thread_id':st.session_state['thread_id']},
            'run_name':'chat_turn'
            }

    # Assistant streaming block
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens, otherwise tool output also comes on frontend
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )