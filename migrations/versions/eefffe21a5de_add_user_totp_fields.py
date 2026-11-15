
"""add user totp fields

Revision ID: eefffe21a5de
Revises: a7974f87c0be
Create Date: 2026-11-15 12:38:33.482683

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = 'eefffe21a5de'
down_revision: Union[str, Sequence[str], None] = 'a7974f87c0be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add TOTP secret column.
    op.add_column(
        'users',
        sa.Column(
            'totp_secret',
            sa.String(length=255),
            nullable=True
        )
    )

    # Add TOTP enabled column.
    # Existing users will receive False.
    op.add_column(
        'users',
        sa.Column(
            'is_totp_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    # Remove the temporary database default.
    op.alter_column(
        'users',
        'is_totp_enabled',
        server_default=None
    )


def downgrade() -> None:
    """Revert TOTP fields."""

    op.drop_column('users', 'is_totp_enabled')
    op.drop_column('users', 'totp_secret')
