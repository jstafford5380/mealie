import datetime
import os
import uuid
from collections.abc import Callable
from os import path
from textwrap import dedent
from typing import Any

from alembic import command, script
from alembic.config import Config
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Connection, ForeignKey, ForeignKeyConstraint, MetaData, Table, create_engine, insert, text
from sqlalchemy.engine import base
from sqlalchemy.orm import Session, sessionmaker

from mealie.db import init_db
from mealie.db.fixes.fix_group_with_no_name import fix_group_with_no_name
from mealie.db.fixes.fix_migration_data import fix_migration_data
from mealie.db.init_db import ALEMBIC_DIR
from mealie.db.models._model_utils.guid import GUID
from mealie.repos.all_repositories import get_repositories
from mealie.services._base_service import BaseService


class AlchemyExporter(BaseService):
    connection_str: str
    engine: base.Engine
    meta: MetaData

    look_for_datetime = {
        "created_at",
        "update_at",
        "date_updated",
        "timestamp",
        "expires_at",
        "locked_at",
        "last_made",
        "completed_date",
        "tokens_valid_after",
    }
    """Column names restored back into datetimes. Anything stored as a `NaiveDateTime` and missing
    here comes back from a backup as a string; `test_every_datetime_column_survives_a_backup` guards
    against forgetting to add one."""
    look_for_date = {"date_added", "date", "end_date"}
    look_for_time = {"scheduled_time"}

    class DateTimeParser(BaseModel):
        date: datetime.date | None = None
        dt: datetime.datetime | None = None
        time: datetime.time | None = None

    def __init__(self, connection_str: str) -> None:
        super().__init__()

        self.connection_str = connection_str
        self.engine = create_engine(connection_str)
        self.meta = MetaData()
        self.session_maker = sessionmaker(bind=self.engine)

    @staticmethod
    def is_uuid(value: Any) -> bool:
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_foreign_key(db_dump: dict[str, list[dict]], fk: ForeignKey, fk_value: Any) -> bool:
        if not fk_value:
            return True

        foreign_table_name = fk.column.table.name
        foreign_field_name = fk.column.name

        for row in db_dump.get(foreign_table_name, []):
            if row[foreign_field_name] == fk_value:
                return True

        return False

    def convert_types(self, data: dict) -> dict:
        """
        walks the dictionary to restore all things that look like string representations of their complex types
        used in the context of reading a json file into a database via SQLAlchemy.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                data = self.convert_types(value)
            elif isinstance(value, list):  # assume that this is a list of dictionaries
                data[key] = [self.convert_types(item) for item in value]
            elif isinstance(value, str):
                if self.is_uuid(value):
                    # convert the data to the current database's native GUID type
                    data[key] = GUID.convert_value_to_guid(value, self.engine.dialect)
                if key in self.look_for_datetime:
                    data[key] = self.DateTimeParser(dt=value).dt
                if key in self.look_for_date:
                    data[key] = self.DateTimeParser(date=value).date
                if key in self.look_for_time:
                    data[key] = self.DateTimeParser(time=value).time
        return data

    def clean_rows(self, db_dump: dict[str, list[dict]], table: Table, rows: list[dict]) -> list[dict]:
        """
        Checks rows against foreign key restraints and removes any rows that would violate them
        """

        fks = table.foreign_keys

        valid_rows = []
        for row in rows:
            is_valid_row = True
            for fk in fks:
                fk_value = row.get(fk.parent.name)
                if self.is_valid_foreign_key(db_dump, fk, row.get(fk.parent.name)):
                    continue

                is_valid_row = False
                self.logger.warning(
                    f"Removing row from table {table.name} because of invalid foreign key {fk.parent.name}: {fk_value}"
                )
                self.logger.warning(f"Row: {row}")
                break

            if is_valid_row:
                valid_rows.append(row)

        return valid_rows

    def dump_schema(self) -> dict:
        """
        Returns the schema of the SQLAlchemy database as a python dictionary. This dictionary is wrapped by
        jsonable_encoder to ensure that the object can be converted to a json string.
        """
        with self.engine.connect() as connection:
            self.meta.reflect(bind=self.engine)

            all_tables = self.meta.tables.values()

            results = {
                **{table.name: [] for table in all_tables},
                "alembic_version": [
                    dict(row) for row in connection.execute(text("SELECT * FROM alembic_version")).mappings()
                ],
            }

            return jsonable_encoder(results)

    def dump(self) -> dict[str, list[dict]]:
        """
        Returns the entire SQLAlchemy database as a python dictionary. This dictionary is wrapped by
        jsonable_encoder to ensure that the object can be converted to a json string.
        """

        # run database fixes first so we aren't backing up bad data
        with self.session_maker() as session:
            try:
                fix_migration_data(session)
            except Exception:
                self.logger.error("Error fixing migration data during export; continuing anyway")

        with self.engine.connect() as connection:
            self.meta.reflect(bind=self.engine)  #  http://docs.sqlalchemy.org/en/rel_0_9/core/reflection.html

            result = {
                table.name: [dict(row) for row in connection.execute(table.select()).mappings()]
                for table in self.meta.tables.values()
            }

        return jsonable_encoder(result)

    def restore(self, db_dump: dict, install_files: Callable[[], None]) -> None:
        if not isinstance(db_dump, dict):
            raise ValueError("Backup database must contain a table map")

        alembic_data = db_dump.get("alembic_version")
        if (
            not isinstance(alembic_data, list)
            or len(alembic_data) != 1
            or not isinstance(alembic_data[0], dict)
            or not isinstance(version := alembic_data[0].get("version_num"), str)
            or not version
        ):
            raise ValueError("Backup does not contain a database schema version")

        alembic_cfg_path = os.getenv("ALEMBIC_CONFIG_FILE", default=str(ALEMBIC_DIR / "alembic.ini"))
        if not path.isfile(alembic_cfg_path):
            raise ValueError("Provided Alembic config path does not exist")

        alembic_cfg = Config(alembic_cfg_path)
        alembic_cfg.attributes["transactional_restore"] = True
        directory = script.ScriptDirectory.from_config(alembic_cfg)
        directory.get_revision(version)
        needs_upgrade = set(directory.get_heads()) != {version}
        data = self.convert_types({table: rows for table, rows in db_dump.items() if table != "alembic_version"})

        try:
            with self.engine.connect() as connection:
                sqlite = connection.dialect.name == "sqlite"
                if sqlite:
                    # SQLite ignores changes to this pragma inside a database transaction.
                    connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
                    connection.commit()

                with connection.begin():
                    if sqlite:
                        # sqlite3 legacy transaction mode does not begin a transaction for DDL.
                        connection.exec_driver_sql("BEGIN IMMEDIATE")

                    self._drop_all(connection)
                    alembic_cfg.attributes["connection"] = connection
                    command.upgrade(alembic_cfg, version)
                    self._import_data(connection, data)

                    # Some migrations inspect recipe files on disk.
                    install_files()
                    if needs_upgrade:
                        command.upgrade(alembic_cfg, "head")

                    # Some data fixes commit or roll back. Keep those changes in the restore transaction.
                    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                        if not get_repositories(session, group_id=None, household_id=None).users.get_all():
                            init_db.init_db(session)
                        elif needs_upgrade:
                            fix_migration_data(session)
                            fix_group_with_no_name(session)
                        session.commit()
        finally:
            self.engine.dispose()

    def _import_data(self, connection: Connection, data: dict) -> None:
        meta = MetaData()
        meta.reflect(bind=connection)
        missing_tables = set(meta.tables) - data.keys() - {"alembic_version"}
        if missing_tables:
            raise ValueError(f"Backup is missing database tables: {', '.join(sorted(missing_tables))}")

        is_postgres = connection.dialect.name == "postgresql"
        if is_postgres:
            connection.execute(text("SET LOCAL session_replication_role = 'replica'"))

        for table_name, rows in data.items():
            if rows:
                table = meta.tables[table_name]
                valid_rows = self.clean_rows(data, table, rows)
                connection.execute(table.delete())
                if valid_rows:
                    connection.execute(insert(table), valid_rows)

        if is_postgres:
            connection.execute(text("SET LOCAL session_replication_role = 'origin'"))
            self._restore_sequences(connection)

    def _restore_sequences(self, connection: Connection) -> None:
        # Restore postgres sequence numbers
        sequences = [
            ("api_extras_id_seq", "api_extras"),
            ("group_meal_plans_id_seq", "group_meal_plans"),
            ("ingredient_food_extras_id_seq", "ingredient_food_extras"),
            ("invite_tokens_id_seq", "invite_tokens"),
            ("long_live_tokens_id_seq", "long_live_tokens"),
            ("notes_id_seq", "notes"),
            ("password_reset_tokens_id_seq", "password_reset_tokens"),
            ("recipe_assets_id_seq", "recipe_assets"),
            ("recipe_ingredient_ref_link_id_seq", "recipe_ingredient_ref_link"),
            ("recipe_nutrition_id_seq", "recipe_nutrition"),
            ("recipe_settings_id_seq", "recipe_settings"),
            ("recipes_ingredients_id_seq", "recipes_ingredients"),
            ("server_tasks_id_seq", "server_tasks"),
            ("shopping_list_extras_id_seq", "shopping_list_extras"),
            ("shopping_list_item_extras_id_seq", "shopping_list_item_extras"),
        ]

        sql = "\n".join([f"SELECT SETVAL('{seq}', (SELECT MAX(id) FROM {table}));" for seq, table in sequences])
        connection.execute(text(dedent(sql)))

    def _drop_all(self, connection: Connection) -> None:
        """Drops all data from the database"""
        from sqlalchemy import inspect
        from sqlalchemy.schema import DropConstraint, DropTable, MetaData, Table

        # Inspect the open connection, not the engine: inspecting the engine checks out a
        # second connection that is only released when the inspector is garbage collected.
        inspector = inspect(connection)

        # We need to re-create a minimal metadata with only the required things to
        # successfully emit drop constraints and tables commands for postgres (based
        # on the actual schema of the running instance)
        meta = MetaData()
        tables = []
        all_fkeys = []
        for table_name in inspector.get_table_names():
            fkeys = []

            for fkey in inspector.get_foreign_keys(table_name):
                if not fkey["name"]:
                    continue

                fkeys.append(ForeignKeyConstraint((), (), name=fkey["name"]))

            tables.append(Table(table_name, meta, *fkeys))
            all_fkeys.extend(fkeys)

        if self.engine.dialect.name == "postgresql":
            # Only pg needs foreign key dropping
            for fkey in all_fkeys:
                connection.execute(DropConstraint(fkey))

            for table in tables:
                connection.execute(DropTable(table))
            # I have no idea how to drop all custom types with sqlalchemy
            # Since we only have one, this will have to do for now
            connection.execute(text("DROP TYPE IF EXISTS authmethod"))
        else:
            for table in tables:
                connection.execute(DropTable(table))
