from datetime import datetime, timezone
from typing import Any

from geoalchemy2 import Geography
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# text-embedding-004 (Gemini) produces 768-dimensional vectors.
EMBEDDING_DIM = 768


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    # Real PostGIS geography point (SRID 4326 = WGS84 lat/lon), used
    # for ST_DWithin nearest-neighbour lookups.
    geom: Mapped[Any] = mapped_column(Geography(geometry_type="POINT", srid=4326))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    aliases: Mapped[list["LocationAlias"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    weather_entries: Mapped[list["WeatherCache"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class LocationAlias(Base):

    __tablename__ = "location_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )

    location: Mapped["Location"] = relationship(back_populates="aliases")


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )

    # "current" | "forecast" | "history" | "nwp"
    endpoint: Mapped[str] = mapped_column(String(50), index=True)

    params_key: Mapped[str] = mapped_column(String(255), default="")

    payload: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    location: Mapped["Location"] = relationship(back_populates="weather_entries")

    __table_args__ = (
        UniqueConstraint(
            "location_id", "endpoint", "params_key", name="uq_weather_cache_key"
        ),
    )


class ChatCache(Base):
    __tablename__ = "chat_cache"

    id: Mapped[int] = mapped_column(primary_key=True)

    question: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    answer: Mapped[str] = mapped_column(Text)

    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM))

    hits: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        # HNSW index over cosine distance so "nearest question" lookups
        # stay fast as the cache grows, instead of scanning every row.
        Index(
            "ix_chat_cache_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
