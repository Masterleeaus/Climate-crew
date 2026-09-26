import sys
import os
import logging
from dotenv import load_dotenv

# Load env vars for Qdrant config
load_dotenv()
os.environ["FORCE_LOCAL_EMBEDDINGS"] = "true"

# Add src to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.tools.rag_tool import search_climate_knowledge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_tool():
    logger.info("--- Testing ClimateKnowledgeSearchTool ---")
    
    # 1. Test Search
    query = "strategies used to adapt to climate change"
    logger.info(f"Querying: '{query}'")
    
    result = search_climate_knowledge.invoke({"query": query, "limit": 2})
    
    logger.info("\nSearch Results:")
    logger.info(result)
    
    # Verification check
    if "No relevant information found" in result:
        logger.warning("Test Warning: RAG might not have data. Did you run 'ingest_hf_data.py'?")
    elif "Error" in result:
        logger.error("Test Failed: Tool execution error.")
    else:
        logger.info("Test Passed: Results retrieved successfully.")

if __name__ == "__main__":
    test_rag_tool()
