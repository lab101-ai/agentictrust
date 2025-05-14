"""Database migration to drop MFA challenges table."""
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Drop MFA challenges table."""
    op.drop_table('mfa_challenges')

def downgrade():
    """Recreate MFA challenges table."""
    op.create_table('mfa_challenges',
        sa.Column('challenge_id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('challenge_type', sa.String(20), nullable=False),
        sa.Column('challenge_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('completed', sa.Boolean(), default=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('operation_type', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    )
