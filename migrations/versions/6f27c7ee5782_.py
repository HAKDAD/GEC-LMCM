"""empty message

Revision ID: 6f27c7ee5782
Revises: 74c1194bdb14
Create Date: 2023-11-01 15:24:43.427703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f27c7ee5782'
down_revision = '74c1194bdb14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('leave_request',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('teacher_id', sa.String(length=10), nullable=False),
    sa.Column('class_id', sa.Integer(), nullable=False),
    sa.Column('leave_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('assigned_teacher_id', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('leave_request')
    # ### end Alembic commands ###