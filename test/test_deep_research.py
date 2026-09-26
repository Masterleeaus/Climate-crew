
import sys
import os
import pytest
from unittest.mock import MagicMock

# Add src to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.deep_research.orchestrator import DeepResearchOrchestrator
from dotenv import load_dotenv

load_dotenv()

def test_deep_research_orchestrator_init():
    orchestrator = DeepResearchOrchestrator(google_api_key=os.getenv("GOOGLE_API_KEY"))
    assert orchestrator.enricher is not None
    assert orchestrator.planner is not None
    assert orchestrator.thought_tree is not None
    assert orchestrator.synthesizer is not None

def test_pipeline_flow():
    # Mocking components to test flow without real API calls
    orch = DeepResearchOrchestrator(google_api_key=os.getenv("GOOGLE_API_KEY"))
    
    orch.enricher.enrich = MagicMock(return_value={
        "original_query": "test", 
        "disambiguated_query": "test query",
        "perspectives": ["p1"],
        "sub_questions": ["q1"]
    })
    
    orch.planner.plan = MagicMock(return_value=[
        {"topic": "t1", "description": "d1", "initial_search_queries": ["sq1"]}
    ])
    
    orch.thought_tree.initialize = MagicMock()
    orch.thought_tree.run_mcts = MagicMock(return_value=[
        {"content": "fact1"}
    ])
    
    orch.advocate.advocate = MagicMock(return_value="Valid argument")
    orch.critic.critique = MagicMock(return_value="Weak argument")
    orch.judge.judge = MagicMock(return_value='{"verdict": "ACCEPT"}')
    orch.synthesizer.synthesize = MagicMock(return_value="# Final Report")
    
    result = orch.run_deep_research("test query")
    
    assert result == "# Final Report"
    orch.enricher.enrich.assert_called_once()
    orch.thought_tree.run_mcts.assert_called_once()
    orch.synthesizer.synthesize.assert_called_once()
