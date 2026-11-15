
import pytest

from sqlalchemy import select, delete

import app.services.otp_service as otp_service

from app.database.connection import AsyncSessionLocal
from app.models.user import User
from app.models.otp import OTPChallenge


@pytest.mark.asyncio
async def test_otp_service(monkeypatch):

    captured = {}

    # Mock email delivery: no real email will be sent
    def fake_send_email_otp(recipient_email, otp):
        captured["recipient_email"] = recipient_email
        captured["otp"] = otp

    monkeypatch.setattr(
        otp_service,
        "send_email_otp",
        fake_send_email_otp
    )

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(User).where(User.id == 1)
        )

        user = result.scalar_one_or_none()

        assert user is not None, (
            "Test user ID 1 not found in the database."
        )

        print("\nStarting automated email OTP test...")
        print("User:", user.full_name)

        # 1. CREATE OTP CHALLENGE

        otp, challenge = await otp_service.create_otp_challenge(
            db=db,
            user_id=user.id,
            channel="email",
            recipient_email=user.email
        )

        assert captured["otp"] == otp
        assert captured["recipient_email"] == user.email

        assert challenge.otp_hash.startswith("$argon2id$")
        assert challenge.expires_at is not None

        print("OTP generated successfully!")
        print("OTP Challenge ID:", challenge.id)
        print("OTP stored as Argon2 hash successfully!")

        # 2. VERIFY OTP

        verified = await otp_service.verify_otp_challenge(
            db=db,
            user_id=user.id,
            channel="email",
            submitted_otp=otp
        )

        assert verified is True

        print("OTP verification successful!")

        # 3. CLEAN UP TEST OTP RECORD

        await db.execute(
            delete(OTPChallenge).where(
                OTPChallenge.id == challenge.id
            )
        )

        await db.commit()

        print("Test OTP record cleaned up.")

        print("\nOTP SERVICE TEST PASSED!")
