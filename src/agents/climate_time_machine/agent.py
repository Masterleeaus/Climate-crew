import os
import time
import json
import cv2
import numpy as np
from typing import List, Dict, Callable, Optional, Any
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

from ..core import BaseAgent
from langchain_core.tools import tool

class ClimateTimeMachineAgent(BaseAgent):
    def __init__(self, google_api_key: str = None, memory_manager: Any = None):
        super().__init__("ClimateTimeMachineAgent", google_api_key, memory_manager, model_name="gemini-2.0-flash")
        self.genai_client = genai.Client(api_key=google_api_key or os.getenv("GOOGLE_API_KEY"))

    def get_tools(self) -> List[Callable]:
        return []

    def get_system_prompt(self) -> str:
        return "You are the Climate Time Machine. Simulate future climate scenarios."

    def run_simulation(self, event: str) -> str:
        scenarios = self._generate_scenarios(event)
        
        results = []
        for scenario in scenarios:
            title = scenario.get("title", "Unknown")
            prompt = scenario.get("image_prompt", "")
            analysis = scenario.get("analysis", "")
            
            video_path = self._create_scenario_video(title, prompt)
            
            results.append({
                "title": title,
                "analysis": analysis,
                "video_path": video_path
            })
            
        report = f"# Climate Time Machine Simulation: {event}\n\n"
        for res in results:
            report += f"## Scenario: {res['title']}\n"
            report += f"**Analysis**: {res['analysis']}\n"
            report += f"**Simulation Video**: {res['video_path']}\n\n"
            
        return report

    def _generate_scenarios(self, event: str) -> List[Dict]:
        prompt = f"""
        Analyze the climate event: "{event}".
        Generate 3 distinct future scenarios:
        1. Best Case (Mitigation succeeds)
        2. Worst Case (Runaway feedback loops)
        3. Most Likely (Business as usual)
        
        For each, provide:
        - "title"
        - "image_prompt": A highly detailed prompt for generating a photorealistic image of this future state.
        - "analysis": A scientific explanation of why this happens.
        
        Return valid JSON list of objects.
        """
        
        response = self.genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    def _create_scenario_video(self, title: str, base_prompt: str) -> str:
        frames_dir = f"artifacts/timelapse_{int(time.time())}"
        os.makedirs(frames_dir, exist_ok=True)
        
        frame_paths = []
        for year in range(1, 6): 
            year_prompt = f"{base_prompt}, Year {2025 + year}, evolution of the event, photorealistic, 4k"
            
            try:
                img_resp = self.genai_client.models.generate_images(
                    model='imagen-3.0-generate-001',
                    prompt=year_prompt,
                    config=types.GenerateImagesConfig(number_of_images=1)
                )
                
                if img_resp.generated_images:
                    img_bytes = img_resp.generated_images[0].image.image_bytes
                    img = Image.open(BytesIO(img_bytes))
                    
                    path = os.path.join(frames_dir, f"frame_{year}.png")
                    img.save(path)
                    frame_paths.append(path)
            except Exception as e:
                print(f"Frame gen failed: {e}")
                
        if not frame_paths:
            return "Failed to generate video."
            
        video_filename = f"Climate_Sim_{title.replace(' ', '_')}.mp4"
        video_path = os.path.join("artifacts", video_filename)
        
        first_frame = cv2.imread(frame_paths[0])
        height, width, _ = first_frame.shape
        video = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 1.0, (width, height))
        
        for p in frame_paths:
            video.write(cv2.imread(p))
            
        video.release()
        return video_path
