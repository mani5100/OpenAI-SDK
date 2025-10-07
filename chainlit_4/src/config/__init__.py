from dotenv import load_dotenv
import os
from dataclasses import dataclass

load_dotenv()

# if using gemini baseurl and api ey we have to do the same.
@dataclass
class Config:
    openai_api_key:str=os.getenv("OPENAI_API_KEY")
    openai_api_model:str=os.getenv("OPENAI_API_MODEL")