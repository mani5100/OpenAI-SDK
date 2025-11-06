from agents import Agent, Runner, SQLiteSession,OpenAIChatCompletionsModel,AsyncOpenAI
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()

client=AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
model=OpenAIChatCompletionsModel(
    "chatgpt-4o-latest",
    client
)
# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
    model=model
)


session = SQLiteSession("user1", "conversations.db")


async def mainfunc():
    # First turn
    result = await Runner.run(
        agent,
        "What is my name",
        session=session
    )
    print(result.final_output)  # "San Francisco"


def main():
    asyncio.run(mainfunc())