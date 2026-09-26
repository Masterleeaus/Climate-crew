
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.agents.deep_research.router import router, get_deep_research_module, ResearchRequest, ResearchResponse

# Create a test app
app = FastAPI()
app.include_router(router)

# Mock the orchestrator
mock_dro = MagicMock()
mock_result = {
    "report": "This is a mock deep research report.",
    "sources": [{"title": "Test Source", "url": "http://test.com", "type": "web"}]
}
mock_dro.run_deep_research.return_value = mock_result

# Mock the dependency
def mock_get_deep_research_module():
    return mock_dro

# Override the dependency
app.dependency_overrides[get_deep_research_module] = mock_get_deep_research_module

client = TestClient(app)

def test_deep_research_endpoint():
    print("\n--- Testing Deep Research Endpoint ---")
    
    payload = {
        "query": "Test query for deep research"
    }
    
    print(f"Sending POST /deep-research/ with payload: {payload}")
    
    response = client.post("/deep-research/", json=payload)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["report"] == "This is a mock deep research report."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["title"] == "Test Source"
    
    # Verify orchestrator was called
    mock_dro.run_deep_research.assert_called_once_with("Test query for deep research")
    print("✅ Deep research endpoint verified via mock!")

if __name__ == "__main__":
    test_deep_research_endpoint()
