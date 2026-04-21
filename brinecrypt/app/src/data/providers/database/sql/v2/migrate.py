import importlib

from sqlalchemy import text

CURRENT_VERSION = 2
BREAKING = False


def migrate(from_version: int, conn):
    if BREAKING:
        raise RuntimeError("Breaking schema change")

    if from_version < CURRENT_VERSION - 1:
        mod = importlib.import_module(f"data.model.sql.v{CURRENT_VERSION - 1}.migrate")
        mod.migrate(from_version, conn)

    "<some migrate, this is not implemented and only as an example here, will be handled when v2 actually exists>"

    conn.execute(
        text("""
        INSERT INTO schema_version (version, date, label, comment)
        VALUES (2, CURRENT_TIMESTAMP, 'dev', '---')
    """)
    )
