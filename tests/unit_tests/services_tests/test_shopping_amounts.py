import pytest

from mealie.services.household_services.shopping_amounts import shopping_quantity


@pytest.mark.parametrize(
    ("quantity", "standard_unit", "factor", "expected"),
    [
        (3 + 11 / 12, "fluid_ounce", 0.5, (4, "tbsp")),
        (7.9, "fluid_ounce", 0.5, (0.5, "cup")),
        (8.01, "fluid_ounce", 0.5, (0.75, "cup")),
        (1.9, "cup", 1, (1, "pt")),
        (2, "pint", 1, (1, "qt")),
        (4, "quart", 1, (1, "gal")),
        (1.01, "gallon", 1, (1.25, "gal")),
        (399.5, "milligram", 1, (400, "mg")),
        (999.5, "milligram", 1, (1, "g")),
        (999, "gram", 1, (1, "kg")),
        (2, "centiliter", 1, (20, "mL")),
        (10, "deciliter", 1, (1, "L")),
        (1051, "milliliter", 1, (1.1, "L")),
        (1151, "milliliter", 1, (1.2, "L")),
        (1.02, "pound", 1, (1.25, "lb")),
        (8, "ounce", 1, (8, "oz")),
        (0.25, None, None, (1, "")),
        (0, None, None, None),
        (1.1, "dash", 1, (2, "")),
    ],
)
def test_shopping_quantity(quantity, standard_unit, factor, expected):
    assert shopping_quantity(quantity, standard_unit, factor) == expected
