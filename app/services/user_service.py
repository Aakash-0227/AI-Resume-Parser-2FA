
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.resume import UserResume
from app.schemas.user import UserCreate
from app.services.security import hash_password


async def create_user(
    db: AsyncSession,
    user_data: UserCreate
) -> User:

    email = str(user_data.email).lower()

    # Check whether the user already exists
    result = await db.execute(
        select(User).where(User.email == email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError("Email is already registered")

    # Hash the password using Argon2
    hashed_password = hash_password(user_data.password)

    # Create the new user
    new_user = User(
        full_name=user_data.full_name,
        email=email,
        phone=user_data.phone,
        password_hash=hashed_password,
        is_active=False,
        is_verified=False
    )

    try:
        db.add(new_user)

        # Generate user ID before linking the resume
        await db.flush()

        # Find the latest unlinked resume matching the user's email
        resume_result = await db.execute(
            select(UserResume)
            .where(
                UserResume.user_id.is_(None),
                UserResume.extracted_data["email"].astext == email
            )
            .order_by(UserResume.created_at.desc())
            .limit(1)
        )

        resume = resume_result.scalar_one_or_none()

        # Link the resume to the newly registered user
        if resume:
            resume.user_id = new_user.id

        await db.commit()
        await db.refresh(new_user)

        return new_user

    except Exception:
        await db.rollback()
        raise
