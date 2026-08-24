from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from . import models
from .api.routes import router

app=FastAPI(title="WeatherGPT API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
@app.on_event("startup")
def startup(): Base.metadata.create_all(bind=engine)
