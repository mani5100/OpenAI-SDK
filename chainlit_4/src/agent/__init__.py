from agents import (
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    Agent
    
)
from config import Config


def create_agent()->Agent:
    config=Config()
    external_client=AsyncOpenAI(
        api_key=config.openai_api_key
    )
    set_tracing_disabled(disabled=True)
    model=OpenAIChatCompletionsModel(
        model=config.openai_api_model,
        openai_client=external_client
    )

    agent=Agent(
        "Chatbot Assistant",
        instructions="You are a helpful assistant.",
        model=model
        )
    return agent