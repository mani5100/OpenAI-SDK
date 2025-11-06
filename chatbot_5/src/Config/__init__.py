from dataclasses import dataclass
from dotenv import load_dotenv
import os
load_dotenv()
@dataclass
class Config:
    openai_api_key:str= os.getenv("OPENAI_API_KEY")
    openai_model:str= os.getenv("OPENAI_API_MODEL")