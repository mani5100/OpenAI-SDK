from dotenv import load_dotenv
from agents import (
    AsyncOpenAI,
    set_default_openai_client,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    Agent,
    Runner
)
load_dotenv()
import os
external_client=AsyncOpenAI()
set_default_openai_client(external_client)
llm_model=OpenAIChatCompletionsModel(
    model="gpt-3.5-turbo",
    openai_client=external_client
)
set_tracing_disabled(True)
agent=Agent(
    name="Customer Service Agent",
    instructions="You are a helpful assistant, specialized in providing single-line responses.",
    model=llm_model,
)
response = Runner.run_sync(agent, "What is AI?")
print(response.final_output)