"""create model_dir and tokenizer columns

Revision ID: a3f1535d0816
Revises: 1d213dd56843
Create Date: 2022-05-13 11:25:05.909184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f1535d0816'
down_revision = '1d213dd56843'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('models', sa.Column('path', sa.String(), nullable=True))
    op.add_column('models', sa.Column('tokenizer', sa.String(), nullable=True))
    pass


def downgrade():
    op.drop_column('models', 'path')
    op.drop_column('models', 'tokenizer')
    pass
