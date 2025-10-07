from dotenv import load_dotenv
load_dotenv()
from agents import (
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    set_default_openai_client,
    function_tool,
    Agent,
    Runner,
    ModelSettings,
    enable_verbose_stdout_logging
)
external_client=AsyncOpenAI()
model=OpenAIChatCompletionsModel(
    'gpt-3.5-turbo',
    external_client
)
# set_tracing_disabled(True)
set_default_openai_client(external_client)
enable_verbose_stdout_logging()

@function_tool
def addition(a:int,b:int)->int:
    """This tool takes 2 values and add them and return it"""
    return a+b

@function_tool
def multiply(a:int,b:int)->int:
    """This tool takes 2 values and multiply them and return it"""
    return a*b

agent=Agent(
    "Assistant",
    tools=[addition,multiply],
    model=model,
    model_settings=ModelSettings(temperature=0.2)
)

def main():
    response=Runner.run_sync(agent,input="What  is the the answer of 2 + 2 x 8")
    print(response.final_output)

if __name__ == "__main__":
    main()