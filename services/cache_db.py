from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import ChatCache, Location, LocationAlias, WeatherCache

logger = logging.getLogger("weathergpt.cache_db")

# How far apart (in metres) two geocoded points can be before they're
# treated as "the same place" for caching purposes.
LOCATION_DEDUP_RADIUS_M = 1000

# How long each kind of weather response stays valid.
WEATHER_TTL_SECONDS = {
    "current": 15 * 60,       # conditions change fast
    "forecast": 60 * 60,
    "nwp": 60 * 60,
    "history": 7 * 24 * 60 * 60,  # past weather never changes
}

CHAT_SIMILARITY_THRESHOLD = float(os.getenv("CHAT_CACHE_SIMILARITY_THRESHOLD", "0.08"))


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _geog_point(latitude: float, longitude: float):
    return func.ST_GeogFromText(f"SRID=4326;POINT({longitude} {latitude})")


# ============================================================
# LOCATIONS
# ============================================================

async def get_cached_location(session: AsyncSession, city: str) -> Location | None:
    query_name = normalize(city)

    alias = await session.scalar(
        select(LocationAlias).where(LocationAlias.query_name == query_name)
    )
    if alias is None:
        return None

    return await session.get(Location, alias.location_id)


async def save_location(session: AsyncSession, city: str, coordinates: dict) -> Location:
    query_name = normalize(city)
    latitude = coordinates["latitude"]
    longitude = coordinates["longitude"]

    nearby = await session.scalar(
        select(Location)
        .where(
            func.ST_DWithin(
                Location.geom, _geog_point(latitude, longitude), LOCATION_DEDUP_RADIUS_M
            )
        )
        .limit(1)
    )

    if nearby is None:
        nearby = Location(
            name=coordinates.get("name", city),
            country=coordinates.get("country"),
            latitude=latitude,
            longitude=longitude,
            geom=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
        )
        session.add(nearby)
        await session.flush()  # assigns nearby.id

    session.add(LocationAlias(query_name=query_name, location_id=nearby.id))
    await session.commit()
    await session.refresh(nearby)
    return nearby


async def get_or_create_location_by_coords(
    session: AsyncSession, latitude: float, longitude: float
) -> Location:
    nearby = await session.scalar(
        select(Location)
        .where(
            func.ST_DWithin(
                Location.geom, _geog_point(latitude, longitude), LOCATION_DEDUP_RADIUS_M
            )
        )
        .limit(1)
    )

    if nearby is not None:
        return nearby

    nearby = Location(
        name=f"{latitude:.4f}, {longitude:.4f}",
        country=None,
        latitude=latitude,
        longitude=longitude,
        geom=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
    )
    session.add(nearby)
    await session.commit()
    await session.refresh(nearby)
    return nearby


# ============================================================
# WEATHER / FORECAST / HISTORY / NWP
# ============================================================

async def get_cached_weather(
    session: AsyncSession, location_id: int, endpoint: str, params_key: str = ""
) -> dict | None:
    stmt = select(WeatherCache).where(
        WeatherCache.location_id == location_id,
        WeatherCache.endpoint == endpoint,
        WeatherCache.params_key == params_key,
        WeatherCache.expires_at > _utcnow(),
    )
    entry = await session.scalar(stmt)
    return entry.payload if entry else None


async def save_weather_cache(
    session: AsyncSession,
    location_id: int,
    endpoint: str,
    payload: dict,
    params_key: str = "",
) -> None:
    ttl = WEATHER_TTL_SECONDS.get(endpoint, 15 * 60)
    expires_at = _utcnow() + timedelta(seconds=ttl)

    stmt = (
        pg_insert(WeatherCache)
        .values(
            location_id=location_id,
            endpoint=endpoint,
            params_key=params_key,
            payload=payload,
            expires_at=expires_at,
        )
        .on_conflict_do_update(
            constraint="uq_weather_cache_key",
            set_={
                "payload": payload,
                "expires_at": expires_at,
                "created_at": _utcnow(),
            },
        )
    )
    await session.execute(stmt)
    await session.commit()


# ============================================================
# CHAT (semantic cache)
# ============================================================

async def find_similar_chat(
    session: AsyncSession, embedding: list[float], location: str | None
) -> ChatCache | None:
    stmt = select(
        ChatCache, ChatCache.embedding.cosine_distance(embedding).label("distance")
    ).order_by(ChatCache.embedding.cosine_distance(embedding))

    if location:
        stmt = stmt.where(ChatCache.location == normalize(location))

    stmt = stmt.limit(1)

    row = (await session.execute(stmt)).first()
    if row is None:
        return None

    entry, distance = row
    if distance is not None and distance <= CHAT_SIMILARITY_THRESHOLD:
        return entry
    return None


async def register_chat_hit(session: AsyncSession, entry: ChatCache) -> None:
    entry.hits += 1
    await session.commit()


async def save_chat(
    session: AsyncSession,
    question: str,
    location: str | None,
    answer: str,
    embedding: list[float],
) -> ChatCache:
    entry = ChatCache(
        question=question,
        location=normalize(location) if location else None,
        answer=answer,
        embedding=embedding,
        hits=0,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
