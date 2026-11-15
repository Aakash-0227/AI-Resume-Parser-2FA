
import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def main():
    async with engine.connect() as connection:
        result = await connection.execute(text("""
            SELECT
                id,
                original_filename,
                extracted_data->>'qualification' AS qualification,
                created_at
            FROM user_resumes
            ORDER BY id DESC
            LIMIT 10
        """))

        rows = result.mappings().all()

        print(f"\nTotal records found: {len(rows)}")

        for row in rows:
            print("\n---------------------------")
            print("Resume ID:", row["id"])
            print("Filename:", row["original_filename"])
            print("Qualification:", row["qualification"])
            print("Created At:", row["created_at"])

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
