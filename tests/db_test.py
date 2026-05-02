import asyncio
from db import init_db, close_db


async def test():
    await init_db()
    print("Database initialized successfully")
    await close_db()


if __name__ == "__main__":
    asyncio.run(test())
