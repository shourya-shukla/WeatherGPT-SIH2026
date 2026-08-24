from fastapi import APIRouter, HTTPException
from ..services.weather import weather_service
from ..services.alerts import advisories
from ..services.assistant import assistant_service
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1")
@router.get("/health")
async def health(): return {"status":"ok"}
@router.get("/geocode")
async def geocode(q:str):
    try: return await weather_service.locate(q)
    except ValueError as e: raise HTTPException(404, str(e))
@router.get("/weather/current")
async def current(location:str="New Delhi"):
    try: loc=await weather_service.locate(location); data,src=await weather_service.current(loc); return {"location":loc,"weather":data,"source":src}
    except ValueError as e: raise HTTPException(404, str(e))
@router.get("/weather/forecast")
async def forecast(location:str="New Delhi"):
    try: loc=await weather_service.locate(location); data,src=await weather_service.forecast(loc); return {"location":loc,"forecast":data,"alerts":advisories(data),"source":src}
    except ValueError as e: raise HTTPException(404, str(e))
@router.post("/chat", response_model=ChatResponse)
async def chat(req:ChatRequest):
    try:
        answer,tool,data,src=await assistant_service.respond(req.message, req.location)
        return {"answer":answer,"tool":tool,"data":data,"source":src}
    except ValueError as e: raise HTTPException(404, str(e))
