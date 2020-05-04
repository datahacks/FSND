"""fixing artist

Revision ID: eba2f3b616f4
Revises: 6fbd6e42e9d0
Create Date: 2020-05-03 16:04:07.249698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eba2f3b616f4'
down_revision = '6fbd6e42e9d0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_venue', sa.Boolean(), nullable=True))
    op.drop_column('Artist', 'seeking_talent')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_talent', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('Artist', 'seeking_venue')
    # ### end Alembic commands ###
