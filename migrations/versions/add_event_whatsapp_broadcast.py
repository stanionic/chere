"""Add Event WhatsApp fields + SMS Broadcast system

Revision ID: add_event_whatsapp_broadcast
Revises: c561f3c4ac7b
Create Date: 2026-07-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_event_whatsapp_broadcast'
down_revision = 'c561f3c4ac7b'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def _table_exists(table_name):
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    # 1. Ajout des colonnes whatsapp et allow_future_invites à event_participants
    if _table_exists('event_participants'):
        with op.batch_alter_table('event_participants', schema=None) as batch_op:
            if not _column_exists('event_participants', 'whatsapp'):
                batch_op.add_column(sa.Column('whatsapp', sa.String(length=20), nullable=True))
            if not _column_exists('event_participants', 'allow_future_invites'):
                batch_op.add_column(sa.Column('allow_future_invites', sa.Boolean(), nullable=True, server_default=sa.text('0')))

        # Index idx_future_invites (vérifier l'existence est complexe, tenter de créer)
        try:
            from sqlalchemy import inspect
            bind = op.get_bind()
            insp = inspect(bind)
            existing_indexes = [idx['name'] for idx in insp.get_indexes('event_participants')]
            if 'idx_future_invites' not in existing_indexes:
                op.create_index('idx_future_invites', 'event_participants', ['allow_future_invites'], unique=False)
        except Exception:
            pass

    # 2. Table event_sms_broadcasts
    if not _table_exists('event_sms_broadcasts'):
        op.create_table('event_sms_broadcasts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('channel', sa.String(length=20), nullable=True, server_default='sms'),
            sa.Column('target_scope', sa.String(length=30), nullable=True, server_default='optin_all'),
            sa.Column('specific_event_id', sa.Integer(), nullable=True),
            sa.Column('recipient_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('sent_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('failed_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='draft'),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
            sa.ForeignKeyConstraint(['specific_event_id'], ['events.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_event_sms_broadcasts_created_at'), 'event_sms_broadcasts', ['created_at'], unique=False)
        op.create_index(op.f('ix_event_sms_broadcasts_event_id'), 'event_sms_broadcasts', ['event_id'], unique=False)

    # 3. Table event_sms_recipients
    if not _table_exists('event_sms_recipients'):
        op.create_table('event_sms_recipients',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('broadcast_id', sa.Integer(), nullable=False),
            sa.Column('participant_id', sa.Integer(), nullable=True),
            sa.Column('phone_number', sa.String(length=20), nullable=False),
            sa.Column('full_name', sa.String(length=140), nullable=True),
            sa.Column('channel', sa.String(length=20), nullable=True, server_default='sms'),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='queued'),
            sa.Column('provider_reference', sa.String(length=100), nullable=True),
            sa.Column('error_message', sa.String(length=255), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['broadcast_id'], ['event_sms_broadcasts.id'], ),
            sa.ForeignKeyConstraint(['participant_id'], ['event_participants.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_event_sms_recipients_broadcast_id'), 'event_sms_recipients', ['broadcast_id'], unique=False)
        op.create_index(op.f('ix_event_sms_recipients_phone_number'), 'event_sms_recipients', ['phone_number'], unique=False)


def downgrade():
    # 3. Drop event_sms_recipients
    if _table_exists('event_sms_recipients'):
        op.drop_index(op.f('ix_event_sms_recipients_phone_number'), table_name='event_sms_recipients')
        op.drop_index(op.f('ix_event_sms_recipients_broadcast_id'), table_name='event_sms_recipients')
        op.drop_table('event_sms_recipients')

    # 2. Drop event_sms_broadcasts
    if _table_exists('event_sms_broadcasts'):
        op.drop_index(op.f('ix_event_sms_broadcasts_event_id'), table_name='event_sms_broadcasts')
        op.drop_index(op.f('ix_event_sms_broadcasts_created_at'), table_name='event_sms_broadcasts')
        op.drop_table('event_sms_broadcasts')

    # 1. Drop colonnes event_participants
    if _table_exists('event_participants'):
        try:
            op.drop_index('idx_future_invites', table_name='event_participants')
        except Exception:
            pass
        with op.batch_alter_table('event_participants', schema=None) as batch_op:
            if _column_exists('event_participants', 'allow_future_invites'):
                batch_op.drop_column('allow_future_invites')
            if _column_exists('event_participants', 'whatsapp'):
                batch_op.drop_column('whatsapp')
