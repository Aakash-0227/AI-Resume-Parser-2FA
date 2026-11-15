
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.resume import UserResume
from app.schemas.user import ProfileUpdate, ProfileResponse


router = APIRouter(
    prefix="/api/v1/profile",
    tags=["Profile"]
)


@router.get(
    "",
    response_model=ProfileResponse
)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserResume)
        .where(UserResume.user_id == current_user.id)
        .order_by(UserResume.created_at.desc())
        .limit(1)
    )

    resume = result.scalar_one_or_none()

    extracted_data = resume.extracted_data if resume and resume.extracted_data else {}

    return ProfileResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        qualification=extracted_data.get("qualification"),
        skills=extracted_data.get("skills", []),
        experience=extracted_data.get("experience"),
        is_active=current_user.is_active,
        is_verified=current_user.is_verified
    )


@router.patch(
    "",
    response_model=ProfileResponse
)
async def update_profile(
    profile_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = profile_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile fields provided for update."
        )

    result = await db.execute(
        select(UserResume)
        .where(UserResume.user_id == current_user.id)
        .order_by(UserResume.created_at.desc())
        .limit(1)
    )

    resume = result.scalar_one_or_none()

    try:
        # Update registered user information
        if "full_name" in update_data:
            current_user.full_name = update_data["full_name"]

        if "phone" in update_data:
            current_user.phone = update_data["phone"]

        # Update extracted resume information
        resume_fields = {
            "qualification",
            "skills",
            "experience"
        }

        if resume_fields.intersection(update_data.keys()):
            if resume is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No linked resume found for this user."
                )

            extracted_data = dict(resume.extracted_data or {})

            for field in resume_fields:
                if field in update_data:
                    extracted_data[field] = update_data[field]

            resume.extracted_data = extracted_data

        await db.commit()
        await db.refresh(current_user)

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        raise

    return await get_profile(db=db, current_user=current_user)
