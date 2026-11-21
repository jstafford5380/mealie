"""Add household saved meal plans."""

import sqlalchemy as sa
from alembic import op

from mealie.db.models._model_utils.guid import GUID

revision = "e2cb33d59c4a"
down_revision = "08880d089634"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_meal_plans",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("group_id", GUID(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("household_id", GUID(), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("entries", sa.JSON(), nullable=False),
    )
    op.create_index("ix_saved_meal_plans_group_id", "saved_meal_plans", ["group_id"])
    op.create_index("ix_saved_meal_plans_household_id", "saved_meal_plans", ["household_id"])


def downgrade() -> None:
    op.drop_table("saved_meal_plans")
