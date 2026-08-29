import asyncio
import os

from google import genai

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        _client = genai.Client(api_key=api_key)
    return _client


def embed_text_sync(text: str) -> list[float]:
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return list(response.embeddings[0].values)


async def embed_text(text: str) -> list[float]:
    return await asyncio.to_thread(embed_text_sync, text)
