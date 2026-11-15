
import asyncio

from sqlalchemy import text
from app.database.connection import engine


async def test_database_connection():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT version()")
            )

            print("Database connected successfully!")
            print(result.scalar())

    except Exception as e:
        print("Database connection failed!")
        print(e)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_database_connection())
