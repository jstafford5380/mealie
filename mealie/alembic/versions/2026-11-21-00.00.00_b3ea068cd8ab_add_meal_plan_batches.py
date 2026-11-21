"""Add batch references to meal plan entries."""

import sqlalchemy as sa
from alembic import op

from mealie.db.models._model_utils.guid import GUID

revision = "b3ea068cd8ab"
down_revision = "f1d306b2e9ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("recipe_batch_id", "leftover_batch_id"):
        op.add_column("group_meal_plans", sa.Column(name, GUID(), nullable=True))
        op.create_index(f"ix_group_meal_plans_{name}", "group_meal_plans", [name])


def downgrade() -> None:
    for name in ("leftover_batch_id", "recipe_batch_id"):
        op.drop_index(f"ix_group_meal_plans_{name}", table_name="group_meal_plans")
        op.drop_column("group_meal_plans", name)
