import sys
import os
import asyncio
import uuid
from decimal import Decimal

# Ensure src is in path
sys.path.append(os.getcwd())

from src.config import settings
from src.services.db.connection import get_db
from sqlalchemy import text
from src.services.redis_client import RedisManager

async def check_db_and_vector():
    print(f"Connecting to DB: {settings.database_url}...")
    try:
        with get_db() as db:
            # Check version and current DB
            ver = db.execute(text("SELECT version(), current_database()")).fetchone()
            print(f"✅ DB Version: {ver[0]}, Database: {ver[1]}")

            # Check pgvector extension
            ext = db.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'")).fetchone()
            if ext:
                print("✅ pgvector extension installed")
            else:
                print("❌ pgvector extension NOT installed")
                return

            # Check vector column (is_reflected)
            res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='qa_history' AND column_name='is_reflected'")).fetchone()
            if res:
                print("✅ QAHistory.is_reflected exists")
            else:
                print("❌ QAHistory.is_reflected MISSING")
            
            # Simple vector test: compute distance between [1,2,3] and [4,5,6]
            # using psycopg v3 syntax/operator
            try:
                dist = db.execute(text("SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector")).scalar()
                print(f"✅ Vector distance query successful: {dist}")
            except Exception as e:
                print(f"❌ Vector query failed: {e}")

    except Exception as e:
        print(f"❌ DB Connection failed: {e}")
        import traceback
        traceback.print_exc()

async def check_redis():
    print(f"Connecting to Redis (Cache: {settings.redis_cache_url})...")
    try:
        client = RedisManager.get_cache()
        client.ping()
        print("✅ Redis PING successful")
        
        # Test basic SET/GET
        key = f"test-key-{uuid.uuid4()}"
        client.set(key, "slough-ai-test", ex=10)
        val = client.get(key)
        if val == "slough-ai-test":
             print("✅ Redis SET/GET successful")
        else:
             print(f"❌ Redis GET mismatch: {val}")
    except Exception as e:
        print(f"❌ Redis failed: {e}")

async def main():
    print("--- Starting Verification ---")
    await check_db_and_vector()
    await check_redis()
    print("--- verification complete ---")

if __name__ == "__main__":
    asyncio.run(main())
