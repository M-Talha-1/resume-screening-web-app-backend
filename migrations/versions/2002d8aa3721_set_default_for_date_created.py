"""Set default for date_created

Revision ID: 2002d8aa3721
Revises: 7fa330c0fbda
Create Date: 2025-03-24 12:03:06.054966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2002d8aa3721'
down_revision: Union[str, None] = '7fa330c0fbda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column('job_descriptions', 'date_created',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=sa.func.now())  # ✅ Add default NOW()

def downgrade():
    op.alter_column('job_descriptions', 'date_created',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)

