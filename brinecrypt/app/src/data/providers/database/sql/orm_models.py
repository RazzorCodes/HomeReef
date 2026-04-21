from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Main(Base):
    __tablename__ = "main"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(
        String,
        CheckConstraint("type IN ('db-per', 'file-local')", name="check_type"),
        nullable=False,
    )
    uri: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    contents: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship to ext_file_metadata
    file_metadata: Mapped[Optional["ExtSyncMetadata"]] = relationship(
        "ExtSyncMetadata", back_populates="main_record", uselist=False
    )


class ExtSyncMetadata(Base):
    __tablename__ = "ext_sync_metadata"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("main.id"), primary_key=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sync: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship back to main
    main_record: Mapped["Main"] = relationship("Main", back_populates="file_metadata")


class SchemaVersion(Base):
    __tablename__ = "schema_version"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    label: Mapped[str] = mapped_column(
        String,
        CheckConstraint(
            "label IN ('release', 'stable', 'experimental', 'dev')", name="check_label"
        ),
        nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
