import datetime
import json
import re
import shutil
import sqlite3
import tempfile
from collections.abc import Callable, Iterator
from contextlib import ExitStack, closing, contextmanager
from pathlib import Path
from zipfile import ZipFile

from mealie.core.config import get_app_settings
from mealie.core.settings.static import APP_VERSION
from mealie.services._base_service import BaseService
from mealie.services.backups_v2.alchemy_exporter import AlchemyExporter
from mealie.services.backups_v2.backup_file import BackupFile


class BackupSchemaMismatch(Exception): ...


class BackupV2(BaseService):
    EXCLUDE_DIRS = {"backups", ".temp"}
    EXCLUDE_FILES = {"mealie.db"}
    EXCLUDE_FILES_REGEX = {re.compile(r"^mealie\.log(?:\.\d+)?$")}
    EXCLUDE_EXTENTIONS = {".zip"}

    RESTORE_FILES = {".secret"}

    def __init__(self, db_url: str | None = None) -> None:
        super().__init__()

        # type - one of these has to be a string
        self.db_url: str = db_url or self.settings.DB_URL  # type: ignore

        self.db_exporter = AlchemyExporter(self.db_url)

    def _stage_sqlite_snapshot(self, incoming: Path) -> None:
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y.%m.%d")
        snapshot = incoming / f"mealie_{timestamp}.bak.db"
        # SQLite's backup API includes committed changes that are still in the WAL.
        with closing(self.db_exporter.engine.raw_connection()) as source, closing(sqlite3.connect(snapshot)) as target:
            source.driver_connection.backup(target)

    def backup(self) -> Path:
        # sourcery skip: merge-nested-ifs, reintroduce-else, remove-redundant-continue
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y.%m.%d.%H.%M.%S")
        short_hash = self.settings.GIT_COMMIT_HASH[:7]

        if APP_VERSION == "develop":
            backup_name = f"mealie_dev-{short_hash}_{timestamp}.zip"
        elif APP_VERSION == "nightly":
            backup_name = f"mealie_nightly-{short_hash}_{timestamp}.zip"
        else:
            backup_name = f"mealie_{APP_VERSION}_{timestamp}.zip"

        backup_file = self.directories.BACKUP_DIR / backup_name

        database_json = self.db_exporter.dump()

        with ZipFile(backup_file, "w") as zip_file:
            zip_file.writestr("database.json", json.dumps(database_json))

            for data_file in self.directories.DATA_DIR.glob("**/*"):
                if data_file.name in self.EXCLUDE_FILES:
                    continue

                if any(pattern.search(data_file.name) for pattern in self.EXCLUDE_FILES_REGEX):
                    continue

                if data_file.is_file() and data_file.suffix not in self.EXCLUDE_EXTENTIONS:
                    relative = data_file.relative_to(self.directories.DATA_DIR)
                    if self.EXCLUDE_DIRS.intersection(relative.parts[:-1]):
                        continue

                    zip_file.write(data_file, f"data/{relative}")

        return backup_file

    @contextmanager
    def _stage_data(self, data_path: Path) -> Iterator[Callable[[], None]]:
        # Put both copies on the live filesystem so that activation and rollback use renames.
        temp_dir = self.directories.DATA_DIR / ".temp"
        temp_dir.mkdir(exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="restore-", dir=temp_dir))
        incoming = staging / "incoming"
        previous = staging / "previous"
        rollback = ExitStack()
        preserve_staging = False

        def install() -> None:
            for replacement in sorted(incoming.iterdir()):
                destination = self.directories.DATA_DIR / replacement.name
                if destination.exists() or destination.is_symlink():
                    original = destination.rename(previous / replacement.name)
                    rollback.callback(original.rename, destination)
                replacement.rename(destination)
                rollback.callback(destination.rename, replacement)

        try:
            incoming.mkdir()
            previous.mkdir()
            for entry in data_path.iterdir():
                replacement = incoming / entry.name
                if entry.is_dir() and entry.name not in self.EXCLUDE_DIRS:
                    shutil.copytree(entry, replacement)
                elif entry.is_file() and entry.name in self.RESTORE_FILES:
                    shutil.copyfile(entry, replacement)

            if self.db_exporter.engine.dialect.name == "sqlite":
                self._stage_sqlite_snapshot(incoming)

            yield install
        except BaseException:
            try:
                rollback.close()
            except OSError:
                preserve_staging = True
                self.logger.exception("Could not roll back restored files. Recovery files are in %s", staging)
                raise
            raise
        else:
            rollback.pop_all()
        finally:
            if not preserve_staging:
                shutil.rmtree(staging, ignore_errors=True)

    def restore(self, backup_path: Path) -> None:
        self.logger.info("initializing backup restore")

        backup = BackupFile(backup_path)

        with backup as contents:
            if not contents.validate():
                self.logger.error(
                    "Invalid backup file. file does not contain required elements (data directory and database.json)"
                )
                raise ValueError("Invalid backup file")

            with self._stage_data(contents.data_directory) as install_files:
                self.db_exporter.restore(contents.read_tables(), install_files)

        # A restored .secret invalidates the cached settings.
        get_app_settings.cache_clear()
        self.logger.info("backup restore complete")
