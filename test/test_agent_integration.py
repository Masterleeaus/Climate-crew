import sys
import os
import logging
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.climatex_audit_agent import ClimateXAuditAgent
from src.agents.carbon_emissions_agent import CarbonEmissionsAgent
from src.agents.biodiversity_agent import BiodiversityAgent
from src.tools.rag_tool import search_climate_knowledge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_bindings():
    logger.info("--- Verifying Agent Tool Bindings ---")
    
    agents = [
        ClimateXAuditAgent(),
        CarbonEmissionsAgent(),
        BiodiversityAgent()
    ]
    
    all_passed = True
    
    for agent in agents:
        tools = agent.get_tools()
        tool_names = [t.name for t in tools]
        
        logger.info(f"Checking {agent.name}...")
        logger.info(f"  Tools: {tool_names}")
        
        if "search_climate_knowledge" in tool_names:
            logger.info(f"  [PASS] search_climate_knowledge is bound.")
        else:
            logger.error(f"  [FAIL] search_climate_knowledge NOT found!")
            all_passed = False
            
    if all_passed:
        logger.info("\nAll agents have the RAG tool correctly bound.")
    else:
        logger.error("\nSome agents are missing the RAG tool.")

if __name__ == "__main__":
    test_agent_bindings()
