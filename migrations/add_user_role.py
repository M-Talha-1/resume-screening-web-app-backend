"""Add role column to users table

Revision ID: add_user_role
Create Date: 2024-03-19 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from app.models import UserRole

def upgrade():
    # Create UserRole enum type
    user_role = sa.Enum(UserRole, name='userrole')
    user_role.create(op.get_bind())

    # Add role column with default value
    op.add_column('users', 
        sa.Column('role', user_role, nullable=False, server_default='user')
    )

def downgrade():
    # Remove role column
    op.drop_column('users', 'role')
    
    # Drop UserRole enum type
    sa.Enum(name='userrole').drop(op.get_bind()) 