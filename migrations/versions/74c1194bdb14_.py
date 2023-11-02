"""empty message

Revision ID: 74c1194bdb14
Revises: 
Create Date: 2023-10-30 14:40:50.669684

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '74c1194bdb14'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password', sa.String(length=100), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    with op.batch_alter_table('class_notifications', schema=None) as batch_op:
        batch_op.alter_column('notification_datetime',
               existing_type=mysql.TIMESTAMP(),
               type_=sa.DateTime(),
               existing_nullable=True)
        batch_op.create_foreign_key(None, 'class', ['class_id'], ['id'])

    with op.batch_alter_table('teacher', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=mysql.BIGINT(unsigned=True),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True)
        batch_op.drop_index('id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('teacher', schema=None) as batch_op:
        batch_op.create_index('id', ['id'], unique=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=mysql.BIGINT(unsigned=True),
               existing_nullable=False,
               autoincrement=True)

    with op.batch_alter_table('class_notifications', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('notification_datetime',
               existing_type=sa.DateTime(),
               type_=mysql.TIMESTAMP(),
               existing_nullable=True)

    op.drop_table('users')
    # ### end Alembic commands ###
