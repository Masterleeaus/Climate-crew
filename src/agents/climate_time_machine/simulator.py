import os
import time
import re
from typing import List, Dict, Any, Optional
from google import genai
from .base import ClimateBaseAgent
from .scenarios import ScenarioGenerator
from .visualizer import ClimateVisualizer

from ..air_quality_agent import AirQualityAgent
from ..biodiversity_agent import BiodiversityAgent
from ..wildfire_agent import WildfireAgent
from ..flood_agent import FloodAgent
from ..deforestation_agent import DeforestationAgent
from ..climate_anomaly_agent import ClimateAnomalyAgent

class DigitalTwinSimulator(ClimateBaseAgent):
    def __init__(
        self,
        name: str = "DigitalTwinsSimulator",
        google_api_key: Optional[str] = None,
        memory_manager: Any = None,
        enable_memory: bool = True
    ):
        super().__init__(name, google_api_key, memory_manager, enable_memory)
        self.client = genai.Client(api_key=self.api_key)
        self.scenario_generator = ScenarioGenerator(self.client)
        self.visualizer = ClimateVisualizer(self.client)
        
        # Domain Agents
        self.agents = {
            "Air Quality": AirQualityAgent(google_api_key, memory_manager),
            "Biodiversity": BiodiversityAgent(google_api_key, memory_manager),
            "Wildfire": WildfireAgent(google_api_key=google_api_key, memory_manager=memory_manager),
            "Flood": FloodAgent(google_api_key, memory_manager),
            "Deforestation": DeforestationAgent(google_api_key=google_api_key, memory_manager=memory_manager),
            "Climate Anomaly": ClimateAnomalyAgent(google_api_key, memory_manager)
        }

    def _get_domain_analysis(self, scenario_title: str, scenario_desc: str, log_callback=None) -> Dict[str, str]:          
        analyses = {}
        for name, agent in self.agents.items():
            msg = f"  > Consulting {name} Agent..."
            print(msg)
            if log_callback: log_callback(msg)
            
            prompt = f"""
            Analyze the following future climate scenario specifically from the perspective of {name}.
            Scenario: {scenario_title}
            Description: {scenario_desc}
            
            Provide a concise, scientific assessment of the likely consequences, risks, and critical thresholds breached.
            """
            try:
                analyses[name] = agent.run(prompt)
            except Exception as e:
                analyses[name] = f"Analysis failed: {e}"
        return analyses

    def run_simulation(self, event_description: str, log_callback=None) -> Dict[str, Any]:
        msg = f"Starting simulation for: {event_description}"
        print(msg)
        if log_callback: log_callback(msg)
        
        if log_callback: log_callback("Generating adversarial climate scenarios...")
        scenarios = self.scenario_generator.generate(event_description)
        
        simulation_results = []
        artifacts_dir = f"artifacts/simulation_{int(time.time())}"
        os.makedirs(artifacts_dir, exist_ok=True)
        
        for i, scenario in enumerate(scenarios):
            title = scenario.get("title", "Unknown Scenario")
            desc = scenario.get("analysis", "")
            msg = f"Processing scenario {i+1}/{len(scenarios)}: {title}"
            print(msg)
            if log_callback: log_callback(msg)
            
            # Sanitize title for valid Windows filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title).strip().replace(" ", "_")
            
            # 1. Visualization
            msg = f"Synthesizing frame-by-frame visualization for: {title}..."
            print(msg)
            if log_callback: log_callback(msg)
            
            prompts = scenario.get("image_prompts", [])
            image_paths = self.visualizer.generate_sequence(
                prompts, 
                os.path.join(artifacts_dir, safe_title)
            )
            
            # Using .gif extension explicitly
            video_path_input = os.path.join(artifacts_dir, f"{safe_title}.gif")
            # create_video returns the actual path used (which should be the same)
            video_path = self.visualizer.create_video(image_paths, video_path_input)
            
            if not video_path:
                 video_path = video_path_input # Fallback to prevent crash later, though it won't exist

            # 2. Domain Expert Analysis
            msg = f"Running agent-based tipping point analysis for: {title}..."
            print(msg)
            if log_callback: log_callback(msg)

            domain_reports = self._get_domain_analysis(title, desc, log_callback)
            
            msg = f"Finished analysis for scenario: {title}. Consolidating results..."
            print(msg)
            if log_callback: log_callback(msg)

            simulation_results.append({
                "title": title,
                "general_analysis": desc,
                "domain_reports": domain_reports,
                "video_path": video_path,
                "image_paths": image_paths
            })
            
        # Merge all scenario videos into one
        msg = "Finalizing visualization rendering (Merging frames)..."
        print(msg)
        if log_callback: log_callback(msg)

        all_video_paths = [r["video_path"] for r in simulation_results if r.get("video_path")]
        combined_video_path = os.path.join(artifacts_dir, "Combined_Simulation.gif")
        
        try:
            self.visualizer.merge_videos(all_video_paths, combined_video_path)
            msg = "Visualization merging complete."
            print(msg)
            if log_callback: log_callback(msg)
        except Exception as e:
            msg = f"Error merging videos: {e}"
            print(msg)
            if log_callback: log_callback(msg)

        return {
            "event": event_description,
            "scenarios": simulation_results,
            "combined_video_path": combined_video_path
        }

    def get_tools(self):
        return []

    def get_system_prompt(self):
        return "You are the Digital Twins Simulator. Your goal is to predict and visualize complex climate scenarios using advanced reasoning."
