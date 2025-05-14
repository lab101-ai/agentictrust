"""Database migration to remove MFA fields from users table."""
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Remove MFA fields from users table."""
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'mfa_type')
    op.drop_column('users', 'mfa_secret')

def downgrade():
    """Add MFA fields back to users table."""
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('mfa_type', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('mfa_secret', sa.String(100), nullable=True))
