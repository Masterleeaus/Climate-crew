import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from ..rag.rag_manager import RAGManager

logger = logging.getLogger(__name__)

# Global RAG Manager instance (singleton pattern for tools)
_rag_manager: Optional[RAGManager] = None

def get_rag_manager() -> RAGManager:
    global _rag_manager
    if _rag_manager is None:
        import os
        os.environ["FORCE_LOCAL_EMBEDDINGS"] = "true"
        
        _rag_manager = RAGManager(
            collection_name="convolve_mas_documents",
            enable_memory=True
        )
    return _rag_manager

@tool
def search_climate_knowledge(query: str, limit: int = 3) -> str:
    """
    Search the Climate Knowledge Base for information.
    Use this tool to find scientific abstracts, corporate targets, or Q&A data regarding climate change,
    adaptation strategies, or carbon emissions.
    
    Args:
        query: Specific search query (e.g., "flood adaptation strategies in urban areas").
        limit: Number of results to return (default: 3).
        
    Returns:
        A string containing the relevant text segments found.
    """
    try:
        rag = get_rag_manager()
        
        # Ensure RAG is initialized
        if not rag._ensure_initialized():
            return "Error: Knowledge Base is currently unavailable."
            
        results = rag.search(query, limit=limit)
        
        if not results:
            return "No relevant information found in the knowledge base."
            
        formatted_results = []
        for i, res in enumerate(results, 1):
            text = res.get("text", "").strip()
            source = res.get("metadata", {}).get("source", "Unknown Source")
            formatted_results.append(f"Result {i} (Source: {source}):\n{text}")
            
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error in search_climate_knowledge: {e}")
        return f"Error occurred while searching: {str(e)}"
