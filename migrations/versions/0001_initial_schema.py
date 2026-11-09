"""Initial database schema with multi-tenant isolation and outbox.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-09 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants & Subjects
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    op.create_table(
        'subjects',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('resident_pseudonym', sa.String(length=64), unique=True, index=True, nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id'), nullable=False, index=True),
        sa.Column('email', sa.String(length=255), unique=True, index=True, nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='resident'),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 2. Identifiers & Verification Challenges
    op.create_table(
        'identifiers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id'), nullable=False, index=True),
        sa.Column('type', sa.String(length=50), nullable=False, index=True),
        sa.Column('blind_index', sa.String(length=64), nullable=False, index=True),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('masked_value', sa.String(length=255), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False, server_default='pending_verification'),
        sa.Column('monitoring_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'blind_index', name='uq_tenant_blind_index')
    )

    # 3. Incidents & Remediation
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id'), nullable=False, index=True),
        sa.Column('identifier_id', sa.String(length=36), sa.ForeignKey('identifiers.id'), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('breach_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False, index=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('priority_score', sa.Integer(), nullable=False, server_default='50', index=True),
        sa.Column('state', sa.String(length=50), nullable=False, server_default='new', index=True),
        sa.Column('exposed_fields', sa.JSON(), nullable=False),
        sa.Column('description_sanitized', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 4. Outbox Events
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('event_id', sa.String(length=36), unique=True, index=True, nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('schema_version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('tenant_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('subject_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('resource_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('authorization_version', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('dead_lettered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('outbox_events')
    op.drop_table('incidents')
    op.drop_table('identifiers')
    op.drop_table('users')
    op.drop_table('subjects')
    op.drop_table('tenants')
