from dataclasses import dataclass
from dotenv import load_dotenv
from agents import AsyncOpenAI,OpenAIChatCompletionsModel
import os
load_dotenv()
@dataclass
class Config():
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    POSTGRES_URL:str = os.getenv("POSTGRES_URL")

openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

openai_model=OpenAIChatCompletionsModel(
    Config.OPENAI_CHAT_MODEL,
    openai_client
)
