import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        r = await client.get('http://localhost:8000/chat/threads/thread_nonexistent123')
        print(f'Status: {r.status_code}')
        print(f'Response: {r.json()}')

asyncio.run(main())
