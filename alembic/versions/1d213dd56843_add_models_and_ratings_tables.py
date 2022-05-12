"""add models and ratings tables

Revision ID: 1d213dd56843
Revises: 
Create Date: 2022-05-12 11:30:31.726510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d213dd56843'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('models', 
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True), 
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('train_data', sa.String()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                              server_default=sa.text('now()'), nullable=False)
        )

    op.create_table('ratings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('translated_text', sa.String(), nullable=False),
        sa.Column('rating', sa.Boolean(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                              server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),

        )
    
    pass




def downgrade():
    op.drop_table('models')
    op.drop_table('ratings')
    pass
