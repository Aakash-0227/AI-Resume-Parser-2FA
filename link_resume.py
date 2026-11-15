
import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def main():
    async with engine.begin() as connection:

        # Confirm that user ID 3 exists
        user_result = await connection.execute(
            text("""
                SELECT id
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": 3}
        )

        if user_result.scalar_one_or_none() is None:
            print("User ID 3 does not exist.")
            return

        # Check the existing resume record
        resume_result = await connection.execute(
            text("""
                SELECT id, user_id
                FROM user_resumes
                WHERE id = :resume_id
            """),
            {"resume_id": 2}
        )

        resume = resume_result.mappings().one_or_none()

        if resume is None:
            print("Resume ID 2 does not exist.")
            return

        if resume["user_id"] == 3:
            print("Resume is already linked to user ID 3.")
            return

        if resume["user_id"] is not None:
            print("Resume is already linked to another user.")
            return

        # Link resume ID 2 to user ID 3
        await connection.execute(
            text("""
                UPDATE user_resumes
                SET user_id = :user_id
                WHERE id = :resume_id
                  AND user_id IS NULL
            """),
            {"user_id": 3, "resume_id": 2}
        )

        print("Resume successfully linked!")
        print("Resume ID: 2")
        print("User ID: 3")


if __name__ == "__main__":
    asyncio.run(main())
