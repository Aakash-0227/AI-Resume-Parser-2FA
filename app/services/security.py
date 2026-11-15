
import os
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext


password_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return password_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(data: dict) -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is missing from .env")

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })

    token = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


def decode_access_token(token: str) -> dict:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is missing from .env")

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )
