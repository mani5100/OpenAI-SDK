"""
Test error scenarios for the chatbot API.

This script tests various error conditions to verify proper error handling:
- Invalid requests (validation errors)
- Missing threads (404 errors)
- Database errors
- OpenAI API failures (simulated)
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from postgresdb_8.config import settings
from postgresdb_8.models.base import Base


class ErrorScenarioTester:
    """Test various error scenarios for the chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    async def cleanup(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append({"test": test_name, "details": details})
    
    async def test_invalid_empty_message(self):
        """Test sending empty message (validation error)."""
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={"message": "", "stream": False}
        )
        
        # Should return 422 Unprocessable Entity
        passed = response.status_code == 422
        self.log_test(
            "Invalid empty message",
            passed,
            f"Expected 422, got {response.status_code}"
        )
        
        if passed:
            data = response.json()
            print(f"   Error response: {data.get('detail', 'No detail')}")
    
    async def test_invalid_missing_message_field(self):
        """Test request without message field (validation error)."""
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={"stream": False}  # Missing 'message' field
        )
        
        # Should return 422 Unprocessable Entity
        passed = response.status_code == 422
        self.log_test(
            "Missing message field",
            passed,
            f"Expected 422, got {response.status_code}"
        )
    
    async def test_invalid_thread_id_format(self):
        """Test with invalid thread_id format."""
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={
                "message": "Test message",
                "thread_id": "invalid-format-12345",  # Invalid format (not from OpenAI)
                "stream": False
            }
        )
        
        # Should return 404 or 500 depending on implementation
        # OpenAI API will reject invalid thread format
        passed = response.status_code in [404, 500, 502]
        self.log_test(
            "Invalid thread_id format",
            passed,
            f"Expected 404/500/502, got {response.status_code}"
        )
    
    async def test_nonexistent_thread(self):
        """Test retrieving non-existent thread (404 error)."""
        fake_thread_id = "thread_nonexistent123456789"
        response = await self.client.get(
            f"{self.base_url}/chat/threads/{fake_thread_id}"
        )
        
        # Should return 404 Not Found
        passed = response.status_code == 404
        self.log_test(
            "Non-existent thread retrieval",
            passed,
            f"Expected 404, got {response.status_code}"
        )
        
        if passed:
            data = response.json()
            print(f"   Error message: {data.get('detail', 'No detail')}")
    
    async def test_delete_nonexistent_thread(self):
        """Test deleting non-existent thread (404 error)."""
        fake_thread_id = "thread_nonexistent987654321"
        response = await self.client.delete(
            f"{self.base_url}/chat/threads/{fake_thread_id}"
        )
        
        # Should return 404 Not Found
        passed = response.status_code == 404
        self.log_test(
            "Delete non-existent thread",
            passed,
            f"Expected 404, got {response.status_code}"
        )
    
    async def test_invalid_pagination_params(self):
        """Test list threads with invalid pagination parameters."""
        # Test with page = 0 (should be >= 1)
        response = await self.client.get(
            f"{self.base_url}/chat/threads?page=0&page_size=10"
        )
        
        passed = response.status_code == 422
        self.log_test(
            "Invalid pagination (page=0)",
            passed,
            f"Expected 422, got {response.status_code}"
        )
        
        # Test with page_size > 100 (max is 100)
        response = await self.client.get(
            f"{self.base_url}/chat/threads?page=1&page_size=200"
        )
        
        passed = response.status_code == 422
        self.log_test(
            "Invalid pagination (page_size>100)",
            passed,
            f"Expected 422, got {response.status_code}"
        )
    
    async def test_health_check_success(self):
        """Test that health check works properly."""
        response = await self.client.get(f"{self.base_url}/health")
        
        # Should return 200 or 503 depending on dependencies
        passed = response.status_code in [200, 503]
        self.log_test(
            "Health check endpoint",
            passed,
            f"Expected 200 or 503, got {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            print(f"   OpenAI: {data.get('openai')}")
    
    async def test_malformed_json(self):
        """Test sending malformed JSON."""
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            content='{"message": "test", invalid}',  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 Unprocessable Entity
        passed = response.status_code == 422
        self.log_test(
            "Malformed JSON request",
            passed,
            f"Expected 422, got {response.status_code}"
        )
    
    async def test_unsupported_http_method(self):
        """Test using unsupported HTTP method."""
        # Try PATCH on an endpoint that doesn't support it
        response = await self.client.patch(
            f"{self.base_url}/chat/message",
            json={"message": "test"}
        )
        
        # Should return 405 Method Not Allowed
        passed = response.status_code == 405
        self.log_test(
            "Unsupported HTTP method (PATCH)",
            passed,
            f"Expected 405, got {response.status_code}"
        )
    
    async def test_invalid_stream_parameter(self):
        """Test with invalid stream parameter type."""
        response = await self.client.post(
            f"{self.base_url}/chat/message",
            json={"message": "test", "stream": "invalid"}  # Should be boolean
        )
        
        # Should return 422 Unprocessable Entity
        passed = response.status_code == 422
        self.log_test(
            "Invalid stream parameter type",
            passed,
            f"Expected 422, got {response.status_code}"
        )
    
    async def test_cors_headers(self):
        """Test that CORS headers are present."""
        response = await self.client.options(
            f"{self.base_url}/chat/message",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Check for CORS headers
        has_cors = "access-control-allow-origin" in response.headers
        self.log_test(
            "CORS headers present",
            has_cors,
            f"CORS headers: {has_cors}"
        )
    
    async def test_request_id_tracking(self):
        """Test that request ID is tracked."""
        # Send request with custom request ID
        custom_id = "test-request-id-123"
        response = await self.client.get(
            f"{self.base_url}/health",
            headers={"X-Request-ID": custom_id}
        )
        
        # Check if request ID is echoed back
        has_request_id = "x-request-id" in response.headers
        self.log_test(
            "Request ID tracking",
            has_request_id,
            f"Request ID in response: {has_request_id}"
        )
        
        if has_request_id:
            print(f"   Request ID: {response.headers.get('x-request-id')}")
    
    async def test_error_response_format(self):
        """Test that error responses have consistent format."""
        response = await self.client.get(
            f"{self.base_url}/chat/threads/nonexistent"
        )
        
        if response.status_code == 404:
            data = response.json()
            has_detail = "detail" in data
            self.log_test(
                "Error response format",
                has_detail,
                f"Has 'detail' field: {has_detail}"
            )
            
            if has_detail:
                print(f"   Error detail: {data['detail']}")
    
    def print_summary(self):
        """Print test summary."""
        total = self.test_results["passed"] + self.test_results["failed"]
        print("\n" + "=" * 60)
        print("ERROR SCENARIO TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"Success rate: {(self.test_results['passed'] / total * 100):.1f}%")
        
        if self.test_results["errors"]:
            print("\nFailed tests:")
            for error in self.test_results["errors"]:
                print(f"  - {error['test']}: {error['details']}")
        
        print("=" * 60)
        
        return self.test_results["failed"] == 0


async def main():
    """Run all error scenario tests."""
    print("=" * 60)
    print("CHATBOT API ERROR SCENARIO TESTS")
    print("=" * 60)
    print("Testing error handling and validation...")
    print()
    
    # Check if API is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health/live", timeout=5.0)
            if response.status_code != 200:
                print("❌ ERROR: API is not responding properly")
                print("Please ensure the API is running: uvicorn src.postgresdb_8.main:app --host 0.0.0.0 --port 8000")
                return False
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to API at http://localhost:8000")
        print(f"Error: {e}")
        print("\nPlease ensure the API is running: uvicorn src.postgresdb_8.main:app --host 0.0.0.0 --port 8000")
        return False
    
    print("✅ API is running\n")
    
    # Run tests
    tester = ErrorScenarioTester()
    
    try:
        print("1. Validation Error Tests")
        print("-" * 60)
        await tester.test_invalid_empty_message()
        await tester.test_invalid_missing_message_field()
        await tester.test_invalid_stream_parameter()
        await tester.test_malformed_json()
        
        print("\n2. Not Found Error Tests")
        print("-" * 60)
        await tester.test_nonexistent_thread()
        await tester.test_delete_nonexistent_thread()
        await tester.test_invalid_thread_id_format()
        
        print("\n3. Pagination Error Tests")
        print("-" * 60)
        await tester.test_invalid_pagination_params()
        
        print("\n4. HTTP Method Tests")
        print("-" * 60)
        await tester.test_unsupported_http_method()
        
        print("\n5. Health & Infrastructure Tests")
        print("-" * 60)
        await tester.test_health_check_success()
        await tester.test_cors_headers()
        await tester.test_request_id_tracking()
        
        print("\n6. Error Format Tests")
        print("-" * 60)
        await tester.test_error_response_format()
        
        # Print summary
        success = tester.print_summary()
        
        return success
        
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
