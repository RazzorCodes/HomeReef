# data/db/engine.py
import importlib
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from .orm_models import Base, SchemaVersion

SQL_ROOT = Path("data/model/sql")
CURRENT_VERSION = 1


def create_db_engine(db_path: Path):
    """Create SQLAlchemy engine for the given database path"""
    return create_engine(f"sqlite:///{db_path.__str__()}", future=True)


def get_db_version(session: Session) -> int:
    """Get current database schema version using ORM"""
    try:
        result = (
            session.query(SchemaVersion).order_by(SchemaVersion.version.desc()).first()
        )
        return result.version if result else 0
    except Exception:
        return 0


def run_sql_file(conn, path: Path):
    """Run raw SQL file for bootstrap/validation"""
    sql = path.read_text(encoding="utf-8")
    conn.exec_driver_sql(sql)


def bootstrap_if_needed(conn):
    """Bootstrap database schema if needed"""
    # Check if tables exist by trying to query schema_version
    try:
        conn.execute(text("SELECT 1 FROM schema_version LIMIT 1"))
        return  # Tables already exist
    except Exception:
        pass

    # Run bootstrap SQL
    v1 = SQL_ROOT / "v1" / "bootstrap_schema.sql"
    run_sql_file(conn, v1)

    # Insert initial schema version record
    conn.execute(
        text("""
            INSERT INTO schema_version (version, date, label, comment)
            VALUES (1, CURRENT_TIMESTAMP, 'stable', 'Initial schema')
        """)
    )
    conn.commit()


def validate_schema(conn, version: int):
    """Run validation SQL files for given version"""
    vdir = SQL_ROOT / f"v{version}"
    if not vdir.exists():
        return

    for file in sorted(vdir.glob("validate_*.sql")):
        run_sql_file(conn, file)


def migrate_to_current(conn):
    """Migrate database to current version"""
    with Session(conn) as session:
        version = get_db_version(session)

    if version >= CURRENT_VERSION:
        return

    # Import and run migration
    mod = importlib.import_module(f"data.model.sql.v{CURRENT_VERSION}.migrate")
    mod.migrate(version, conn)


def init_database(engine):
    """Initialize database: bootstrap, migrate, validate"""
    # First, ensure tables are created using ORM
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        bootstrap_if_needed(conn)
        # migrate_to_current(conn)

        with Session(conn) as session:
            version = get_db_version(session)

        validate_schema(conn, version)
