"""
Test script for RAG functionality.
Run: python test/test_rag.py
"""

import sys
import os
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from src.rag import RAGManager, DocumentLoader, TextChunker


def test_document_loading():
    """Test document loading from docs folder."""
    print("=" * 60)
    print("Test 1: Document Loading")
    print("=" * 60)
    
    loader = DocumentLoader()
    docs_path = "docs"
    
    if not os.path.exists(docs_path):
        print(f"[SKIP] Docs folder not found: {docs_path}")
        return None
    
    try:
        documents = loader.load_directory(docs_path, recursive=True)
        print(f"[PASS] Loaded {len(documents)} documents")
        
        for doc in documents:
            file_name = doc.get("metadata", {}).get("file_name", "Unknown")
            text_length = len(doc.get("text", ""))
            print(f"  - {file_name}: {text_length} characters")
        
        return documents
    except Exception as e:
        print(f"[FAIL] Error loading documents: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_text_chunking(documents):
    """Test text chunking."""
    print("\n" + "=" * 60)
    print("Test 2: Text Chunking (Fixed-size)")
    print("=" * 60)
    
    if not documents:
        print("[SKIP] No documents to chunk")
        return None
    
    try:
        chunker = TextChunker(chunk_size=100000, chunk_overlap=2000)
        chunks = chunker.chunk_documents(documents)
        print(f"[PASS] Created {len(chunks)} chunks")
        
        if chunks:
            sample = chunks[0]
            print(f"  Sample chunk: {len(sample.get('text', ''))} characters")
            print(f"  Metadata keys: {list(sample.get('metadata', {}).keys())}")
        
        return chunks
    except Exception as e:
        print(f"[FAIL] Error chunking: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_semantic_chunking(documents):
    """Test semantic chunking."""
    print("\n" + "=" * 60)
    print("Test 2b: Semantic Chunking")
    print("=" * 60)
    
    if not documents:
        print("[SKIP] No documents to chunk")
        return None
    
    try:
        chunker = TextChunker(
            chunk_size=100000,
            chunk_overlap=2000,
            use_semantic_chunking=True,
            semantic_threshold=0.5
        )
        chunks = chunker.chunk_documents(documents)
        print(f"[PASS] Created {len(chunks)} semantic chunks")
        
        if chunks:
            sample = chunks[0]
            print(f"  Sample chunk: {len(sample.get('text', ''))} characters")
            metadata = sample.get('metadata', {})
            print(f"  Metadata keys: {list(metadata.keys())}")
            if 'chunking_method' in metadata:
                print(f"  Chunking method: {metadata['chunking_method']}")
        
        return chunks
    except Exception as e:
        print(f"[FAIL] Error semantic chunking: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_rag_indexing(chunks):
    """Test RAG indexing into Qdrant."""
    print("\n" + "=" * 60)
    print("Test 3: RAG Indexing")
    print("=" * 60)
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        print("[SKIP] Qdrant not configured")
        return None
    
    if not google_api_key:
        print("[SKIP] GOOGLE_API_KEY not set")
        return None
    
    if not chunks:
        print("[SKIP] No chunks to index")
        return None
    
    try:
        # Initialize RAG manager with all new features enabled
        rag_manager = RAGManager(
            enable_memory=True,
            use_reranker=True,
            enable_multihop=True,
            max_hops=3
        )
        indexed = rag_manager.index_documents(chunks[:5], batch_size=2)  # Test with first 5 chunks
        print(f"[PASS] Indexed {indexed} chunks")
        
        info = rag_manager.get_collection_info()
        print(f"  Collection: {info.get('name')}")
        print(f"  Points: {info.get('points_count', 0)}")
        print(f"  Features enabled:")
        print(f"    - Memory: {rag_manager.enable_memory}")
        print(f"    - Reranker: {rag_manager.use_reranker}")
        print(f"    - Multihop: {rag_manager.enable_multihop}")
        
        return rag_manager
    except Exception as e:
        print(f"[FAIL] Error indexing: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_rag_search(rag_manager):
    """Test RAG search."""
    print("\n" + "=" * 60)
    print("Test 4: RAG Search (Basic)")
    print("=" * 60)
    
    if not rag_manager:
        print("[SKIP] RAG manager not available")
        return
    
    try:
        query = "climate change"
        results = rag_manager.search(query, limit=3, use_reranker=False, use_multihop=False)
        print(f"[PASS] Found {len(results)} results for query: '{query}'")
        
        for i, result in enumerate(results, 1):
            text = result.get("text", "")[:200]
            score = result.get("score", 0.0)
            metadata = result.get("metadata", {})
            file_name = metadata.get("file_name", "Unknown")
            print(f"\n  Result {i} (score: {score:.3f}, from: {file_name}):")
            print(f"  {text}...")
        
        # Test context retrieval
        context = rag_manager.get_context(query, limit=2, include_memory=False)
        if context:
            print(f"\n[PASS] Context retrieved ({len(context)} characters)")
        else:
            print("[WARN] No context retrieved")
            
    except Exception as e:
        print(f"[FAIL] Error searching: {e}")
        import traceback
        traceback.print_exc()


def test_reranker(rag_manager):
    """Test reranker functionality."""
    print("\n" + "=" * 60)
    print("Test 5: Reranker")
    print("=" * 60)
    
    if not rag_manager:
        print("[SKIP] RAG manager not available")
        return
    
    if not rag_manager.use_reranker:
        print("[SKIP] Reranker not enabled")
        return
    
    try:
        query = "climate change impacts"
        # Search without reranker
        results_no_rerank = rag_manager.search(query, limit=5, use_reranker=False)
        # Search with reranker
        results_with_rerank = rag_manager.search(query, limit=5, use_reranker=True)
        
        print(f"[PASS] Reranker test completed")
        print(f"  Results without reranker: {len(results_no_rerank)}")
        print(f"  Results with reranker: {len(results_with_rerank)}")
        
        if results_with_rerank:
            print("\n  Top reranked results:")
            for i, result in enumerate(results_with_rerank[:3], 1):
                rerank_score = result.get("rerank_score")
                if rerank_score is not None:
                    rerank_score_str = f"{rerank_score:.6f}"
                else:
                    rerank_score_str = "N/A"
                combined_score = result.get("combined_score", result.get("score", 0.0))
                print(f"    {i}. Rerank score: {rerank_score_str}, Combined: {combined_score:.6f}")
        
    except Exception as e:
        print(f"[FAIL] Error testing reranker: {e}")
        import traceback
        traceback.print_exc()


def test_multihop_reasoning(rag_manager):
    """Test multihop reasoning."""
    print("\n" + "=" * 60)
    print("Test 6: Multihop Reasoning")
    print("=" * 60)
    
    if not rag_manager:
        print("[SKIP] RAG manager not available")
        return
    
    if not rag_manager.enable_multihop:
        print("[SKIP] Multihop reasoning not enabled")
        return
    
    try:
        # Complex query that benefits from multihop
        complex_query = "What are the impacts of climate change on biodiversity and ocean ecosystems?"
        
        # Single hop search
        results_single = rag_manager.search(complex_query, limit=5, use_multihop=False)
        
        # Multihop search
        results_multihop = rag_manager.search(complex_query, limit=5, use_multihop=True)
        
        print(f"[PASS] Multihop reasoning test completed")
        print(f"  Query: '{complex_query}'")
        print(f"  Single hop results: {len(results_single)}")
        print(f"  Multihop results: {len(results_multihop)}")
        
        if results_multihop:
            print("\n  Multihop results (showing hop info):")
            for i, result in enumerate(results_multihop[:3], 1):
                hop = result.get("hop", "N/A")
                sub_query = result.get("sub_query", "N/A")
                score = result.get("score", 0.0)
                print(f"    {i}. Hop {hop}, Score: {score:.3f}")
                if sub_query != "N/A":
                    print(f"       Sub-query: {sub_query[:60]}...")
        
    except Exception as e:
        print(f"[FAIL] Error testing multihop reasoning: {e}")
        import traceback
        traceback.print_exc()


def test_memory_integration(rag_manager):
    """Test memory integration with RAG."""
    print("\n" + "=" * 60)
    print("Test 7: Memory Integration")
    print("=" * 60)
    
    if not rag_manager:
        print("[SKIP] RAG manager not available")
        return
    
    if not rag_manager.enable_memory or not rag_manager.memory_manager:
        print("[SKIP] Memory not enabled or memory manager not available")
        return
    
    try:
        query = "climate change"
        
        # Test context with memory
        context_with_memory = rag_manager.get_context(query, limit=3, include_memory=True)
        context_without_memory = rag_manager.get_context(query, limit=3, include_memory=False)
        
        print(f"[PASS] Memory integration test completed")
        print(f"  Context without memory: {len(context_without_memory)} characters")
        print(f"  Context with memory: {len(context_with_memory)} characters")
        
        if len(context_with_memory) > len(context_without_memory):
            print("  [INFO] Memory context added additional information")
        
        # Try to add some memory
        try:
            rag_manager.memory_manager.add(
                "Climate change is causing rising sea levels and extreme weather events.",
                agent_id="rag",
                metadata={"source": "test", "topic": "climate"}
            )
            print("  [INFO] Added test memory entry")
        except Exception as e:
            print(f"  [WARN] Could not add memory: {e}")
        
    except Exception as e:
        print(f"[FAIL] Error testing memory integration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n[RAG Test Suite - Enhanced with Semantic Chunking, Rerankers, Multihop, and Mem0]\n")
    
    # Test document loading
    documents = test_document_loading()
    
    # Test fixed-size chunking
    chunks = test_text_chunking(documents)
    
    # Test semantic chunking
    semantic_chunks = test_semantic_chunking(documents)
    
    # Use fixed-size chunks for indexing (or semantic if available)
    chunks_to_index = chunks if chunks else semantic_chunks
    
    # Test indexing
    rag_manager = test_rag_indexing(chunks_to_index)
    
    # Test basic search
    test_rag_search(rag_manager)
    
    # Test reranker
    test_reranker(rag_manager)
    
    # Test multihop reasoning
    test_multihop_reasoning(rag_manager)
    
    # Test memory integration
    test_memory_integration(rag_manager)
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)
