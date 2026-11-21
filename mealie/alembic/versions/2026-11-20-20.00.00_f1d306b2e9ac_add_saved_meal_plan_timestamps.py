"""Add the standard model timestamps to saved meal plans."""

import sqlalchemy as sa
from alembic import op

from mealie.db.models._model_utils.datetime import NaiveDateTime

revision = "f1d306b2e9ac"
down_revision = "e2cb33d59c4a"
branch_labels = None
depends_on = None

TABLE = "saved_meal_plans"
CREATED_INDEX = "ix_saved_meal_plans_created_at"


def upgrade() -> None:
    # Some development databases ran the first revision with timestamps already included.
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(TABLE)}
    for name in ("created_at", "update_at"):
        if name not in columns:
            op.add_column(TABLE, sa.Column(name, NaiveDateTime(), nullable=True))

    if all(index["name"] != CREATED_INDEX for index in inspector.get_indexes(TABLE)):
        op.create_index(CREATED_INDEX, TABLE, ["created_at"])


def downgrade() -> None:
    op.drop_index(CREATED_INDEX, table_name=TABLE)
    op.drop_column(TABLE, "update_at")
    op.drop_column(TABLE, "created_at")
