import os
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.agents.deep_research.router import router as deep_research_router
from src.agents.retail_analytics.router import router as retail_router
from src.api.agents import router as agents_router
from src.api.data import router as data_router
from src.api.media import router as media_router
from src.agents.climate_time_machine.router import router as ctm_router
from src.api.global_pulse import router as global_pulse_router
from src.agents.audit_router import router as audit_router
from src.api.climate_finance import router as climate_finance_router
from src.api.news import router as news_router, get_qdrant_manager, get_news_fetcher, get_article_processor
from src.api.disaster_management import router as disaster_router

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Convolve MAS API",
    description="Multi-Agent System for Climate Intelligence & Deep Research",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(deep_research_router)
app.include_router(retail_router)
app.include_router(agents_router)
app.include_router(data_router)
app.include_router(media_router)
app.include_router(ctm_router)
app.include_router(global_pulse_router)
app.include_router(audit_router)
app.include_router(climate_finance_router)
app.include_router(news_router)
app.include_router(disaster_router)

@app.get("/")
async def root():
    return {"message": "Convolve MAS API is running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
