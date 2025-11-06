"""Test script for Chat API endpoints."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"


async def test_chat_endpoints():
    """Test all chat endpoints."""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Testing Chat API Endpoints")
        print("=" * 60)
        
        # Test 1: Send message without thread_id (auto-create)
        print("\n1️⃣ Test: Send message (auto-create thread)")
        try:
            response = await client.post(
                f"{BASE_URL}/chat/message",
                json={
                    "message": "Hello! What is Python?",
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Thread ID: {result['thread_id']}")
            print(f"   User message: {result['user_message']['content'][:50]}...")
            print(f"   Assistant response: {result['assistant_message']['content'][:100]}...")
            print(f"   Total tokens: {result['total_tokens']}")
            thread_id = result['thread_id']
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # Test 2: Send another message to existing thread
        print("\n2️⃣ Test: Send message to existing thread")
        try:
            response = await client.post(
                f"{BASE_URL}/chat/message",
                json={
                    "message": "Can you explain async/await?",
                    "thread_id": thread_id,
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Assistant response: {result['assistant_message']['content'][:100]}...")
            print(f"   Total tokens: {result['total_tokens']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Get thread history
        print(f"\n3️⃣ Test: Get thread history")
        try:
            response = await client.get(f"{BASE_URL}/chat/threads/{thread_id}")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Thread ID: {result['thread_id']}")
            print(f"   Message count: {result['message_count']}")
            print(f"   Total tokens: {result['total_tokens']}")
            print(f"   Messages: {len(result['messages'])}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: List all threads
        print(f"\n4️⃣ Test: List all threads")
        try:
            response = await client.get(f"{BASE_URL}/chat/threads?page=1&page_size=10")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Total threads: {result['total']}")
            print(f"   Page: {result['page']}/{result['total_pages']}")
            print(f"   Threads on page: {len(result['threads'])}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Delete thread
        print(f"\n5️⃣ Test: Delete thread")
        try:
            response = await client.delete(f"{BASE_URL}/chat/threads/{thread_id}")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Success: {result['success']}")
            print(f"   Message: {result['message']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 6: Verify thread is deleted
        print(f"\n6️⃣ Test: Verify thread deletion")
        try:
            response = await client.get(f"{BASE_URL}/chat/threads/{thread_id}")
            if response.status_code == 404:
                print(f"✅ Thread correctly deleted (404)")
            else:
                print(f"❌ Thread still exists! Status: {response.status_code}")
        except Exception as e:
            print(f"✅ Thread correctly deleted (exception: {type(e).__name__})")
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_chat_endpoints())
