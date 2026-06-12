"""merge all heads

Revision ID: 35d1ca4ee0c6
Revises: 0a1b2c3d4e6f, 2b3c4d5e6f7a, e6f7a8b9c0d1
Create Date: 2026-06-12 13:59:19.533757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35d1ca4ee0c6'
down_revision: Union[str, Sequence[str], None] = ('0a1b2c3d4e6f', '2b3c4d5e6f7a', 'e6f7a8b9c0d1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
