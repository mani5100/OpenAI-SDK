"""Quick script to test database connectivity and verify tables."""
import asyncio
import sys

sys.path.insert(0, 'src')

from postgresdb_8.utils.database import get_db_manager
from postgresdb_8.config.settings import Settings
from sqlalchemy import text


async def test_database():
    """Test database connectivity and verify tables."""
    # Initialize settings first
    settings = Settings()
    db = get_db_manager(settings)
    
    # Test health check
    is_healthy = await db.health_check()
    print(f"✅ Database health check: {'PASSED' if is_healthy else 'FAILED'}")
    
    # Use session from the async generator
    session_gen = db.get_session()
    session = await anext(session_gen)
    
    try:
        # List tables
        result = await session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        )
        tables = result.fetchall()
        
        print(f"\n📋 Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check conversation_threads structure
        result = await session.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'conversation_threads'
                ORDER BY ordinal_position
            """)
        )
        columns = result.fetchall()
        
        print(f"\n🧵 conversation_threads columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check messages structure
        result = await session.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'messages'
                ORDER BY ordinal_position
            """)
        )
        columns = result.fetchall()
        
        print(f"\n💬 messages columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
    
    finally:
        await session.close()
        await session_gen.aclose()


if __name__ == "__main__":
    asyncio.run(test_database())
