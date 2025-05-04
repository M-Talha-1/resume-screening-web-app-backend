"""initial

Revision ID: 520bb4232fe0
Revises: 
Create Date: 2025-05-04 03:57:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '520bb4232fe0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create applicants table
    op.create_table('applicants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('skills', sa.JSON(), nullable=False),
        sa.Column('designation', sa.String(), nullable=True),
        sa.Column('total_experience', sa.Float(), nullable=False),
        sa.Column('current_company', sa.String(), nullable=True),
        sa.Column('current_location', sa.String(), nullable=True),
        sa.Column('notice_period', sa.Integer(), nullable=True),
        sa.Column('expected_salary', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('linkedin', sa.String(), nullable=True),
        sa.Column('github', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('education', sa.JSON(), nullable=True),
        sa.Column('experience', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='OPEN'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)

    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create candidate_evaluations table
    op.create_table('candidate_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('skill_match', sa.Float(), nullable=False),
        sa.Column('experience_match', sa.Float(), nullable=False),
        sa.Column('matching_skills', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('evaluation_duration', sa.Interval(), nullable=True),
        sa.Column('evaluation_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('candidate_evaluations')
    op.drop_table('resumes')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_table('applicants')
    op.drop_table('users') 