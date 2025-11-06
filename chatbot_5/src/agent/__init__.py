from agents import (
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    set_default_openai_client,
    Agent,
    function_tool,
    enable_verbose_stdout_logging
)
from Config import Config
def create_agent()->Agent:
    external_client=AsyncOpenAI(
        api_key=Config.openai_api_key
    )
    enable_verbose_stdout_logging()
    set_default_openai_client(external_client)
    
    @function_tool
    def add(a:float,b:float)->float:
        """This tool is used to add 2 numbers"""
        print(f"ADD TOOL CALLED: {a} + {b}")
        return a+b
    
    @function_tool
    def subtract(a:float,b:float)->float:
        """This tool is used to subtract 2 numbers"""
        print(f"Subtract TOOL CALLED: {a} - {b}")
        return a-b
    
    @function_tool
    def multiply(a:float,b:float)->float:
        """This tool is used to multiply 2 numbers"""
        print(f"Multiply TOOL CALLED: {a} x {b}")
        return a*b
    
    @function_tool
    def divide(a:float,b:float)->float:
        """This tool is used to divide 2 numbers"""
        print(f"Divide TOOL CALLED: {a} / {b}")
        return a/b
    
    model=OpenAIChatCompletionsModel(
        model=Config.openai_model,
        openai_client=external_client,
    )
    agent=Agent(
        name="Assitant",
        instructions="""You are a helpful Assistant. 
    IMPORTANT: You MUST use the available tools (add, subtract, multiply, divide) for ALL mathematical calculations.
    Never calculate numbers yourself - always use the appropriate tool.
    When you see a math problem, identify the operation needed and use the corresponding tool.""",
        model=model,
        tools=[add,subtract,multiply,divide]
    )
    return agent