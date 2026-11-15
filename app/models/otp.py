
from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    otp_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
