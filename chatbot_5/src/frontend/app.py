import chainlit as cl
from agent import create_agent
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent,Runner
from typing import cast
from rich import print

import chainlit as cl

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="General Help & Guidance",
            message="You are an experienced assistant ready to help with any questions I have. Please provide detailed, step-by-step explanations and guide me through whatever I need help with.",
            icon="/public/logo.png",
            mode="Help",
            command="Help"
        ),
        cl.Starter(
            label="Python Development Help",
            message="You are an experienced Python developer. I need help writing Python code. Please guide me through the process step-by-step, explain your approach, and help me understand the code you write.",
            icon="/public/logo.png",
            command="Code",
            mode="coding"
        ),
        cl.Starter(
            label="Chemistry Teacher",
            message="You are an experienced chemistry teacher. I will ask you questions related to chemistry and you have to explain them step-by-step in detail with examples where needed.",
            icon="/public/logo.png",
            mode="chemistry",
            command="Teaching"
        ),
        cl.Starter(
            label="Problem-Solving Assistant",
            message="You are an expert problem-solver. I will present problems to you and you need to work through them with me step-by-step, explaining your reasoning and helping me understand the solution process.",
            icon="/public/logo.png",
            mode="problem-solving",
            command="Teaching"
        )
    ]

@cl.on_chat_start
async def agent():
    agent=create_agent()
    cl.user_session.set("agent",agent)
    cl.user_session.set("session_history",[])
@cl.on_message
async def on_message(msg:cl.Message):
    # thinking_message=cl.Message(content="Thinking") #There are 2 messages now we have to use one to avoid redundency
    message=cl.Message(content="Thinking...")
    await message.send()
    agent=cast(Agent,cl.user_session.get("agent"))
    session_history:list=cast(list,cl.user_session.get("session_history",[]))
    session_history.append({
        "role":'user',
        "content":msg.content
    })
    res=Runner.run_streamed(
        starting_agent=agent,
        input=session_history
    )
    async for event in res.stream_events():
        if event.type=="raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
            if message.content=="Thinking...":
                message.content=""
                await message.update()
            await message.stream_token(event.data.delta)
    # print("="*20) #This was for checking how session history is maintained
    cl.user_session.set("session_history",res.to_input_list())
    # print(cl.user_session.get("session_history")) #This was for checking how session history is maintained
    # print("="*20) #This was for checking how session history is maintained
    
    # await cl.Message(content=res.final_output).send()
    message.content=res.final_output
    await message.update()