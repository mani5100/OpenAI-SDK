from agents import (
    OpenAIChatCompletionsModel,
    Runner,
    AsyncOpenAI,
    Agent,
    function_tool,
    RunContextWrapper,
)
from openai.types.responses import ResponseTextDeltaEvent
import asyncio
from dotenv import load_dotenv
from dataclasses import dataclass
from rich import print

@dataclass
class User:
    name:str
    age:int
    location:str
   
@function_tool
def user_info(ctx:RunContextWrapper[User])->str:
    """This rerurn the user information. His name, age and current location"""
    return f"""name of user is {ctx.context.name}
Age of user is {ctx.context.age}
Location of user is {ctx.context.location}"""

def dynamic_instruction(ctx:RunContextWrapper[User],agent:Agent):
    if ctx.context.age<18:
        return "You are a assistant and you can not provide any informations to user as it is a minor."
    else:
        return "You are a assistant. If asked you have to provide the information to the user"   
user1=User("Abdul",23,"Lahore")
load_dotenv()
externalClient=AsyncOpenAI()
model=OpenAIChatCompletionsModel(
    "gpt-3.5-turbo",
    openai_client=externalClient
)
agent=Agent[User](
    "Assistant",
    instructions=dynamic_instruction,
    tools=[user_info]
)
agent1=agent.clone(
    name="Assistant 1",
    instructions="You are a helpful assistant. You can to call tool to get info of user."
)

async def main_func():
    response=Runner.run_streamed(starting_agent=agent,input="Write a 500 word essay on pakistani culture",context=user1)
    async for event in response.stream_events():
        if event.type== "raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
            print(event.data.delta,end="")
        
def main():
    asyncio.run(main_func())