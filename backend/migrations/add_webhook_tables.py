"""
Create webhook tables

Revision ID: add_webhook_tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


def upgrade():
    """Create webhook tables"""
    # Create webhook_endpoints table
    op.create_table(
        'webhook_endpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('secret_key', sa.String(255), nullable=True),
        sa.Column('events', sa.Text, nullable=False),  # JSON array of event types
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('timeout_seconds', sa.Integer, default=10, nullable=False),
        sa.Column('max_retries', sa.Integer, default=3, nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        schema='sonicus'
    )
    
    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('endpoint_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('payload', sa.Text, nullable=False),  # JSON payload
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('http_status_code', sa.Integer, nullable=True),
        sa.Column('response_body', sa.Text, nullable=True),
        sa.Column('response_headers', sa.Text, nullable=True),  # JSON
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('attempt_count', sa.Integer, default=0, nullable=False),
        sa.Column('max_attempts', sa.Integer, default=3, nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        schema='sonicus'
    )
    
    # Create indexes for better performance
    op.create_index('ix_webhook_endpoints_is_active', 'webhook_endpoints', ['is_active'], schema='sonicus')
    op.create_index('ix_webhook_endpoints_organization_id', 'webhook_endpoints', ['organization_id'], schema='sonicus')
    op.create_index('ix_webhook_deliveries_endpoint_id', 'webhook_deliveries', ['endpoint_id'], schema='sonicus')
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['status'], schema='sonicus')
    op.create_index('ix_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type'], schema='sonicus')
    op.create_index('ix_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'], schema='sonicus')


def downgrade():
    """Drop webhook tables"""
    op.drop_index('ix_webhook_deliveries_created_at', schema='sonicus')
    op.drop_index('ix_webhook_deliveries_event_type', schema='sonicus')
    op.drop_index('ix_webhook_deliveries_status', schema='sonicus')
    op.drop_index('ix_webhook_deliveries_endpoint_id', schema='sonicus')
    op.drop_index('ix_webhook_endpoints_organization_id', schema='sonicus')
    op.drop_index('ix_webhook_endpoints_is_active', schema='sonicus')
    
    op.drop_table('webhook_deliveries', schema='sonicus')
    op.drop_table('webhook_endpoints', schema='sonicus')
