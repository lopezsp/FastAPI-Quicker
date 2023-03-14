"""nick_name and followers

Revision ID: 1146d79b84d1
Revises: 
Create Date: 2023-03-13 16:27:22.768204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1146d79b84d1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('followers', sa.Integer))
    op.add_column('users', sa.Column('nick_name', sa.String))


def downgrade() -> None:
    op.drop_column('users', 'followers')
    op.drop_column('users', 'nick_name')

