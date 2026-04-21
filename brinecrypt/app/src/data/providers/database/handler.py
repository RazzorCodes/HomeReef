from datetime import datetime

from sqlalchemy import case, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import desc

from data.model.data_object import DataObject, DataObjectSync
from data.providers.data_provider import DataHandler
from data.providers.database.configuration import DatabaseHandlerConfiguration
from data.providers.database.sql.engine import create_db_engine, init_database
from data.providers.database.sql.orm_models import ExtSyncMetadata, Main
from misc.logger import logger


class DatabaseHandler(DataHandler):
    __db_handler_count = 0

    def __init__(self, configuration: DatabaseHandlerConfiguration):

        if not configuration or not configuration.validate():
            raise ValueError("Invalid configuration")

        super().__init__(
            configuration.name,  # type: ignore[arg-type] - validate handles None case
            DatabaseHandler,
        )

        try:
            self.engine = create_db_engine(configuration.location)  # type: ignore[arg-type] - validate handles None case
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

        init_database(self.engine)

    def _query(self, uri: str) -> DataObject | DataObjectSync | None:
        """Query database using ORM"""
        with Session(self.engine) as session:
            exact = case((Main.uri == uri, uri), else_=None)
            contains = case((Main.uri.contains(uri), uri), else_=None)

            stmt = (
                select(Main)
                .where(Main.uri.contains(uri))
                .order_by(desc(exact), desc(contains))
            )

            result = session.execute(stmt).first()

            if not result:
                return None

            if result.tags.contains("sync"):
                stmt = select(ExtSyncMetadata).where(ExtSyncMetadata.id == result.id)
                metadata = session.execute(stmt).first()
                if metadata:
                    return DataObjectSync(
                        name=result.name,
                        tags=result.tags,
                        data=result.contents,
                        created_at=result.created_at,
                        sync=metadata.sync,
                        last_update=metadata.last_update,
                        path=metadata.path,
                    )

            return DataObject(
                name=result.name,
                tags=result.tags,
                data=result.contents,
                created_at=result.created_at,
            )

    def _register(self, object: DataObject) -> str | None:
        """Register or update a data object using ORM"""
        with Session(self.engine) as session:
            if isinstance(object.data, bytes):
                contents = object.data.decode()
            elif isinstance(object.data, str):
                contents = object.data
            else:
                contents = None

            existing = session.query(Main).filter_by(uri=object.name).first()
            if existing:
                existing.tags = object.tags
                existing.contents = contents
                existing.updated_at = datetime.now()
            else:
                main_record = Main(
                    type="db-per",
                    uri=object.name,
                    tags=object.tags,
                    contents=contents,
                    updated_at=datetime.now(),
                )
                if isinstance(object, DataObjectSync):
                    # these records do not seem to update
                    main_record.file_metadata = ExtSyncMetadata(
                        address=object.path,
                        sync=object.sync,
                        created_at=datetime.now(),
                    )
                session.add(main_record)

            session.commit()
            return object.name
