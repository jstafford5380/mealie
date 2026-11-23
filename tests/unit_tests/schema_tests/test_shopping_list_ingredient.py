import uuid

import pytest

from mealie.schema.household.group_shopping_list import ShoppingListItemOut


def test_shopping_list_ingredient_validation():
    db_obj = {
        "quantity": 8,
        "unit": None,
        "food": {
            "id": "4cf32eeb-d136-472d-86c7-287b6328d21f",
            "name": "bell peppers",
            "pluralName": None,
            "description": "",
            "extras": {},
            "labelId": None,
            "aliases": [],
            "label": None,
            "createdAt": "2024-02-26T18:29:46.190754",
            "updatedAt": "2024-02-26T18:29:46.190758",
        },
        "note": "",
        "shoppingListId": "dc8bce82-2da9-49f0-94e6-6d69d311490e",
        "checked": False,
        "position": 5,
        "foodId": "4cf32eeb-d136-472d-86c7-287b6328d21f",
        "labelId": None,
        "unitId": None,
        "extras": {},
        "id": "80f4df25-6139-4d30-be0c-4100f50e5396",
        "label": None,
        "recipeReferences": [],
        "groupId": uuid.uuid4(),
        "householdId": uuid.uuid4(),
        "createdAt": "2024-02-27T10:18:19.274677",
        "updatedAt": "2024-02-27T11:26:32.643392",
    }
    out = ShoppingListItemOut.model_validate(db_obj)
    assert out.display == "8 bell peppers"


@pytest.mark.parametrize(
    "unit", ["can", "pack", "clove", "head", "bunch", "serving", "sprig", "dash", "pinch", "splash"]
)
def test_shopping_amount_keeps_units_without_fixed_conversions(unit: str) -> None:
    item_id, unit_id, food_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plural = f"{unit}es" if unit.endswith(("ch", "sh")) else f"{unit}s"
    item = ShoppingListItemOut.model_validate(
        {
            "id": item_id,
            "shopping_list_id": uuid.uuid4(),
            "group_id": uuid.uuid4(),
            "household_id": uuid.uuid4(),
            "food_id": food_id,
            "food": {"id": food_id, "name": "tomatoes"},
            "unit_id": unit_id,
            "unit": {"id": unit_id, "name": unit, "plural_name": plural},
            "quantity": 1.5,
            "recipe_references": [
                {
                    "id": uuid.uuid4(),
                    "recipe_id": uuid.uuid4(),
                    "shopping_list_item_id": item_id,
                    "recipe_quantity": 1.5,
                }
            ],
        }
    )
    amount = item.shopping_amount
    assert amount is not None
    assert amount.quantity == 2
    assert amount.unit == plural
    assert item.quantity == 1.5
