import chainlit as cl
@cl.on_message
async def on_message(message:cl.Message):
    print(message.content)

