from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import os
import uuid
import json
import asyncio

from .simulator import DigitalTwinSimulator

router = APIRouter(prefix="/climate-time-machine", tags=["Climate Time Machine"])

class SimulationRequest(BaseModel):
    event_description: str
    years: int = 5

class SimulationResponse(BaseModel):
    message: str
    video_url: str

# Store active simulations
SIMULATION_RESULTS = {}

@router.post("/simulate", response_model=SimulationResponse)
async def trigger_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    sim_id = str(uuid.uuid4())
    SIMULATION_RESULTS[sim_id] = {"status": "running", "logs": []}
    
    background_tasks.add_task(run_simulation_task, sim_id, request)
    
    return SimulationResponse(
        message=f"Simulation started (ID: {sim_id}). Check status at/climate-time-machine/status/{sim_id}",
        video_url=f"http://localhost:8000/media/videos/simulation_{sim_id}.gif"
    )

def run_simulation_task(sim_id: str, request: SimulationRequest):
    """Background task to run simulation."""
    try:
        def log_step(msg: str):
            if sim_id in SIMULATION_RESULTS:
                 if "logs" not in SIMULATION_RESULTS[sim_id]:
                     SIMULATION_RESULTS[sim_id]["logs"] = []
                 SIMULATION_RESULTS[sim_id]["logs"].append(msg)

        api_key = os.getenv("GOOGLE_API_KEY")
        sim = DigitalTwinSimulator(google_api_key=api_key)
        
        # Run simulation with logging
        result = sim.run_simulation(event_description=request.event_description, log_callback=log_step)
        
        # Process individual scenarios for the results
        processed_scenarios = []
        import shutil
        artifacts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", "artifacts"))
        
        if "scenarios" in result:
            for i, scenario in enumerate(result["scenarios"]):
                s_video_path = scenario.get("video_path")
                s_url = None
                
                if s_video_path and os.path.exists(s_video_path):
                     s_filename = f"simulation_{sim_id}_scenario_{i}.gif"
                     s_new_path = os.path.join(artifacts_root, s_filename)
                     shutil.move(s_video_path, s_new_path)
                     s_url = f"http://localhost:8000/media/videos/{s_filename}"
                
                processed_scenarios.append({
                    "title": scenario.get("title"),
                    "analysis": scenario.get("general_analysis"),
                    "domain_reports": scenario.get("domain_reports"),
                    "video_url": s_url
                })

        video_path = result.get("combined_video_path")
        
        if video_path and os.path.exists(video_path):
             new_filename = f"simulation_{sim_id}.gif"
             new_path = os.path.join(artifacts_root, new_filename)
             
             shutil.move(video_path, new_path)
             
             url = f"http://localhost:8000/media/videos/{new_filename}"
             
             # Atomic update of result
             SIMULATION_RESULTS[sim_id]["status"] = "completed"
             SIMULATION_RESULTS[sim_id]["url"] = url
             SIMULATION_RESULTS[sim_id]["scenarios"] = processed_scenarios
        else:
             SIMULATION_RESULTS[sim_id]["status"] = "completed" # Completed even if combined failed? Or failed?
             # Partial success if scenarios exist
             if processed_scenarios:
                 SIMULATION_RESULTS[sim_id]["url"] = None
                 SIMULATION_RESULTS[sim_id]["scenarios"] = processed_scenarios
             else:
                 SIMULATION_RESULTS[sim_id]["status"] = "failed"
                 SIMULATION_RESULTS[sim_id]["error"] = "No output generated"
             
    except Exception as e:
        SIMULATION_RESULTS[sim_id]["status"] = "failed"
        SIMULATION_RESULTS[sim_id]["error"] = str(e)


@router.get("/status/{sim_id}")
async def get_simulation_status(sim_id: str):
    return SIMULATION_RESULTS.get(sim_id, {"status": "not_found"})
