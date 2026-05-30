import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.conf import settings

MAX_UPLOAD_SIZE = 100 * 1024 * 1024
SQLITE_EXT = ".sqlite3"
POSTGRES_EXT = ".dump"
SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_-]+\.(sqlite3|dump)$")


class BackupError(Exception):
    pass


@dataclass(frozen=True)
class BackupFile:
    name: str
    path: Path
    size: int
    modified: datetime
    size_display: str


@dataclass(frozen=True)
class RestoreResult:
    restored_backup: Path
    pre_restore_backup: Path


def backup_dir():
    path = settings.BASE_DIR / "backups"
    path.mkdir(exist_ok=True)
    return path


def database_kind():
    engine = settings.DATABASES["default"].get("ENGINE", "")
    if "postgresql" in engine or "postgres" in engine:
        return "postgresql"
    if "sqlite3" in engine:
        return "sqlite"
    return "unsupported"


def allowed_extension(kind=None):
    kind = kind or database_kind()
    return POSTGRES_EXT if kind == "postgresql" else SQLITE_EXT


def safe_backup_path(filename, kind=None):
    filename = (filename or "").strip()
    if not SAFE_FILENAME_RE.match(filename):
        return None
    if not filename.lower().endswith(allowed_extension(kind)):
        return None

    root = backup_dir().resolve()
    path = (root / filename).resolve()
    if root != path and root not in path.parents:
        return None
    return path


def list_backups(kind=None, limit=20):
    ext = allowed_extension(kind)
    files = sorted(
        backup_dir().glob(f"*{ext}"),
        key=lambda file: file.stat().st_mtime,
        reverse=True,
    )[:limit]
    return [_backup_file(file) for file in files]


def create_backup(prefix="tracker_backup"):
    kind = database_kind()
    if kind == "postgresql":
        return _create_postgres_backup(prefix)
    if kind == "sqlite":
        return _create_sqlite_backup(prefix)
    raise BackupError("Database backups are only supported for SQLite and PostgreSQL.")


def save_uploaded_backup(uploaded):
    ext = allowed_extension()
    if not uploaded:
        raise BackupError("Please select a backup file.")
    if not uploaded.name.lower().endswith(ext):
        raise BackupError(f"Only {ext} backup files are allowed.")
    if uploaded.size > MAX_UPLOAD_SIZE:
        raise BackupError("File too large (max 100 MB).")

    path = safe_backup_path(uploaded.name)
    if not path:
        raise BackupError("Invalid filename.")

    with open(path, "wb") as destination:
        for chunk in uploaded.chunks():
            destination.write(chunk)
    return _backup_file(path)


def restore_backup(filename):
    kind = database_kind()
    backup_path = safe_backup_path(filename, kind)
    if not backup_path or not backup_path.exists():
        raise BackupError(f"Backup file not found or invalid: {filename}")

    if kind == "postgresql":
        return _restore_postgres_backup(backup_path)
    if kind == "sqlite":
        return _restore_sqlite_backup(backup_path)
    raise BackupError("Database restore is only supported for SQLite and PostgreSQL.")


def _create_sqlite_backup(prefix):
    db_path = _sqlite_db_path()
    if not db_path.exists():
        raise BackupError(f"No SQLite database found at {db_path}")

    backup_path = backup_dir() / f"{prefix}_{_timestamp()}{SQLITE_EXT}"
    shutil.copy2(db_path, backup_path)
    return _backup_file(backup_path)


def _restore_sqlite_backup(backup_path):
    db_path = _sqlite_db_path()
    pre_restore = backup_dir() / f"pre_restore_{_timestamp()}{SQLITE_EXT}"
    if db_path.exists():
        shutil.copy2(db_path, pre_restore)
    shutil.copy2(backup_path, db_path)
    return RestoreResult(restored_backup=backup_path, pre_restore_backup=pre_restore)


def _create_postgres_backup(prefix):
    backup_path = backup_dir() / f"{prefix}_{_timestamp()}{POSTGRES_EXT}"
    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-acl",
        "--file",
        str(backup_path),
    ]
    _run_postgres_command(command, "pg_dump")
    return _backup_file_from_path(backup_path)


def _restore_postgres_backup(backup_path):
    pre_restore = _create_postgres_backup("pre_restore").path
    command = [
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-acl",
        "--dbname",
        _postgres_database_name(),
        str(backup_path),
    ]
    _run_postgres_command(command, "pg_restore")
    return RestoreResult(restored_backup=backup_path, pre_restore_backup=pre_restore)


def _run_postgres_command(command, tool_name):
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=_postgres_env(),
        )
    except FileNotFoundError as exc:
        raise BackupError(
            f"{tool_name} is not installed. Install PostgreSQL client tools on the server."
        ) from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise BackupError(f"{tool_name} failed: {message}") from exc


def _postgres_env():
    parsed = _parsed_database_url()
    query = parse_qs(parsed.query)
    env = os.environ.copy()
    env.update(
        {
            "PGHOST": parsed.hostname or "",
            "PGPORT": str(parsed.port or 5432),
            "PGDATABASE": _postgres_database_name(parsed),
            "PGUSER": unquote(parsed.username or ""),
            "PGPASSWORD": unquote(parsed.password or ""),
            "PGSSLMODE": query.get("sslmode", [os.environ.get("PGSSLMODE", "require")])[0],
        }
    )
    return env


def _postgres_database_name(parsed=None):
    parsed = parsed or _parsed_database_url()
    return unquote(parsed.path.lstrip("/"))


def _parsed_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise BackupError("DATABASE_URL is required for PostgreSQL backups.")

    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise BackupError("DATABASE_URL must be a PostgreSQL connection URL.")
    if not parsed.hostname or not parsed.path.strip("/"):
        raise BackupError("DATABASE_URL is missing a host or database name.")
    return parsed


def _sqlite_db_path():
    name = settings.DATABASES["default"].get("NAME") or (settings.BASE_DIR / "db.sqlite3")
    path = Path(name)
    if not path.is_absolute():
        path = settings.BASE_DIR / path
    return path


def _backup_file(path):
    return BackupFile(
        name=path.name,
        path=path,
        size=path.stat().st_size,
        modified=datetime.fromtimestamp(path.stat().st_mtime),
        size_display=_fmt_size(path.stat().st_size),
    )


def _backup_file_from_path(path):
    if path.exists():
        return _backup_file(path)
    return BackupFile(
        name=path.name,
        path=path,
        size=0,
        modified=datetime.now(),
        size_display=_fmt_size(0),
    )


def _fmt_size(bytes_val):
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
