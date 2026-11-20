import json
import statistics
import uuid
from pathlib import Path
from zipfile import ZipFile

import pytest
from sqlalchemy.orm import Session

import tests.data as test_data
from mealie.core.config import get_app_settings
from mealie.core.settings.directories import AppDirectories
from mealie.db.db_setup import session_context
from mealie.db.models._model_utils.guid import GUID
from mealie.db.models.group import Group
from mealie.db.models.household.cookbook import CookBook
from mealie.db.models.household.household import Household
from mealie.db.models.household.household_to_recipe import HouseholdToRecipe
from mealie.db.models.household.mealplan import GroupMealPlanRules
from mealie.db.models.household.shopping_list import ShoppingList
from mealie.db.models.recipe.ingredient import IngredientFoodModel, IngredientUnitModel
from mealie.db.models.recipe.labels import MultiPurposeLabel
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.db.models.recipe.tool import Tool
from mealie.db.models.users.user_to_recipe import UserToRecipe
from mealie.db.models.users.users import User
from mealie.services.backups_v2.alchemy_exporter import AlchemyExporter
from mealie.services.backups_v2.backup_file import BackupFile
from mealie.services.backups_v2.backup_v2 import BackupV2


def test_database_backup():
    backup_v2 = BackupV2()
    path_to_backup = backup_v2.backup()

    assert path_to_backup.exists()

    backup = BackupFile(path_to_backup)

    with backup as contents:
        assert contents.validate()

    backup_v2.db_exporter.engine.dispose()


def test_database_restore():
    settings = get_app_settings()

    # Capture existing database snapshot
    original_exporter = AlchemyExporter(settings.DB_URL)
    original_snapshot = original_exporter.dump()
    original_exporter.engine.dispose()

    # Create Backup
    backup_v2 = BackupV2(settings.DB_URL)
    path_to_backup = backup_v2.backup()

    assert path_to_backup.exists()
    backup_v2.restore(path_to_backup)

    new_exporter = AlchemyExporter(settings.DB_URL)
    restored_snapshot = new_exporter.dump()
    new_exporter.engine.dispose()

    assert original_snapshot.keys() == restored_snapshot.keys()
    for table, rows in original_snapshot.items():
        expected = sorted(json.dumps(row, sort_keys=True) for row in rows)
        actual = sorted(json.dumps(row, sort_keys=True) for row in restored_snapshot[table])
        assert expected == actual, table


@pytest.mark.parametrize("failure", ["metadata", "missing_table", "import", "activate_files"])
def test_failed_restore_preserves_live_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    backup = BackupV2()
    monkeypatch.setattr(backup, "directories", AppDirectories(tmp_path / "live"))
    original_secret = backup.directories.DATA_DIR / ".secret"
    original_secret.write_text("live secret")
    live_file = backup.directories.RECIPE_DATA_DIR / "existing.txt"
    live_file.write_text("live recipe")

    with session_context() as session:
        user_ids = {user_id for (user_id,) in session.query(User.id).all()}
    assert user_ids

    # Use the current migration version and omit users so accidental activation would replace them.
    data = backup.db_exporter.dump_schema()
    if failure == "metadata":
        del data["alembic_version"]
    elif failure == "missing_table":
        del data["recipes"]
    elif failure == "import":
        data["unknown_table"] = [{"id": 1}]

    archive = tmp_path / "restore.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("database.json", json.dumps(data))
        zip_file.writestr("data/.secret", "replacement secret")
        zip_file.writestr("data/recipes/replacement.txt", "replacement recipe")

    if failure == "activate_files":
        rename = Path.rename

        def fail_on_recipe_install(path: Path, target: Path) -> Path:
            if path.parent.name == "incoming" and path.name == "recipes":
                raise OSError("Cannot activate recipes")
            return rename(path, target)

        monkeypatch.setattr(Path, "rename", fail_on_recipe_install)

    expected_errors = {
        "metadata": ValueError,
        "missing_table": ValueError,
        "import": KeyError,
        "activate_files": OSError,
    }
    with pytest.raises(expected_errors[failure]):
        backup.restore(archive)

    with session_context() as session:
        assert {user_id for (user_id,) in session.query(User.id).all()} == user_ids
    assert original_secret.read_text() == "live secret"
    assert live_file.read_text() == "live recipe"
    assert not (backup.directories.RECIPE_DATA_DIR / "replacement.txt").exists()
    assert not list(backup.directories.DATA_DIR.glob("*.bak.db"))
    backup.db_exporter.engine.dispose()


def _5ab195a474eb_add_normalized_search_properties(session: Session):
    recipes = session.query(RecipeModel).all()

    for recipe in recipes:
        if recipe.name:
            assert recipe.name_normalized
        if recipe.description:
            assert recipe.description_normalized

        for ingredient in recipe.recipe_ingredient:
            if ingredient.note:
                assert ingredient.note_normalized
            if ingredient.original_text:
                assert ingredient.original_text_normalized


def _b04a08da2108_added_shopping_list_label_settings(session: Session):
    shopping_lists = session.query(ShoppingList).all()
    labels = session.query(MultiPurposeLabel).all()

    for shopping_list in shopping_lists:
        group_labels = [label for label in labels if label.group_id == shopping_list.group_id]
        assert len(shopping_list.label_settings) == len(group_labels)
        for label_setting, label in zip(
            sorted(shopping_list.label_settings, key=lambda x: x.label.id),
            sorted(group_labels, key=lambda x: x.id),
            strict=True,
        ):
            assert label_setting.label == label


def _04ac51cbe9a4_added_group_slug(session: Session):
    groups = session.query(Group).all()

    for group in groups:
        assert group.slug


def _0341b154f79a_added_normalized_unit_and_food_names(session: Session):
    foods = session.query(IngredientFoodModel).all()
    units = session.query(IngredientUnitModel).all()

    for food in foods:
        if food.name:
            assert food.name_normalized

    for unit in units:
        assert unit.name_normalized
        if unit.abbreviation:
            assert unit.abbreviation_normalized


def _d7c6efd2de42_migrate_favorites_and_ratings_to_user_ratings(session: Session):
    recipes = session.query(RecipeModel).all()

    users_by_group_id: dict[GUID, list[User]] = {}
    for recipe in recipes:
        users = users_by_group_id.get(recipe.group_id)
        if users is None:
            users = session.query(User).filter(User.group_id == recipe.group_id).all()
            users_by_group_id[recipe.group_id] = users

        user_to_recipes = session.query(UserToRecipe).filter(UserToRecipe.recipe_id == recipe.id).all()
        user_ratings = [x.rating for x in user_to_recipes if x.rating]
        assert recipe.rating == (statistics.mean(user_ratings) if user_ratings else None)


def _legacy_organizer_owner_ids(backup_path: Path) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
    """Ids of the cookbooks and meal plan rules that had legacy organizer join rows in the backup itself."""
    with BackupFile(backup_path) as contents:
        tables = contents.read_tables()

    def owner_ids(table: str, column: str) -> set[uuid.UUID]:
        return {uuid.UUID(row[column]) for row in tables.get(table) or []}

    cookbook_ids = (
        owner_ids("cookbooks_to_categories", "cookbook_id")
        | owner_ids("cookbooks_to_tags", "cookbook_id")
        | owner_ids("cookbooks_to_tools", "cookbook_id")
    )
    rule_ids = owner_ids("plan_rules_to_categories", "group_plan_rule_id") | owner_ids(
        "plan_rules_to_tags", "plan_rule_id"
    )
    return cookbook_ids, rule_ids


def _86054b40fd06_added_query_filter_string_to_cookbook_and_mealplan(session: Session, backup_path: Path):
    cookbooks = session.query(CookBook).all()
    mealplan_rules = session.query(GroupMealPlanRules).all()
    legacy_cookbook_ids, legacy_rule_ids = _legacy_organizer_owner_ids(backup_path)

    # 3697d65c5f92 empties the category/tag/tool join tables once 86054b40fd06 has folded them into
    # query_filter_string, so the filter can no longer be rebuilt from these relationships.
    for cookbook in cookbooks:
        assert not cookbook.categories
        assert not cookbook.tags
        assert not cookbook.tools
        if cookbook.id in legacy_cookbook_ids:
            assert cookbook.query_filter_string

    for rule in mealplan_rules:
        assert not rule.categories
        assert not rule.tags
        if rule.id in legacy_rule_ids:
            assert rule.query_filter_string

        # plan_rules_to_households is left alone, so its part of the filter can still be rebuilt
        if rule.households:
            vals = ",".join([f'"{household.id}"' for household in rule.households])
            assert f"household_id IN [{vals}]" in rule.query_filter_string


def _b9e516e2d3b3_add_household_to_recipe_last_made_household_to_foods_and_tools(session: Session):
    groups = session.query(Group).all()

    for group in groups:
        households = session.query(Household).filter(Household.group_id == group.id).all()
        household_ids = {household.id for household in households}
        recipes = session.query(RecipeModel).filter(RecipeModel.group_id == group.id).all()
        for recipe in recipes:
            for household in households:
                household_to_recipe = (
                    session.query(HouseholdToRecipe)
                    .filter(HouseholdToRecipe.recipe_id == recipe.id, HouseholdToRecipe.household_id == household.id)
                    .one_or_none()
                )

                if recipe.last_made:
                    assert household_to_recipe
                    assert household_to_recipe.last_made == recipe.last_made
                else:
                    assert not household_to_recipe

        foods = session.query(IngredientFoodModel).filter(IngredientFoodModel.group_id == group.id).all()
        for food in foods:
            if food.on_hand:
                assert {hh.id for hh in food.households_with_ingredient_food} == household_ids
            else:
                assert not food.households_with_ingredient_food

        tools = session.query(Tool).filter(Tool.group_id == group.id).all()
        for tool in tools:
            if tool.on_hand:
                assert {hh.id for hh in tool.households_with_tool} == household_ids
            else:
                assert not tool.households_with_tool


def _a39c7f1826e3_add_unit_standardization_fields(session: Session):
    groups = session.query(Group).all()

    for group in groups:
        # test_data.backup_version_1d9a002d7234_1 has a non-anonymized "pint" unit
        # and has not yet run the standardization migration.
        pint_units = (
            session.query(IngredientUnitModel)
            .filter(IngredientUnitModel.group_id == group.id, IngredientUnitModel.name == "pint")
            .all()
        )
        for unit in pint_units:
            assert unit.standard_quantity == 2
            assert unit.standard_unit == "cup"


def test_database_restore_data():
    """
    This tests real user backups to make sure the data is restored correctly. The data has been anonymized, but
    relationships and data types should be preserved.

    This test should verify all migrations that do some sort of database manipulation (e.g. populating a new column).
    If a new migration is added that does any sort of data manipulation, this test should be updated.
    """

    backup_paths = [
        test_data.backup_version_1d9a002d7234_1,
        test_data.backup_version_44e8d670719d_1,
        test_data.backup_version_44e8d670719d_2,
        test_data.backup_version_44e8d670719d_3,
        test_data.backup_version_44e8d670719d_4,
        test_data.backup_version_ba1e4a6cfe99_1,
        test_data.backup_version_bcfdad6b7355_1,
        test_data.backup_version_09aba125b57a_1,
        test_data.backup_version_86054b40fd06_1,
    ]

    migration_funcs = [
        _5ab195a474eb_add_normalized_search_properties,
        _b04a08da2108_added_shopping_list_label_settings,
        _04ac51cbe9a4_added_group_slug,
        _0341b154f79a_added_normalized_unit_and_food_names,
        _d7c6efd2de42_migrate_favorites_and_ratings_to_user_ratings,
        _b9e516e2d3b3_add_household_to_recipe_last_made_household_to_foods_and_tools,
        _a39c7f1826e3_add_unit_standardization_fields,
    ]

    settings = get_app_settings()
    backup_v2 = BackupV2(settings.DB_URL)

    backup_v2.directories.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    original_data_backup = backup_v2.backup()

    try:
        for backup_path in backup_paths:
            assert backup_path.exists()
            backup_v2.restore(backup_path)

            with session_context() as session:
                for migration_func in migration_funcs:
                    try:
                        migration_func(session)
                    except Exception as e:
                        session.rollback()
                        raise Exception(
                            f'Migration "{migration_func.__name__}" failed on backup "{backup_path}"'
                        ) from e

                try:
                    _86054b40fd06_added_query_filter_string_to_cookbook_and_mealplan(session, backup_path)
                except Exception as e:
                    session.rollback()
                    raise Exception(
                        f'Migration "_86054b40fd06_added_query_filter_string_to_cookbook_and_mealplan" '
                        f'failed on backup "{backup_path}"'
                    ) from e

    finally:
        backup_v2.restore(original_data_backup)
