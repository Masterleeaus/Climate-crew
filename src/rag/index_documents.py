"""
Script to index documents from the docs folder into Qdrant.
Run: python -m src.rag.index_documents
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.rag import RAGManager, DocumentLoader, TextChunker


def index_docs_folder(docs_folder: str = "docs"):
    """Index all documents from the docs folder."""
    print("=" * 60)
    print("Document Indexing for RAG")
    print("=" * 60)
    
    # Check environment variables
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    print(f"\nQDRANT_URL: {'Set' if qdrant_url else 'Not set'}")
    print(f"QDRANT_API_KEY: {'Set' if qdrant_api_key else 'Not set'}")
    print(f"GOOGLE_API_KEY: {'Set' if google_api_key else 'Not set'}")
    
    if not qdrant_url or not qdrant_api_key:
        print("\n[ERROR] Qdrant not configured. Set QDRANT_URL and QDRANT_API_KEY in .env")
        return False
    
    if not google_api_key:
        print("\n[ERROR] GOOGLE_API_KEY not set. Required for embeddings.")
        return False
    
    # Initialize components
    print("\n[1/4] Initializing components...")
    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
    rag_manager = RAGManager()
    
    # Load documents
    docs_path = project_root / docs_folder
    if not docs_path.exists():
        print(f"\n[ERROR] Docs folder not found: {docs_path}")
        return False
    
    print(f"\n[2/4] Loading documents from: {docs_path}")
    try:
        documents = loader.load_directory(str(docs_path), recursive=True)
        print(f"Loaded {len(documents)} documents")
        
        if not documents:
            print("[WARNING] No documents found in docs folder")
            return False
        
        for doc in documents:
            file_name = doc.get("metadata", {}).get("file_name", "Unknown")
            text_length = len(doc.get("text", ""))
            print(f"  - {file_name} ({text_length} characters)")
    
    except Exception as e:
        print(f"\n[ERROR] Failed to load documents: {e}")
        return False
    
    # Chunk documents
    print(f"\n[3/4] Chunking documents...")
    try:
        chunks = chunker.chunk_documents(documents)
        print(f"Created {len(chunks)} chunks")
    except Exception as e:
        print(f"\n[ERROR] Failed to chunk documents: {e}")
        return False
    
    # Index chunks
    print(f"\n[4/4] Indexing chunks into Qdrant...")
    try:
        indexed_count = rag_manager.index_documents(chunks, batch_size=10)
        print(f"Successfully indexed {indexed_count} chunks")
        
        # Get collection info
        info = rag_manager.get_collection_info()
        print(f"\nCollection info:")
        print(f"  - Name: {info.get('name')}")
        print(f"  - Points: {info.get('points_count', 0)}")
        print(f"  - Vector size: {info.get('config', {}).get('vector_size')}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Documents indexed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to index documents: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = index_docs_folder()
    sys.exit(0 if success else 1)
