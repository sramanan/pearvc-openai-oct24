"""Added status

Revision ID: 12455d7c6685
Revises: 877dca0195f7
Create Date: 2024-10-12 18:06:23.393532

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12455d7c6685'
down_revision = '877dca0195f7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('call', schema=None) as batch_op:
        batch_op.add_column(sa.Column('call_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('call_message', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('call', schema=None) as batch_op:
        batch_op.drop_column('call_message')
        batch_op.drop_column('call_type')

    # ### end Alembic commands ###
