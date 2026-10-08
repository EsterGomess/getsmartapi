"""merge migration heads

Revision ID: da93f63dd196
Revises: 090b69375243, a6e6e7a249d1
Create Date: 2026-10-08 09:59:20.517726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da93f63dd196'
down_revision: Union[str, None] = ('090b69375243', 'a6e6e7a249d1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
