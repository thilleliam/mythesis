"""Suppression de id_chantier dans transferer_equipement

Revision ID: e0d6cf555852
Revises: 359a9816ad67
Create Date: 2025-03-26 22:40:19.237840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0d6cf555852'
down_revision: Union[str, None] = '359a9816ad67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
