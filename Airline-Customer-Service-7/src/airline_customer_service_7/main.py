"""
Multi-Agent Airline Customer Service System - Starter Code

Fill in the missing implementations following the assignment instructions.
"""

from __future__ import annotations as _annotations

import asyncio
import random
import uuid
from pydantic import BaseModel
from agents import (
    Agent,
    HandoffOutputItem,
    ItemHelpers,
    MessageOutputItem,
    RunContextWrapper,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
    function_tool,
    handoff,
    trace,
    OpenAIChatCompletionsModel,
    AsyncOpenAI
)
from dotenv import load_dotenv
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


load_dotenv()


model=OpenAIChatCompletionsModel(
    "gpt-4o",
    openai_client=AsyncOpenAI()
)

# TODO: Implement the AirlineAgentContext Pydantic model
# Requirements:
# - Inherit from BaseModel
# - Add passenger_name: str | None = None
# - Add confirmation_number: str | None = None
# - Add seat_number: str | None = None
# - Add flight_number: str | None = None

class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None




# TODO: Implement the FAQ lookup tool
# Requirements:
# - Use @function_tool decorator with name_override and description_override
# - Check for keywords: "bag", "baggage", "luggage", "carry-on", "seat", "wifi", etc.
# - Return appropriate responses for each category
# - Return fallback message for unknown topics


@function_tool(
    name_override="faq_lookup_tool", description_override="Lookup frequently asked questions."
)
async def faq_lookup_tool(ctx:RunContextWrapper[AirlineAgentContext],question: str) -> str:
    # TODO: Implement the FAQ lookup logic
    # Hint: Use question.lower() to make it case-insensitive
    # Check for keyword categories and return appropriate responses
    if "bag" in question.lower().split():
        return "You can get your bags from counter A."
    elif "baggage" in question.lower().split():
        return "You can get your baggage from counter B."
    elif "luggage" in question.lower().split():
        return "You can get your luggage from counter C."
    elif "carry-on" in question.lower().split():
        return "You can get your carry-on from counter D."
    elif "seat" in question.lower().split():
        return f"Your seat number is {ctx.context.seat_number}"
    elif "wifi" in question.lower().split():
        return "You can ask the attendent for wifi password."
    else:
        return "You can go to Counter E for general queries."


# TODO: Implement the update_seat tool
# Requirements:
# - Use @function_tool decorator
# - Accept context, confirmation_number, and new_seat parameters
# - Update context.context.confirmation_number and context.context.seat_number
# - Assert that flight_number exists
# - Return a confirmation message


@function_tool
async def update_seat(
    context: RunContextWrapper[AirlineAgentContext],confirmation_number: str,new_seat: str,passenger_name: str,
) -> str:
    """
    Update the seat for a given confirmation number.

    Args:
        context: The run context containing shared state
        confirmation_number: The confirmation number for the flight
        new_seat: The new seat to update to
        name: The name of passenger
    """
    assert context.context.flight_number is not None, "Flight details are missing. Please complete a booking first."

    context.context.confirmation_number = confirmation_number
    context.context.seat_number = new_seat
    if passenger_name:
        context.context.passenger_name = passenger_name

    return (
        f"Seat updated to {new_seat} for confirmation {confirmation_number}. "
        "Let me know if you need anything else."
    )
    


# TODO: Implement the on_seat_booking_handoff hook
# Requirements:
# - Accept RunContextWrapper[AirlineAgentContext] as parameter
# - Generate a random flight number (format: "FLT-XXX" where XXX is 100-999)
# - Update context.context.flight_number
# - Return None


async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    flight_number = f"FLT-{random.randint(100, 999)}"
    context.context.flight_number = flight_number


# TODO: Implement the FAQ Agent
# Requirements:
# - Name: "FAQ Agent"
# - Appropriate handoff_description
# - Instructions that include RECOMMENDED_PROMPT_PREFIX
# - Add the FAQ lookup tool to tools list
# - Add Triage Agent to handoffs list

faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    model=model,
    # TODO: Add handoff_description
    handoff_description="This FAQ agent is for general questions and FAQ about airline policies",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a FAQ Agent. When a User asks about "bag", "baggage", "luggage", "carry-on", "seat", "wifi", etc or general questions you have to use \
        faq_lookup_tool to find the answer. After answering the question ask them if they have any further question.
        If the query is related to services like seat booking, handoff them to the Triage Agent.
    """,
    tools=[faq_lookup_tool],  # TODO: Add faq_lookup_tool
    handoffs=[],  # TODO: Add triage_agent
)

# TODO: Implement the Seat Booking Agent
# Requirements:
# - Name: "Seat Booking Agent"
# - Appropriate handoff_description
# - Instructions that include RECOMMENDED_PROMPT_PREFIX
# - Add the update_seat tool to tools list
# - Add Triage Agent to handoffs list
# - Connect to the on_seat_booking_handoff hook using handoff()

seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",
    model=model,
    handoff_description="This Seat Booking Agent agent is for booking the seat in flight.",
    # TODO: Add handoff_description
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a Seat Booking Agent responsible for helping passengers update their seat assignments.
    When a customer wants to change their seat or book a seat, first ask them for their name and confirmation number. Then ask them which new seat they would like. Once you have both pieces of information, use the update_seat tool to process the request. 
    After successfully updating the seat, confirm the change with the customer and ask if they need anything else. If they have questions outside of seat booking, transfer them back to the Triage Agent.
    """,
    tools=[update_seat],  # TODO: Add update_seat tool
    handoffs=[],  # TODO: Add handoff with on_seat_booking_handoff hook
)

# TODO: Implement the Triage Agent
# Requirements:
# - Name: "Triage Agent"
# - Appropriate handoff_description
# - Instructions that include RECOMMENDED_PROMPT_PREFIX
# - No tools
# - Handoffs to FAQ Agent and Seat Booking Agent (with hook)

triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    model=model,
    # TODO: Add handoff_description
    handoff_description="This Triage agent acts as a router agent. It understands the query and gives control to the following agent.",
    instructions=(
        f"""{RECOMMENDED_PROMPT_PREFIX} \
        You are the airline triage specialist. Listen to the traveler's request and decide which teammate should help.\n\
        - For policy questions about bags, luggage, carry-ons, seats, Wi-Fi, or other FAQs, hand off to the FAQ Agent.\n\
        - For seat assignment or changes, hand off to the Seat Booking Agent (this will also assign a flight number).\n\
        - If a conversation returns to you, greet the traveler and route them again if needed."""
    ),
    tools=[],  # Triage agent has no tools
    handoffs=[handoff(seat_booking_agent, on_handoff=on_seat_booking_handoff), faq_agent],  # TODO: Add faq_agent and seat_booking_agent with handoff hook
)

# Setup bidirectional handoffs
faq_agent.handoffs.append(triage_agent)
seat_booking_agent.handoffs.append(triage_agent)


def main():
    """
    Main function to run the interactive loop.
    
    TODO: Implement the main loop that:
    1. Starts with triage_agent
    2. Maintains input_items list
    3. Creates AirlineAgentContext instance
    4. Generates conversation_id
    5. Loops while True:
       - Gets user input
       - Wraps in trace()
       - Runs agent with Runner.run()
       - Displays all output items
       - Updates current_agent and input_items
    """
    current_agent: Agent[AirlineAgentContext] = triage_agent
    input_items: list[TResponseInputItem] = []
    context=AirlineAgentContext()

    # TODO: Generate a conversation ID using uuid
    conversation_id = str(uuid.uuid4())

    while True:
        # TODO: Get user input
        user_input = input("Enter your message: ")
        user_item={
            "role":"user",
            "content": user_input
        }
        # TODO: Wrap in trace() with group_id
        with trace("Customer service", group_id=conversation_id):
            # TODO: Add input to input_items
            input_items.append(user_item)
            # TODO: Run the agent
            result = Runner.run_sync(
                starting_agent=current_agent,
                input=input_items,
                context=context,
                conversation_id=conversation_id
            )

            # TODO: Display output items
            for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):
                    print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
                elif isinstance(new_item, HandoffOutputItem):
                    source=new_item.agent.name
                    target=new_item.target_agent.name
                    print(f"Handoff from {source}->{target}")
                    # TODO: Display handoff information
                elif isinstance(new_item, ToolCallItem):
                    tool_name = new_item.name
                    tool_args = new_item.arguments
                    print(f"{agent_name}: Calling tool '{tool_name}' with arguments: {tool_args}")
                elif isinstance(new_item, ToolCallOutputItem):
                    print(f"{agent_name}: Tool Output '{new_item.output}'")
                    # TODO: Display tool output
                else:
                    print(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")
            
            # TODO: Update input_items and current_agent
            input_items = result.to_input_list()
            print(input_items)
            current_agent = result.last_agent



if __name__ == "__main__":
    asyncio.run(main())
