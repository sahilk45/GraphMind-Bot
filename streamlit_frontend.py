import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

CONFIG = {'configurable':{'thread_id':'thread-1'}} #using checkpointer, so while invoke we need thread_id

#st.session_state -> dict , whose values doesn't reset on pressing enter, these reset on reloading
# message_history = [] -> this will not work as empties on every enter
if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]

#loading the conversation history, beac on pressing enter in type here in streamlit complete scripts re-runs so previous msgs will be deleted
#i.e, these are previous msgs in the chat: 
for messages in st.session_state['message_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])


user_input = st.chat_input('Type here')

if user_input:
    #first add msg to message_history
    st.session_state['message_history'].append({'role':'user','content':user_input})
    #display current msg:
    with st.chat_message('user'):
        st.text(user_input)

    response = chatbot.invoke({'messages':[HumanMessage(content=user_input)]},config=CONFIG)
    ai_message = response['messages'][-1].content
    #first add msg to message_history
    st.session_state['message_history'].append({'role':'assistant','content':ai_message})
    with st.chat_message('assistant'):
        st.text(ai_message)