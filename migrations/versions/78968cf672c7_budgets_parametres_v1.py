"""budgets - parametres v1

Revision ID: 78968cf672c7
Revises: b41a4fe5bd2e
Create Date: 2022-12-01 17:34:34.675407

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78968cf672c7'
down_revision = 'b41a4fe5bd2e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mq_budget_parametres_defaultvisualisation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('localisation', sa.String(length=100), nullable=False),
    sa.Column('titre', sa.String(length=255), nullable=True),
    sa.Column('sous_titre', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('localisation')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('mq_budget_parametres_defaultvisualisation')
    # ### end Alembic commands ###