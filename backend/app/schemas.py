from pydantic import BaseModel, Field
from typing import Any

class Location(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: str = "India"
    admin1: str | None = None

class SourceMeta(BaseModel):
    provider: str
    retrieved_at: str
    data_mode: str = "live"

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    location: str | None = None
    language: str = "en"

class ChatResponse(BaseModel):
    answer: str
    tool: str
    data: dict[str, Any]
    source: SourceMeta
