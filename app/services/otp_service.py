
import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.otp import OTPChallenge
from app.services.security import hash_password, verify_password
from app.services.email_service import send_email_otp


OTPChannel = Literal["email", "whatsapp", "totp"]

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


async def create_otp_challenge(
    db: AsyncSession,
    user_id: int,
    channel: OTPChannel,
    recipient_email: str
) -> tuple[str, OTPChallenge]:

    if channel != "email":
        raise ValueError(
            "Only email OTP delivery is currently implemented"
        )

    otp = f"{secrets.randbelow(1000000):06d}"

    challenge = OTPChallenge(
        user_id=user_id,
        channel=channel,
        otp_hash=hash_password(otp),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
        attempts=0
    )

    try:
        db.add(challenge)

        await db.flush()

        await asyncio.to_thread(
            send_email_otp,
            recipient_email=recipient_email,
            otp=otp
        )

        await db.commit()
        await db.refresh(challenge)

        return otp, challenge

    except Exception:
        await db.rollback()
        raise


async def verify_otp_challenge(
    db: AsyncSession,
    user_id: int,
    channel: OTPChannel,
    submitted_otp: str
) -> bool:

    if channel != "email":
        raise ValueError(
            "Only email OTP verification is currently implemented"
        )

    result = await db.execute(
        select(OTPChallenge)
        .where(
            OTPChallenge.user_id == user_id,
            OTPChallenge.channel == channel,
            OTPChallenge.verified_at.is_(None)
        )
        .order_by(OTPChallenge.created_at.desc())
    )

    challenge = result.scalars().first()

    if challenge is None:
        raise ValueError("No pending OTP challenge found")

    if challenge.expires_at <= datetime.now(timezone.utc):
        raise ValueError("OTP has expired")

    if challenge.attempts >= MAX_OTP_ATTEMPTS:
        raise ValueError("Maximum OTP attempts exceeded")

    if not verify_password(submitted_otp, challenge.otp_hash):
        challenge.attempts += 1
        await db.commit()
        raise ValueError("Invalid OTP")

    challenge.verified_at = datetime.now(timezone.utc)

    await db.commit()

    return True
