import chainlit as cl
from rich import print
from agent import create_agent
from agents import Runner,Agent
from typing import cast

@cl.on_chat_start
async def on_start():
    agent=create_agent()
    cl.user_session.set("agent",agent)
    cl.user_session.set('chat_history',[])
@cl.on_message
async def on_msg(msg:cl.Message):
    thinking_msg=cl.Message(content="Thinking")
    await thinking_msg.send()
    agent=cast(Agent,cl.user_session.get("agent"))
    # print("User Message: ",msg.content)
    chat_history:list=cl.user_session.get("chat_history",[])
    chat_history.append({
        "role":"user",
        'content':msg.content
    })
    response=Runner.run_sync(agent,chat_history,max_turns=3)
    # message=cl.Message(
    #     content=f"{response.final_output}"
    # )
    thinking_msg.content=response.final_output
    await thinking_msg.send()
    # print(chat_history)
    cl.user_session.set("chat_history",response.to_input_list())
    print(response.to_input_list())