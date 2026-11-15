
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user
from app.services.otp_service import create_otp_challenge
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        new_user = await create_user(db, user_data)

        await create_otp_challenge(
            db=db,
            user_id=new_user.id,
            channel="email",
            recipient_email=new_user.email
        )

        return {
            "message": "Registration successful. OTP sent to your email.",
            "user": {
                "id": new_user.id,
                "full_name": new_user.full_name,
                "email": new_user.email,
                "phone": new_user.phone,
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified
            },
            "otp_channel": "email",
            "otp_expiry_minutes": 5
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User registration was saved, but OTP email delivery failed."
        ) from error


@router.get(
    "/me",
    response_model=UserResponse
)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse
)
async def update_my_profile(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile fields provided for update."
        )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return current_user
