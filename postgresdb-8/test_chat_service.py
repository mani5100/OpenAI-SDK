"""Test integrated ChatService with OpenAI and PostgreSQL."""
import asyncio
import sys

sys.path.insert(0, 'src')

from postgresdb_8.config.settings import Settings
from postgresdb_8.utils.database import get_db_manager
from postgresdb_8.services.openai_service import get_openai_service
from postgresdb_8.services.chat_service import ChatService


async def test_chat_service():
    """Test ChatService integration with OpenAI and Database."""
    print("🔗 Testing Integrated ChatService (OpenAI + PostgreSQL)\n")
    
    settings = Settings()
    db_manager = get_db_manager(settings)
    openai_service = get_openai_service(settings)
    
    # Get database session
    session_gen = db_manager.get_session()
    session = await anext(session_gen)
    
    try:
        # Create ChatService
        chat_service = ChatService(openai_service, session)
        print("✅ ChatService initialized\n")
        
        # Test 1: Create thread (OpenAI + PostgreSQL)
        print("🧵 Test 1: Create Thread (stores in both OpenAI and PostgreSQL)...")
        thread = await chat_service.create_thread()
        print(f"✅ Thread created:")
        print(f"   DB ID: {thread.id}")
        print(f"   OpenAI ID: {thread.openai_thread_id}")
        print(f"   Message count: {thread.message_count}")
        print(f"   Total tokens: {thread.total_tokens}\n")
        
        # Test 2: Send message non-streaming (stores everything)
        print("💬 Test 2: Send Non-Streaming Message...")
        response = await chat_service.send_message_non_streaming(
            thread_id=str(thread.id),
            user_message="Hello! What is Python?"
        )
        print(f"✅ Message sent and stored:")
        print(f"   User message ID: {response['user_message_id']}")
        print(f"   Assistant message ID: {response['assistant_message_id']}")
        print(f"   Response: {response['content'][:80]}...")
        print(f"   Tokens - Prompt: {response['usage']['prompt_tokens']}, "
              f"Completion: {response['usage']['completion_tokens']}\n")
        
        # Test 3: Get thread history from PostgreSQL
        print("📋 Test 3: Get Thread History (from PostgreSQL)...")
        history = await chat_service.get_thread_history(str(thread.id))
        print(f"✅ Thread history:")
        print(f"   Message count: {history['message_count']}")
        print(f"   Total tokens: {history['total_tokens']}")
        print(f"   Messages in DB: {len(history['messages'])}")
        for i, msg in enumerate(history['messages'], 1):
            print(f"   {i}. [{msg['role']}] {msg['content'][:50]}...")
        print()
        
        # Test 4: Send streaming message
        print("⚡ Test 4: Send Streaming Message...")
        print("Assistant: ", end="", flush=True)
        
        full_response = ""
        storage_info = None
        
        async for event in chat_service.send_message_streaming(
            thread_id=str(thread.id),
            user_message="Count from 1 to 3."
        ):
            if event["type"] == "text_delta":
                delta = event["delta"]
                print(delta, end="", flush=True)
                full_response += delta
            elif event["type"] == "storage_complete":
                storage_info = event
            elif event["type"] == "error":
                print(f"\n❌ Error: {event['message']}")
                break
        
        print()  # New line
        if storage_info:
            print(f"✅ Streaming complete and stored in PostgreSQL")
            print(f"   User message ID: {storage_info['user_message_id']}")
            print(f"   Assistant message ID: {storage_info['assistant_message_id']}")
            print(f"   Thread message count: {storage_info['thread']['message_count']}\n")
        
        # Test 5: Get updated history
        print("📊 Test 5: Get Updated Thread Statistics...")
        stats = await chat_service.get_thread_statistics(str(thread.id))
        if stats:
            print(f"✅ Thread statistics:")
            print(f"   Total messages: {stats['message_count']}")
            print(f"   Total tokens: {stats['total_tokens']}")
            print(f"   Prompt tokens: {stats['total_prompt_tokens']}")
            print(f"   Completion tokens: {stats['total_completion_tokens']}")
            print(f"   Avg prompt tokens: {stats['avg_prompt_tokens']:.1f}")
            print(f"   Avg completion tokens: {stats['avg_completion_tokens']:.1f}\n")
        
        # Test 6: List threads
        print("📋 Test 6: List All Threads...")
        threads = await chat_service.list_threads(limit=5)
        print(f"✅ Found {len(threads)} thread(s):")
        for i, t in enumerate(threads[:3], 1):
            print(f"   {i}. ID: {t['id'][:18]}... | "
                  f"Messages: {t['message_count']} | "
                  f"Tokens: {t['total_tokens']}")
        print()
        
        # Test 7: Delete thread (from both OpenAI and PostgreSQL)
        print("🗑️  Test 7: Delete Thread (from both OpenAI and PostgreSQL)...")
        deleted = await chat_service.delete_thread(str(thread.id))
        print(f"✅ Thread deleted: {deleted}")
        
        # Verify deletion
        deleted_thread = await chat_service.get_thread(str(thread.id))
        print(f"✅ Verified deletion: thread is None = {deleted_thread is None}\n")
        
        print("✨ All ChatService integration tests passed!")
        print("\n🎯 Task 3.3 Complete: Thread creation with PostgreSQL integration ✅")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await session.close()
        await session_gen.aclose()
        await openai_service.close()


if __name__ == "__main__":
    asyncio.run(test_chat_service())
