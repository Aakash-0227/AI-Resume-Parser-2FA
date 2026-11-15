
import io

import qrcode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.database.connection import get_db
from app.models.user import User

from app.schemas.user import UserCreate
from app.schemas.otp import OTPVerifyRequest

from app.services.user_service import create_user

from app.services.otp_service import (
    create_otp_challenge,
    verify_otp_challenge
)

from app.services.security import (
    create_access_token,
    verify_password
)

from app.services.totp_service import (
    generate_totp_secret,
    generate_provisioning_uri,
    verify_totp_code
)

from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# --------------------------------------------------
# REQUEST SCHEMAS
# --------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    otp: str | None = Field(
        default=None,
        pattern=r"^\d{6}$"
    )


class TOTPVerifyRequest(BaseModel):
    otp: str = Field(pattern=r"^\d{6}$")


# --------------------------------------------------
# 1. USER REGISTRATION
# POST /api/v1/auth/register
# --------------------------------------------------

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
            detail="Registration was saved, but OTP email delivery failed."
        ) from error


# --------------------------------------------------
# 2. EMAIL OTP VERIFICATION
# POST /api/v1/auth/verify-2fa
# --------------------------------------------------

@router.post("/verify-2fa")
async def verify_2fa(
    otp_data: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            User.email == str(otp_data.email)
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified"
        )

    try:
        await verify_otp_challenge(
            db=db,
            user_id=user.id,
            channel=otp_data.channel,
            submitted_otp=otp_data.otp
        )

        user.is_verified = True
        user.is_active = True

        await db.commit()
        await db.refresh(user)

        access_token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email
            }
        )

        return {
            "message": "OTP verified successfully. Account activated.",
            "verified": True,
            "user_id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        ) from error


# --------------------------------------------------
# 3. USER LOGIN WITH OPTIONAL TOTP
# POST /api/v1/auth/login
# --------------------------------------------------

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            User.email == str(login_data.email)
        )
    )

    user = result.scalar_one_or_none()

    # Verify email and password.
    if user is None or not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check account activation.
    if not user.is_active or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete account verification first"
        )

    # Require authenticator OTP when TOTP is enabled.
    if user.is_totp_enabled:

        if not login_data.otp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticator OTP is required for this account"
            )

        if not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP configuration is invalid. Contact support."
            )

        is_valid = verify_totp_code(
            secret=user.totp_secret,
            otp=login_data.otp
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authenticator code"
            )

    elif login_data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP is not enabled for this account"
        )

    # Issue JWT only after all required checks pass.
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email
        }
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "totp_verified": user.is_totp_enabled
    }


# --------------------------------------------------
# 4. TOTP SETUP
# POST /api/v1/auth/totp/setup
# --------------------------------------------------

@router.post("/totp/setup")
async def setup_totp(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TOTP is already enabled"
        )

    # Generate a fresh secret.
    secret = generate_totp_secret()

    # Save pending secret in database.
    current_user.totp_secret = secret
    current_user.is_totp_enabled = False

    await db.commit()

    return {
        "message": "TOTP setup initiated successfully.",
        "instructions": [
            "Open Google Authenticator.",
            "Use the QR display endpoint to scan your account.",
            "Verify the six-digit code."
        ]
    }


# --------------------------------------------------
# 5. DISPLAY TOTP QR CODE
# GET /api/v1/auth/totp/qr
# --------------------------------------------------

@router.get("/totp/qr")
async def display_totp_qr(
    current_user: User = Depends(get_current_user)
):
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please initiate TOTP setup first"
        )

    provisioning_uri = generate_provisioning_uri(
        email=current_user.email,
        secret=current_user.totp_secret
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png"
    )


# --------------------------------------------------
# 6. VERIFY AND ENABLE TOTP
# POST /api/v1/auth/totp/verify
# --------------------------------------------------

@router.post("/totp/verify")
async def verify_totp(
    otp_data: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP is already enabled"
        )

    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete TOTP setup first"
        )

    is_valid = verify_totp_code(
        secret=current_user.totp_secret,
        otp=otp_data.otp
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired authenticator code"
        )

    current_user.is_totp_enabled = True

    await db.commit()
    await db.refresh(current_user)

    return {
        "message": "TOTP enabled successfully.",
        "totp_enabled": True,
        "user_id": current_user.id
    }


# --------------------------------------------------
# 7. DISABLE TOTP
# POST /api/v1/auth/totp/disable
# --------------------------------------------------

@router.post("/totp/disable")
async def disable_totp(
    otp_data: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP is not enabled"
        )

    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP secret not found"
        )

    is_valid = verify_totp_code(
        secret=current_user.totp_secret,
        otp=otp_data.otp
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authenticator code"
        )

    current_user.is_totp_enabled = False
    current_user.totp_secret = None

    await db.commit()

    return {
        "message": "TOTP disabled successfully.",
        "totp_enabled": False
    }
