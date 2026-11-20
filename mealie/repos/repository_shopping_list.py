from collections.abc import Iterator
from contextlib import contextmanager

from pydantic import UUID4
from sqlalchemy import func, select, update

from mealie.db.models.household.shopping_list import ShoppingList
from mealie.schema.household.group_shopping_list import ShoppingListOut, ShoppingListUpdate

from .repository_generic import HouseholdRepositoryGeneric


class RepositoryShoppingList(HouseholdRepositoryGeneric[ShoppingListOut, ShoppingList]):
    @contextmanager
    def recipe_change(self, item_id: UUID4) -> Iterator[None]:
        """Serialize recipe changes to the same list before any quantities are read."""
        with self.transaction():
            scope = self._filter_builder(id=item_id)
            if self.session.get_bind().dialect.name == "postgresql":
                # The item flush also updates the list timestamp. An advisory lock avoids
                # taking those row locks in the opposite order from ordinary item edits.
                lock_key = int.from_bytes(item_id.bytes[:8], byteorder="big", signed=True)
                self.session.execute(
                    select(func.pg_advisory_xact_lock(lock_key)).select_from(self.model).filter_by(**scope)
                )
            else:
                # Reserve SQLite's writer transaction before loading the list.
                self.session.execute(update(self.model).filter_by(**scope).values(updated_at=self.model.updated_at))

            self.session.expire_all()
            yield

    def update(self, item_id: UUID4, data: ShoppingListUpdate | dict) -> ShoppingListOut:  # type: ignore[override]
        return super().update(item_id, data)
