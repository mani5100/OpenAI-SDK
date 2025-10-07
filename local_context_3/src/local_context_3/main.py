from agents import (
    OpenAIChatCompletionsModel,
    Runner,
    AsyncOpenAI,
    Agent,
    function_tool,
    RunContextWrapper
)
from dotenv import load_dotenv
from dataclasses import dataclass

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

def main():
    response=Runner.run_sync(starting_agent=agent,input="What is my name.",context=user1)
    print(response.final_output)