from typing import List, Dict, Callable, Optional, Any
import logging
import os
from datetime import datetime

from .base import BaseAgent
from .deep_research.orchestrator import DeepResearchOrchestrator
from .wildfire_agent import WildfireAgent, get_fire_map_by_coordinates
from ..reporting.pdf_generator import PDFReportGenerator
from ..tools.rag_tool import search_climate_knowledge
from langchain_core.tools import tool

@tool
def generate_audit_report(query: str, latitude: float, longitude: float) -> str:
    """
    Generate a full Carbon Audit PDF Report including Deep Research and Satellite Maps.
    Args:
        query: Description of the project to audit (e.g. "Audit Amazon Project Alpha").
        latitude: Project latitude.
        longitude: Project longitude.
    Returns:
        Path to the generated PDF report.
    """
    # This tool function needs access to the agent instance to call other agents.
    # However, since tools are static/stateless in this pattern, we might need a workaround 
    # or implement this logic inside the Agent's run loop itself rather than as a tool.
    # For now, we will return a placeholder string that the Agent intercepts to trigger the workflow.
    return f"TRIGGER_AUDIT: {query}||{latitude}||{longitude}"

class ClimateXAuditAgent(BaseAgent):
    """
    The Lead Auditor for ClimateX.ai.
    Orchestrates Deep Research + Evidence Gathering + Reporting.
    """
    
    def __init__(
        self, 
        google_api_key: str = None, 
        firms_api_key: str = None,
        memory_manager: Optional[Any] = None
    ):
        super().__init__("ClimateXAuditAgent", google_api_key, memory_manager=memory_manager)
        
        # Sub-orchestrator for deep textual research
        self.researcher = DeepResearchOrchestrator(
            google_api_key=google_api_key,
            # We could pass domain agents here if needed
        )
        
        # Evidence Gatherer (Truth Layer)
        self.wildfire_agent = WildfireAgent(firms_api_key=firms_api_key, google_api_key=google_api_key)
        
        # Reporter
        self.pdf_generator = PDFReportGenerator()
        
    def get_tools(self) -> List[Callable]:
        # We perform the audit logic internally, but expose a tool for the LLM to 'decide' to audit.
        # Also expose the knowledge search tool for researching adaptation strategies/targets.
        return [generate_audit_report, search_climate_knowledge]

    def get_system_prompt(self) -> str:
        return """You are the Lead Carbon Auditor for ClimateX.ai.
Your goal is to verify carbon offset projects using deep research and satellite evidence.

When asked to audit a project:
1. Identify the location (lat/lon).
2. Call generate_audit_report(query, lat, lon).
"""

    def run(self, query: str) -> str:
        # Intercept logic: standard run first
        response = super().run(query)
        
        # Check if the LLM decided to trigger an audit via the tool output pattern
        if "TRIGGER_AUDIT:" in response:
            try:
                # Parse the trigger
                trigger_data = response.split("TRIGGER_AUDIT:")[1].strip()
                trigger_data = trigger_data.split("\n")[0].strip()
                
                parts = trigger_data.split("||")
                audit_query = parts[0]
                lat = float(parts[1])
                lon = float(parts[2])
                
                result = self.perform_full_audit(audit_query, lat, lon)
                return f"Audit Complete. Report generated: {result['pdf_url']}\nSummary: {result['summary'][:200]}..."
            except Exception as e:
                return f"Failed to parse audit trigger: {e}"
        
        return response

    def perform_full_audit(self, query: str, lat: float, lon: float) -> Dict[str, Any]:
        self.log(f"Starting Full Audit for: {query} at ({lat}, {lon})")
        
        # 1. Deep Research (Text)
        self.log("Phase 1: Deep Research (Evidence Gathering)")
        research_context = f"Investigate carbon project verification, deforestation risks, and fire history for {query} at coordinates {lat}, {lon}."
        final_report_text = self.researcher.run_deep_research(research_context)
        
        # Handle dict return from researcher if applicable, otherwise assume string or extract
        if isinstance(final_report_text, dict):
            final_report_text = final_report_text.get("report", str(final_report_text))

        # 2. Visual Evidence (Maps)
        self.log("Phase 2: Satellite Evidence (Truth Layer)")
        map_paths = []
        try:
            # Generate Fire Map (Radius 50km)
            map_result_str = get_fire_map_by_coordinates.invoke({"latitude": lat, "longitude": lon, "radius_km": 50.0})
            
            if "artifacts/" in map_result_str:
                import re
                match = re.search(r"(artifacts/[^\s\)]+)", map_result_str)
                if match:
                    map_paths.append(match.group(1))
                    self.log(f"Generated Map: {match.group(1)}")
                    
        except Exception as e:
            self.log(f"Warning: Failed to generate map: {e}")

        # 3. Generate PDF
        self.log("Phase 3: Generating PDF Report")
        pdf_path = self.pdf_generator.generate_audit_report(
            query=query,
            content=final_report_text,
            map_images=map_paths
        )
        
        filename = os.path.basename(pdf_path)
        download_url = f"http://localhost:8000/media/reports/{filename}"
        
        # Calculate a mock compliance score based on simple heuristics (e.g. fire detected = lower score)
        compliance_score = 85
        if map_paths: # If map generated successfully (implying data found), maybe adjust?
            # Basic logic: if keywords "fire" or "deforestation" in report, lower score
            if "fire" in final_report_text.lower() or "deforestation" in final_report_text.lower():
                compliance_score = 45
            else:
                compliance_score = 92
        
        return {
            "status": "complete",
            "compliance_score": compliance_score,
            "summary": final_report_text,
            "pdf_url": download_url,
            "evidence_count": len(map_paths)
        }
