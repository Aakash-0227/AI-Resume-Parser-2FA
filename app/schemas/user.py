
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    is_active: bool
    is_verified: bool


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    qualification: str | None = Field(default=None, max_length=255)
    skills: list[str] | None = None
    experience: str | None = None


class ProfileResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    qualification: str | None
    skills: list[str] = Field(default_factory=list)
    experience: str | None
    is_active: bool
    is_verified: bool
