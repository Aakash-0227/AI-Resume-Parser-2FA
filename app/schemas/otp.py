
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


OTPChannel = Literal["email", "whatsapp", "totp"]


class OTPRequest(BaseModel):
    email: EmailStr
    channel: OTPChannel


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    channel: OTPChannel
    otp: str = Field(pattern=r"^[0-9]{6}$")


class OTPResponse(BaseModel):
    message: str
    channel: OTPChannel
    expires_in: int | None = None


class OTPVerificationResponse(BaseModel):
    message: str
    verified: bool
    channel: OTPChannel
