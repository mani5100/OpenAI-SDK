"""
PostGresDB-8 package for OpenAI Agents SDK integration.

This package contains the FastAPI application and CLI tools.
"""

# Note: The old CLI agent code has been commented out as it's not used by FastAPI
# To run the CLI version, uncomment the code below and run: python -m postgresdb_8

# from .config import openai_model, Config
# from agents import Agent, Runner
# from agents.extensions.memory import SQLAlchemySession
# import asyncio
# import uuid
#
# async def agent_main():
#     user_id = str(uuid.uuid4())
#     session = SQLAlchemySession.from_url(
#         user_id,
#         url=Config.POSTGRES_URL,
#         create_tables=True
#     )
#     agent = Agent(
#         "Helpful assistant",
#         model=openai_model,
#         instructions="You are a helpful assistant."
#     )
#     response = await Runner.run(
#         agent,
#         input="Do you really know about my University?",
#         session=session
#     )
#     print(response.final_output)
#
# def main():
#     asyncio.run(agent_main())
#
# if __name__ == "__main__":
#     asyncio.run(main())
