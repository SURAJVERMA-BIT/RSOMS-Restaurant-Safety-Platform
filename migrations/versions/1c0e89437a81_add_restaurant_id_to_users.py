"""add restaurant_id to users

Revision ID: 1c0e89437a81
Revises: 61d7783ed9a5
Create Date: 2026-06-28 09:11:11.842115

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c0e89437a81'
down_revision = '61d7783ed9a5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('restaurant_id', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('restaurant_id')
