"""
End-to-end test for the complete chatbot workflow.

This script tests the entire chatbot workflow:
1. Send message (auto-create thread)
2. Send follow-up message to existing thread
3. Retrieve thread history
4. List all threads
5. Delete thread
6. Verify deletion
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import httpx


class EndToEndTester:
    """End-to-end testing for the chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.thread_id = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "steps": []
        }
    
    async def cleanup(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def log_step(self, step_name: str, passed: bool, details: str = ""):
        """Log test step result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {step_name}")
        if details:
            print(f"   {details}")
        
        self.test_results["steps"].append({
            "name": step_name,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    async def step_1_send_first_message(self):
        """Step 1: Send first message (auto-create thread)."""
        print("\n" + "="*60)
        print("STEP 1: Send First Message (Auto-create Thread)")
        print("="*60)
        
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={
                "message": "Hello! Can you explain what FastAPI is in one sentence?",
                "stream": False
            }
        )
        
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            self.thread_id = data.get("thread_id")
            
            # Validate response structure
            has_thread_id = "thread_id" in data
            has_user_message = "user_message" in data
            has_assistant_message = "assistant_message" in data
            has_total_tokens = "total_tokens" in data
            
            structure_valid = all([has_thread_id, has_user_message, has_assistant_message, has_total_tokens])
            
            if structure_valid:
                print(f"   Thread ID: {self.thread_id}")
                print(f"   User Message: {data['user_message']['content'][:50]}...")
                print(f"   Assistant Response: {data['assistant_message']['content'][:80]}...")
                print(f"   Total Tokens: {data['total_tokens']}")
                
                self.log_step(
                    "Send first message",
                    True,
                    f"Thread created: {self.thread_id}, Tokens: {data['total_tokens']}"
                )
            else:
                self.log_step("Send first message", False, "Invalid response structure")
        else:
            self.log_step(
                "Send first message",
                False,
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
    
    async def step_2_send_followup_message(self):
        """Step 2: Send follow-up message to existing thread."""
        print("\n" + "="*60)
        print("STEP 2: Send Follow-up Message (Existing Thread)")
        print("="*60)
        
        if not self.thread_id:
            self.log_step("Send follow-up message", False, "No thread ID from step 1")
            return
        
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={
                "message": "What are the main benefits of using FastAPI?",
                "thread_id": self.thread_id,
                "stream": False
            }
        )
        
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            
            # Verify same thread ID
            same_thread = data.get("thread_id") == self.thread_id
            
            if same_thread:
                print(f"   Thread ID: {data['thread_id']} (matches)")
                print(f"   User Message: {data['user_message']['content'][:50]}...")
                print(f"   Assistant Response: {data['assistant_message']['content'][:80]}...")
                print(f"   Total Tokens: {data['total_tokens']}")
                
                self.log_step(
                    "Send follow-up message",
                    True,
                    f"Same thread used, Tokens: {data['total_tokens']}"
                )
            else:
                self.log_step(
                    "Send follow-up message",
                    False,
                    f"Thread ID mismatch: expected {self.thread_id}, got {data.get('thread_id')}"
                )
        else:
            self.log_step(
                "Send follow-up message",
                False,
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
    
    async def step_3_retrieve_thread_history(self):
        """Step 3: Retrieve complete thread history."""
        print("\n" + "="*60)
        print("STEP 3: Retrieve Thread History")
        print("="*60)
        
        if not self.thread_id:
            self.log_step("Retrieve thread history", False, "No thread ID from step 1")
            return
        
        response = await self.client.get(
            f"{self.base_url}/chat/threads/{self.thread_id}"
        )
        
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            
            # Validate structure
            has_messages = "messages" in data
            message_count = len(data.get("messages", []))
            
            # We sent 2 messages, so we should have 4 total (2 user + 2 assistant)
            expected_messages = 4
            correct_count = message_count == expected_messages
            
            if has_messages and correct_count:
                print(f"   Thread ID: {data.get('thread_id')}")
                print(f"   Message Count: {message_count}")
                print(f"   Total Tokens: {data.get('total_tokens', 0)}")
                print(f"\n   Message History:")
                for i, msg in enumerate(data['messages'], 1):
                    role = msg['role']
                    content = msg['content'][:60]
                    tokens = msg.get('total_tokens', 0)
                    print(f"      {i}. [{role.upper()}] {content}... (tokens: {tokens})")
                
                self.log_step(
                    "Retrieve thread history",
                    True,
                    f"{message_count} messages retrieved"
                )
            else:
                self.log_step(
                    "Retrieve thread history",
                    False,
                    f"Expected {expected_messages} messages, got {message_count}"
                )
        else:
            self.log_step(
                "Retrieve thread history",
                False,
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
    
    async def step_4_list_threads(self):
        """Step 4: List all threads with pagination."""
        print("\n" + "="*60)
        print("STEP 4: List All Threads (Paginated)")
        print("="*60)
        
        response = await self.client.get(
            f"{self.base_url}/chat/threads?page=1&page_size=10"
        )
        
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            
            # Validate structure
            has_threads = "threads" in data
            has_pagination = all(k in data for k in ["total", "page", "page_size", "total_pages"])
            
            if has_threads and has_pagination:
                thread_count = len(data["threads"])
                total = data["total"]
                
                print(f"   Total Threads: {total}")
                print(f"   Returned: {thread_count}")
                print(f"   Page: {data['page']} of {data['total_pages']}")
                
                # Check if our thread is in the list
                our_thread_found = any(
                    t.get("thread_id") == self.thread_id 
                    for t in data["threads"]
                )
                
                if our_thread_found:
                    print(f"   ✓ Our thread ({self.thread_id}) found in list")
                
                self.log_step(
                    "List threads",
                    True,
                    f"{thread_count} threads listed, our thread {'found' if our_thread_found else 'NOT found'}"
                )
            else:
                self.log_step(
                    "List threads",
                    False,
                    "Invalid response structure"
                )
        else:
            self.log_step(
                "List threads",
                False,
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
    
    async def step_5_delete_thread(self):
        """Step 5: Delete the thread."""
        print("\n" + "="*60)
        print("STEP 5: Delete Thread")
        print("="*60)
        
        if not self.thread_id:
            self.log_step("Delete thread", False, "No thread ID from step 1")
            return
        
        response = await self.client.delete(
            f"{self.base_url}/chat/threads/{self.thread_id}"
        )
        
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            
            success = data.get("success", False)
            deleted_id = data.get("thread_id")
            
            if success and deleted_id == self.thread_id:
                print(f"   Thread Deleted: {deleted_id}")
                print(f"   Success: {success}")
                
                self.log_step(
                    "Delete thread",
                    True,
                    f"Thread {self.thread_id} deleted successfully"
                )
            else:
                self.log_step(
                    "Delete thread",
                    False,
                    f"Unexpected response: {data}"
                )
        else:
            self.log_step(
                "Delete thread",
                False,
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
    
    async def step_6_verify_deletion(self):
        """Step 6: Verify thread is deleted."""
        print("\n" + "="*60)
        print("STEP 6: Verify Thread Deletion")
        print("="*60)
        
        if not self.thread_id:
            self.log_step("Verify deletion", False, "No thread ID from step 1")
            return
        
        response = await self.client.get(
            f"{self.base_url}/chat/threads/{self.thread_id}"
        )
        
        # Should return 404 since thread was deleted
        passed = response.status_code == 404
        
        if passed:
            print(f"   Thread not found (as expected): {self.thread_id}")
            self.log_step(
                "Verify deletion",
                True,
                "Thread properly deleted (404 returned)"
            )
        else:
            self.log_step(
                "Verify deletion",
                False,
                f"Expected 404, got {response.status_code}"
            )
    
    async def step_7_test_streaming(self):
        """Step 7: Test streaming response."""
        print("\n" + "="*60)
        print("STEP 7: Test Streaming Response")
        print("="*60)
        
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={
                "message": "What is Python? (Keep it brief)",
                "stream": True
            }
        )
        
        passed = response.status_code == 200
        
        if passed:
            # Check content type
            content_type = response.headers.get("content-type", "")
            is_sse = "text/event-stream" in content_type
            
            if is_sse:
                print(f"   Content-Type: {content_type}")
                print(f"   Streaming events received:")
                
                # Read first few events
                event_count = 0
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        print(f"      - Event: {event_type}")
                        event_count += 1
                        
                        # Stop after a few events to not consume too much
                        if event_count >= 5:
                            break
                
                self.log_step(
                    "Test streaming",
                    True,
                    f"SSE streaming working, {event_count}+ events received"
                )
            else:
                self.log_step(
                    "Test streaming",
                    False,
                    f"Expected SSE, got {content_type}"
                )
        else:
            self.log_step(
                "Test streaming",
                False,
                f"HTTP {response.status_code}: {response.text[:100]}"
            )
    
    def print_summary(self):
        """Print test summary."""
        total = self.test_results["passed"] + self.test_results["failed"]
        
        print("\n" + "="*60)
        print("END-TO-END TEST SUMMARY")
        print("="*60)
        print(f"Total steps: {total}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"Success rate: {(self.test_results['passed'] / total * 100):.1f}%")
        
        if self.test_results["failed"] > 0:
            print("\nFailed steps:")
            for step in self.test_results["steps"]:
                if not step["passed"]:
                    print(f"  - {step['name']}: {step['details']}")
        
        print("="*60)
        
        return self.test_results["failed"] == 0


async def main():
    """Run end-to-end test workflow."""
    print("="*60)
    print("CHATBOT API END-TO-END TEST")
    print("="*60)
    print("Testing complete chatbot workflow...")
    
    # Check if API is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health/live", timeout=5.0)
            if response.status_code != 200:
                print("\n❌ ERROR: API is not responding properly")
                print("Please ensure the API is running: uvicorn src.postgresdb_8.main:app --host 0.0.0.0 --port 8000")
                return False
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to API at http://localhost:8000")
        print(f"Error: {e}")
        print("\nPlease ensure the API is running: uvicorn src.postgresdb_8.main:app --host 0.0.0.0 --port 8000")
        return False
    
    print("✅ API is running\n")
    
    # Run end-to-end test
    tester = EndToEndTester()
    
    try:
        # Execute workflow steps in order
        await tester.step_1_send_first_message()
        await tester.step_2_send_followup_message()
        await tester.step_3_retrieve_thread_history()
        await tester.step_4_list_threads()
        await tester.step_5_delete_thread()
        await tester.step_6_verify_deletion()
        await tester.step_7_test_streaming()
        
        # Print summary
        success = tester.print_summary()
        
        return success
        
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
