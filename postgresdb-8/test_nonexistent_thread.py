import asyncio
import httpx

async def test_nonexistent_thread():
    async with httpx.AsyncClient() as client:
        # Test GET non-existent thread
        resp = await client.get('http://localhost:8000/api/v1/chat/threads/00000000-0000-0000-0000-000000000001')
        print(f'GET Status: {resp.status_code}')
        print(f'GET Response: {resp.json()}')
        print()
        
        # Test DELETE non-existent thread
        resp2 = await client.delete('http://localhost:8000/api/v1/chat/threads/00000000-0000-0000-0000-000000000002')
        print(f'DELETE Status: {resp2.status_code}')
        print(f'DELETE Response: {resp2.json()}')

if __name__ == "__main__":
    asyncio.run(test_nonexistent_thread())
