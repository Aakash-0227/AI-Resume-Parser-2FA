
from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.database.connection import Base


class UserResume(Base):
    __tablename__ = "user_resumes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    extracted_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
