"""Add Event, EventParticipant, and Transaction models

Revision ID: add_event_system
Revises: 
Create Date: 2026-07-15 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_event_system'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(180), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(280)),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('is_paid', sa.Boolean(), default=False),
        sa.Column('price', sa.Float(), default=0.0),
        sa.Column('currency', sa.String(3), default='RWF'),
        sa.Column('max_participants', sa.Integer()),
        sa.Column('location', sa.String(255)),
        sa.Column('event_date', sa.DateTime()),
        sa.Column('event_end_date', sa.DateTime()),
        sa.Column('registration_deadline', sa.DateTime()),
        sa.Column('cover_image', sa.String(255)),
        sa.Column('organizer_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('is_published', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create event_participants table
    op.create_table(
        'event_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('full_name', sa.String(140), nullable=False),
        sa.Column('email', sa.String(150), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('registration_date', sa.DateTime(), default=sa.func.now()),
        sa.Column('confirmation_date', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_event_email', 'event_participants', ['event_id', 'email'])

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('participant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), default='RWF'),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('momo_reference', sa.String(100)),
        sa.Column('payment_method', sa.String(50), default='momo'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('paid_at', sa.DateTime()),
        sa.Column('response_data', sa.JSON()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['participant_id'], ['event_participants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('transactions')
    op.drop_table('event_participants')
    op.drop_table('events')
