import sys
import os
import logging
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_sources.huggingface_loader import HuggingFaceLoader
from src.rag.rag_manager import RAGManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    
    # Force use of local embeddings (sentence-transformers)
    # Force use of local embeddings (sentence-transformers)
    os.environ["FORCE_LOCAL_EMBEDDINGS"] = "true"
    logger.info("Enabled FORCE_LOCAL_EMBEDDINGS to use all-MiniLM-L6-v2")
    
    # 1. Initialize Loader and RAG
    hf_loader = HuggingFaceLoader()
    # Initialize RAG Manager (ensure you have QDRANT_URL and GOOGLE_API_KEY in .env)
    rag_manager = RAGManager(
        collection_name="convolve_mas_documents",
        enable_memory=False # For pure data ingestion, we might not need memory manager overhead
    )
    
    # FORCE DELETE collection to handle dimension mismatches (e.g., 3072 vs 384)
    if os.getenv("QDRANT_URL"):
        try:
            from qdrant_client import QdrantClient
            q_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
            # q_client.delete_collection("convolve_mas_documents")
            # logger.info("Deleted existing 'convolve_mas_documents' collection to force recreation.")
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")
    
    # 2. Ingest Text Data (e.g., Targets GHG)
    logger.info("--- Starting Text Ingestion ---")
    documents = hf_loader.load_text_dataset(
        dataset_name="mwong/climate-evidence-related",
        split="train",
        format_string="Claim: {claim}\nEvidence: {evidence}",
    )
    
    if documents:
        rag_manager.index_documents(documents)
        logger.info(f"Ingested {len(documents)} documents from targets_ghg")
    else:
        logger.warning("No documents loaded from targets_ghg. Check column names.")

   

if __name__ == "__main__":
    main()
