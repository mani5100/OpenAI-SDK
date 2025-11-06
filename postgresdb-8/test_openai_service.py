"""Test OpenAI service integration."""
import asyncio
import sys

sys.path.insert(0, 'src')

from postgresdb_8.config.settings import Settings
from postgresdb_8.services.openai_service import get_openai_service


async def test_openai_service():
    """Test OpenAI service methods."""
    print("🤖 Testing OpenAI Service Integration\n")
    
    try:
        # Initialize service
        settings = Settings()
        openai_service = get_openai_service(settings)
        print(f"✅ OpenAI service initialized")
        print(f"   Model: {settings.OPENAI_CHAT_MODEL}")
        print(f"   Assistant: {settings.OPENAI_ASSISTANT_NAME}\n")
        
        # Test 1: Get or create assistant
        print("📝 Test 1: Get/Create Assistant...")
        assistant = await openai_service.get_or_create_assistant()
        print(f"✅ Assistant ID: {assistant.id}")
        print(f"   Name: {assistant.name}")
        print(f"   Model: {assistant.model}\n")
        
        # Test 2: Create thread
        print("🧵 Test 2: Create Thread...")
        thread = await openai_service.create_thread()
        print(f"✅ Thread ID: {thread.id}\n")
        
        # Test 3: Send message
        print("💬 Test 3: Send Message...")
        test_message = "Hello! Can you help me with Python programming?"
        message = await openai_service.send_message(
            thread_id=thread.id,
            content=test_message
        )
        print(f"✅ Message sent: {message.id}")
        print(f"   Content: '{test_message}'\n")
        
        # Test 4: Non-streaming response
        print("🔄 Test 4: Get Non-Streaming Response...")
        response = await openai_service.get_response_non_streaming(
            thread_id=thread.id,
            user_message="Tell me one interesting fact about Python in one sentence."
        )
        print(f"✅ Response received:")
        print(f"   Content: {response['content'][:100]}...")
        print(f"   Tokens - Prompt: {response['usage']['prompt_tokens']}, "
              f"Completion: {response['usage']['completion_tokens']}, "
              f"Total: {response['usage']['total_tokens']}\n")
        
        # Test 5: Get thread messages
        print("📋 Test 5: Retrieve Thread History...")
        messages = await openai_service.get_thread_messages(thread.id)
        print(f"✅ Retrieved {len(messages)} messages:")
        for i, msg in enumerate(messages[:5], 1):  # Show first 5
            role = msg.role
            content = ""
            if msg.content:
                for content_block in msg.content:
                    if hasattr(content_block, 'text') and content_block.text:
                        content = content_block.text.value[:50]
            print(f"   {i}. [{role}] {content}...")
        print()
        
        # Test 6: Streaming response
        print("⚡ Test 6: Test Streaming Response...")
        print("Assistant: ", end="", flush=True)
        
        # Send a new message first
        await openai_service.send_message(
            thread_id=thread.id,
            content="Count from 1 to 5, one number per line."
        )
        
        full_response = ""
        token_usage = None
        
        async for event in openai_service.run_assistant_streaming(thread.id):
            if event["type"] == "text_delta":
                delta = event["delta"]
                print(delta, end="", flush=True)
                full_response += delta
            elif event["type"] == "run_completed":
                token_usage = event["usage"]
            elif event["type"] == "error":
                print(f"\n❌ Error: {event['message']}")
                break
        
        print()  # New line after streaming
        if token_usage:
            print(f"✅ Streaming completed")
            print(f"   Tokens - Total: {token_usage['total_tokens']}\n")
        
        # Test 7: Delete thread
        print("🗑️  Test 7: Delete Thread...")
        deleted = await openai_service.delete_thread(thread.id)
        print(f"✅ Thread deleted: {deleted}\n")
        
        print("✨ All OpenAI service tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await openai_service.close()


if __name__ == "__main__":
    asyncio.run(test_openai_service())
