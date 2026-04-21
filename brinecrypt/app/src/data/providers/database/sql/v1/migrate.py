"""
Schema version 1 migration module

Version 1 is the bootstrap/initial schema, so there's no migration to perform.
This module exists for consistency and to satisfy the migration framework.
"""

CURRENT_VERSION = 1
BREAKING = False


def migrate(from_version: int, conn):
    """
    Migrate to version 1.

    Since v1 is the bootstrap version, this is a no-op.
    The bootstrap is handled by bootstrap_schema.sql.

    Args:
        from_version: Source schema version (should be 0)
        conn: Database connection
    """
    # Version 1 is bootstrap - no migration needed
    # The bootstrap_schema.sql handles initial creation
    pass
