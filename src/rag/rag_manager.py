import os
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import time
import hashlib
import numpy as np
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer, CrossEncoder
from ..prompt.prompt_loader import get_prompt_loader

logger = logging.getLogger(__name__)

GOOGLE_GENAI_AVAILABLE = True
SENTENCE_TRANSFORMERS_AVAILABLE = True


class RAGManager:
    """Manage document indexing and retrieval using Qdrant."""
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "convolve_mas_documents",
        google_api_key: Optional[str] = None,
        embedding_model: str = "gemini-embedding-001",
        use_fallback_embeddings: bool = True,
        fallback_model: str = "all-MiniLM-L6-v2",
        memory_manager: Optional[Any] = None,
        enable_memory: bool = True,
        use_reranker: bool = True,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        enable_multihop: bool = True,
        max_hops: int = 3
    ):
        """
        Initialize RAG Manager.
        
        Args:
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key
            collection_name: Name of the Qdrant collection
            google_api_key: Google API key for embeddings
            embedding_model: Gemini embedding model name
            use_fallback_embeddings: Use sentence-transformers if Google API fails
            fallback_model: Sentence-transformers model name for fallback
            memory_manager: Optional MemoryManager instance for Mem0 integration
            enable_memory: Whether to use memory for enhanced context
            use_reranker: Whether to use reranker for improved relevance
            reranker_model: Cross-encoder model for reranking
            enable_multihop: Whether to enable multihop reasoning
            max_hops: Maximum number of reasoning hops
        """
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.qdrant_path = os.getenv("QDRANT_PATH")
        self.collection_name = collection_name
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        # Force local embeddings if requested (overrides API key for embeddings only)
        if os.getenv("FORCE_LOCAL_EMBEDDINGS", "").lower() == "true":
            logger.info("FORCE_LOCAL_EMBEDDINGS is set. Ignoring Google API Key for embeddings.")
            self.google_api_key = None
            
        self.embedding_model = embedding_model
        self.use_fallback_embeddings = use_fallback_embeddings
        self.fallback_model = fallback_model
        
        # Memory integration
        self.memory_manager = memory_manager
        self.enable_memory = enable_memory
        
        # Reranker settings
        self.use_reranker = use_reranker
        self.reranker_model = reranker_model
        self._reranker = None
        
        # Multihop reasoning settings
        self.enable_multihop = enable_multihop
        self.max_hops = max_hops
        
        self._qdrant_client = None
        self._initialized = False
        self._last_init_failure: Optional[float] = None
        self._init_retry_cooldown = 60  # seconds before retrying failed init
        self._fallback_embedder = None
        self._using_fallback = False
        self._embedding_dim = 3072  # Default for gemini-embedding-001 (can be 768 for fallback)
        self._genai_client = None
        
        # Initialize Google API client if available
        if self.google_api_key and GOOGLE_GENAI_AVAILABLE:
            try:
                self._genai_client = genai.Client(api_key=self.google_api_key)
                logger.info("Google GenAI client configured for embeddings")
            except Exception as e:
                logger.warning(f"Failed to configure Google API client: {e}")
        else:
            if not self.google_api_key:
                logger.warning("GOOGLE_API_KEY not set.")
            if not GOOGLE_GENAI_AVAILABLE:
                logger.warning("google.genai package not available.")
        
        # Initialize fallback embedder if needed
        if self.use_fallback_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self._fallback_embedder = SentenceTransformer(self.fallback_model)
                # Get actual embedding dimension from fallback model
                test_embedding = self._fallback_embedder.encode("test")
                self._embedding_dim = len(test_embedding)
                logger.info(f"Fallback embedder initialized: {self.fallback_model} (dim={self._embedding_dim})")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback embedder: {e}")
                self._fallback_embedder = None
        
        # Initialize reranker if enabled
        if self.use_reranker and SENTENCE_TRANSFORMERS_AVAILABLE and CrossEncoder:
            try:
                self._reranker = CrossEncoder(self.reranker_model)
                logger.info(f"Reranker initialized: {self.reranker_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
                self._reranker = None
                self.use_reranker = False
        
        # Initialize memory manager if not provided but enabled
        if self.enable_memory and not self.memory_manager:
            try:
                from ..memory import MemoryManager
                self.memory_manager = MemoryManager(google_api_key=self.google_api_key)
                logger.info("Memory manager initialized for RAG")
            except Exception as e:
                logger.warning(f"Failed to initialize memory manager: {e}")
                self.enable_memory = False
        
        # Initialize prompt loader
        try:
            self._prompt_loader = get_prompt_loader()
            logger.info("Prompt loader initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize prompt loader: {e}")
            self._prompt_loader = None
    
    def _ensure_initialized(self) -> bool:
        """Initialize Qdrant client and collection."""
        if self._initialized:
            return True
        
        if not self.qdrant_path and (not self.qdrant_url or not self.qdrant_api_key):
            logger.warning("Qdrant not configured (URL/Key or Path missing). RAG features disabled.")
            return False
        
        # Cooldown: don't retry too quickly after a failure
        if self._last_init_failure is not None:
            if time.time() - self._last_init_failure < self._init_retry_cooldown:
                return False
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            
            if self.qdrant_path:
                logger.info(f"Initializing Qdrant with local path: {self.qdrant_path}")
                self._qdrant_client = QdrantClient(path=self.qdrant_path)
            else:
                self._qdrant_client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key
                )
            
            # Determine actual embedding dimension by making a test call
            actual_dim = self._embedding_dim
            if self._genai_client and not self._using_fallback:
                try:
                    # Make a test API call to get the actual dimension
                    test_embedding = self._get_embedding("test", task_type="RETRIEVAL_DOCUMENT")
                    actual_dim = len(test_embedding)
                    logger.info(f"Detected embedding dimension from Gemini API: {actual_dim}")
                except Exception as e:
                    logger.warning(f"Could not determine embedding dimension from API: {e}.")
                    if self._fallback_embedder:
                        logger.info("Switching to fallback embedder (sentence-transformers) for dimension check.")
                        self._using_fallback = True
                        actual_dim = self._embedding_dim
                    else:
                        logger.warning(f"Using default dimension: {actual_dim}")
            elif self._fallback_embedder:
                # Already set during initialization
                actual_dim = self._embedding_dim
            
            # Update embedding dimension
            self._embedding_dim = actual_dim
            
            # Check if collection exists and verify dimension
            collection_exists = False
            try:
                collection_info = self._qdrant_client.get_collection(self.collection_name)
                collection_exists = True
                existing_dim = collection_info.config.params.vectors.size
                
                if existing_dim != actual_dim:
                    logger.warning(
                        f"Collection dimension mismatch: existing={existing_dim}, required={actual_dim}. "
                        f"Recreating collection '{self.collection_name}'..."
                    )
                    # Delete and recreate collection with correct dimension
                    self._qdrant_client.delete_collection(self.collection_name)
                    collection_exists = False
                else:
                    logger.info(f"Using existing collection: {self.collection_name} (vector size: {existing_dim})")
            except Exception:
                # Collection doesn't exist
                collection_exists = False
            
            if not collection_exists:
                # Collection doesn't exist or was deleted, create it
                self._qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self._embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name} (vector size: {self._embedding_dim})")
            
            self._initialized = True
            self._last_init_failure = None
            return True
            
        except ImportError:
            logger.error("qdrant-client not installed. Install with: pip install qdrant-client")
            self._last_init_failure = time.time()
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            self._last_init_failure = time.time()
            return False
    
    def _get_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Get embedding for text using Gemini embedder API, with fallback to sentence-transformers.
        
        Args:
            text: Text to embed
            task_type: Task type for Gemini embeddings ("RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY")
        """
        # Try Google API first if available
        if self._genai_client and not self._using_fallback:
            try:
                # Use Google GenAI embedding API with client
                # The google.genai package uses client.models.embed_content
                # Map task_type to proper enum values
                task_type_upper = task_type.upper()
                if task_type_upper not in ["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", "SEMANTIC_SIMILARITY", "CLASSIFICATION", "CLUSTERING"]:
                    task_type_upper = "RETRIEVAL_DOCUMENT"
                
                embed_config = None
                if types:
                    try:
                        # Use task_type parameter in config
                        embed_config = types.EmbedContentConfig(task_type=task_type_upper)
                    except Exception as e:
                        # If types.EmbedContentConfig doesn't support task_type, try without
                        logger.debug(f"Could not set task_type in config: {e}")
                        try:
                            embed_config = types.EmbedContentConfig()
                        except Exception:
                            embed_config = None
                
                # Make API call to Gemini embedder
                logger.info(f"Making API call to Gemini embedder: model={self.embedding_model}, task_type={task_type_upper}")
                emb_response = self._genai_client.models.embed_content(
                    model=self.embedding_model,
                    contents=text,  # Can be string or list of strings
                    config=embed_config
                )
                
                # Extract embedding from response
                # The API returns an object with embeddings attribute (list of embedding objects)
                embedding = None
                if hasattr(emb_response, 'embeddings'):
                    # embeddings is a list, take the first one
                    embeddings_list = emb_response.embeddings
                    if embeddings_list and len(embeddings_list) > 0:
                        embedding_obj = embeddings_list[0]
                        # Each embedding object has a .values attribute containing the vector
                        if hasattr(embedding_obj, 'values'):
                            embedding = embedding_obj.values
                        elif hasattr(embedding_obj, 'embedding'):
                            embedding = embedding_obj.embedding
                        elif isinstance(embedding_obj, list):
                            embedding = embedding_obj
                elif hasattr(emb_response, 'embedding'):
                    embedding = emb_response.embedding
                elif isinstance(emb_response, dict):
                    embedding = emb_response.get("embedding") or emb_response.get("values") or emb_response.get("embeddings")
                    if embedding and isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
                        embedding = embedding[0]
                elif isinstance(emb_response, list):
                    embedding = emb_response[0] if emb_response else None
                
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    # Update embedding dimension based on actual Gemini response
                    if self._embedding_dim != len(embedding):
                        self._embedding_dim = len(embedding)
                        logger.info(f"Updated embedding dimension to {self._embedding_dim} based on Gemini API response")
                    logger.info(f"Successfully generated embedding via Gemini API (dim={len(embedding)})")
                    return embedding
                else:
                    logger.warning(f"Unexpected embedding response format: {type(emb_response)}")
                    raise ValueError("Invalid embedding response from Google API")
                    
            except Exception as e:
                error_str = str(e)
                # Check if it's a quota error
                if "429" in error_str or "quota" in error_str.lower() or "Quota exceeded" in error_str:
                    logger.warning(f"Google API quota exceeded. Error: {error_str[:200]}")
                    if self.use_fallback_embeddings and self._fallback_embedder:
                        logger.info("Switching to fallback embedding provider (sentence-transformers)")
                        self._using_fallback = True
                        # Fall through to fallback
                    else:
                        logger.error("Quota exceeded and no fallback available. Please upgrade your Google API plan or install sentence-transformers.")
                        raise
                else:
                    logger.error(f"Error getting embedding from Google API: {e}")
                    if self.use_fallback_embeddings and self._fallback_embedder:
                        logger.info("Falling back to sentence-transformers due to API error")
                        self._using_fallback = True
                        # Fall through to fallback
                    else:
                        raise
        
        # Use fallback embedder if available
        if self._fallback_embedder:
            try:
                embedding = self._fallback_embedder.encode(text, normalize_embeddings=True).tolist()
                if not self._using_fallback:
                    logger.info("Using fallback embedder (sentence-transformers)")
                    self._using_fallback = True
                return embedding
            except Exception as e:
                logger.error(f"Error getting embedding from fallback: {e}")
                raise
        
        # No embedding provider available
        raise ValueError(
            "No embedding provider available. "
            "Set GOOGLE_API_KEY or install sentence-transformers: pip install sentence-transformers"
        )
    
    def _get_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """
        Get embeddings for multiple texts using batched API calls.
        
        Args:
            texts: List of texts to embed
            task_type: Task type for Gemini embeddings ("RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY")
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Try Google API first if available
        if self._genai_client and not self._using_fallback:
            try:
                task_type_upper = task_type.upper()
                if task_type_upper not in ["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", "SEMANTIC_SIMILARITY", "CLASSIFICATION", "CLUSTERING"]:
                    task_type_upper = "RETRIEVAL_DOCUMENT"
                
                embed_config = None
                if types:
                    try:
                        embed_config = types.EmbedContentConfig(task_type=task_type_upper)
                    except Exception as e:
                        logger.debug(f"Could not set task_type in config: {e}")
                        try:
                            embed_config = types.EmbedContentConfig()
                        except Exception:
                            embed_config = None
                
                # Batch API call - pass list of texts
                emb_response = self._genai_client.models.embed_content(
                    model=self.embedding_model,
                    contents=texts,
                    config=embed_config
                )
                
                # Extract embeddings from response
                embeddings = []
                if hasattr(emb_response, 'embeddings'):
                    embeddings_list = emb_response.embeddings
                    for embedding_obj in embeddings_list:
                        if hasattr(embedding_obj, 'values'):
                            embeddings.append(embedding_obj.values)
                        elif hasattr(embedding_obj, 'embedding'):
                            embeddings.append(embedding_obj.embedding)
                        elif isinstance(embedding_obj, list):
                            embeddings.append(embedding_obj)
                elif hasattr(emb_response, 'embedding'):
                    # Single embedding response
                    embeddings = [emb_response.embedding]
                elif isinstance(emb_response, dict):
                    embedding_data = emb_response.get("embedding") or emb_response.get("values") or emb_response.get("embeddings")
                    if embedding_data:
                        if isinstance(embedding_data[0], list):
                            embeddings = embedding_data
                        else:
                            embeddings = [embedding_data]
                elif isinstance(emb_response, list):
                    embeddings = emb_response
                
                if embeddings and len(embeddings) == len(texts):
                    # Update embedding dimension if needed
                    if embeddings and len(embeddings[0]) != self._embedding_dim:
                        self._embedding_dim = len(embeddings[0])
                        logger.info(f"Updated embedding dimension to {self._embedding_dim} based on Gemini API response")
                    logger.info(f"Successfully generated {len(embeddings)} embeddings via Gemini API (dim={len(embeddings[0]) if embeddings else 0})")
                    return embeddings
                else:
                    logger.warning(f"Unexpected embedding response format: expected {len(texts)} embeddings, got {len(embeddings) if embeddings else 0}")
                    raise ValueError("Invalid embedding response from Google API")
                    
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "Quota exceeded" in error_str:
                    logger.warning(f"Google API quota exceeded. Error: {error_str[:200]}")
                    if self.use_fallback_embeddings and self._fallback_embedder:
                        logger.info("Switching to fallback embedding provider (sentence-transformers)")
                        self._using_fallback = True
                    else:
                        logger.error("Quota exceeded and no fallback available. Please upgrade your Google API plan or install sentence-transformers.")
                        raise
                else:
                    logger.error(f"Error getting embeddings from Google API: {e}")
                    if self.use_fallback_embeddings and self._fallback_embedder:
                        logger.info("Falling back to sentence-transformers due to API error")
                        self._using_fallback = True
                    else:
                        raise
        
        # Use fallback embedder if available
        if self._fallback_embedder:
            try:
                embeddings = self._fallback_embedder.encode(texts, normalize_embeddings=True).tolist()
                if not self._using_fallback:
                    logger.info("Using fallback embedder (sentence-transformers)")
                    self._using_fallback = True
                return embeddings
            except Exception as e:
                logger.error(f"Error getting embeddings from fallback: {e}")
                raise
        
        # No embedding provider available
        raise ValueError(
            "No embedding provider available. "
            "Set GOOGLE_API_KEY or install sentence-transformers: pip install sentence-transformers"
        )
    
    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 128
    ) -> int:
        """
        Index documents into Qdrant.
        
        Args:
            documents: List of document dictionaries with 'text' and 'metadata'
            batch_size: Number of documents to process in each batch
            
        Returns:
            Number of documents indexed
        """
        if not self._ensure_initialized():
            return 0
        
        from qdrant_client.models import PointStruct
        
        indexed_count = 0
        indexed_at = datetime.utcnow().isoformat()
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Filter out empty texts and prepare texts for batch embedding
            valid_docs = []
            texts_for_embedding = []
            
            for doc in batch:
                text = doc.get("text", "").strip()
                if not text:
                    continue
                valid_docs.append(doc)
                texts_for_embedding.append(text)
            
            if not texts_for_embedding:
                continue
            
            try:
                # Batch embeddings call
                embeddings = self._get_embeddings(texts_for_embedding, task_type="RETRIEVAL_DOCUMENT")
                
                # Build points with deterministic IDs and flattened payloads
                points = []
                for idx, doc in enumerate(valid_docs):
                    try:
                        text = texts_for_embedding[idx]
                        embedding = embeddings[idx]
                        metadata = doc.get("metadata", {})
                        
                        # Generate deterministic point_id using sha256
                        # Use chunk_id if present, otherwise use text
                        id_source = metadata.get("chunk_id")
                        if not id_source:
                            id_source = text
                        
                        # Convert to string for hashing
                        id_str = str(id_source)
                        # Hash and convert to int mod 2**63
                        point_id = int(hashlib.sha256(id_str.encode('utf-8')).hexdigest(), 16) % (2**63)
                        
                        # Flatten metadata into payload (avoid nested structure)
                        payload = {
                            "text": text,
                            "indexed_at": indexed_at
                        }
                        
                        # Flatten metadata fields directly into payload
                        for key, value in metadata.items():
                            if key != "chunk_id":  # chunk_id already used for ID generation
                                payload[key] = value
                        
                        points.append(
                            PointStruct(
                                id=point_id,
                                vector=embedding,
                                payload=payload
                            )
                        )
                        indexed_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error processing document in batch: {e}")
                        continue
                
                # Upsert batch of points
                if points:
                    self._qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    logger.info(f"Indexed batch: {len(points)} documents (total: {indexed_count})")
                    
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                # Fallback to per-document processing if batch fails
                for doc in valid_docs:
                    try:
                        text = doc.get("text", "").strip()
                        if not text:
                            continue
                        
                        embedding = self._get_embedding(text, task_type="RETRIEVAL_DOCUMENT")
                        metadata = doc.get("metadata", {})
                        
                        # Generate deterministic point_id
                        id_source = metadata.get("chunk_id")
                        if not id_source:
                            id_source = text
                        id_str = str(id_source)
                        point_id = int(hashlib.sha256(id_str.encode('utf-8')).hexdigest(), 16) % (2**63)
                        
                        # Flatten payload
                        payload = {
                            "text": text,
                            "indexed_at": indexed_at
                        }
                        for key, value in metadata.items():
                            if key != "chunk_id":
                                payload[key] = value
                        
                        self._qdrant_client.upsert(
                            collection_name=self.collection_name,
                            points=[PointStruct(
                                id=point_id,
                                vector=embedding,
                                payload=payload
                            )]
                        )
                        indexed_count += 1
                        
                    except Exception as e2:
                        logger.warning(f"Error indexing document in fallback: {e2}")
                        continue
        
        logger.info(f"Indexed {indexed_count} documents total")
        return indexed_count
    
    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        use_full_pipeline: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Comprehensive reranking pipeline:
        1. Bi-Encoder (recall) - Already done via initial vector search
        2. Cross-Encoder (top 50) - Rerank top 50 candidates
        3. Chunk-aware scoring - Score based on chunk position/context
        4. Context-aware reranking - Consider surrounding chunks
        5. MMR diversification - Diversify final results
        
        Args:
            query: Original query
            results: List of search results from bi-encoder
            top_k: Number of top results to return after reranking
            use_full_pipeline: Whether to use the full 5-stage pipeline
            
        Returns:
            Reranked and diversified list of results
        """
        if not results:
            return results
        
        if not use_full_pipeline:
            # Fallback to simple cross-encoder reranking
            return self._simple_rerank(query, results, top_k)
        
        try:
            logger.info(f"Starting comprehensive reranking pipeline on {len(results)} results")
            
            # Stage 1: Bi-Encoder (recall) - Already done, results are from vector search
            # Results already have 'score' from bi-encoder similarity
            
            # Stage 2: Cross-Encoder (top 50)
            # Take top 50 from bi-encoder results for cross-encoder reranking
            top_50 = sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)[:50]
            cross_encoder_results = self._cross_encoder_rerank(query, top_50)
            
            # Stage 3: Chunk-aware scoring
            chunk_aware_results = self._chunk_aware_scoring(query, cross_encoder_results)
            
            # Stage 4: Context-aware reranking
            context_aware_results = self._context_aware_reranking(query, chunk_aware_results)
            
            # Stage 5: MMR diversification
            final_results = self._mmr_diversification(query, context_aware_results, top_k or len(context_aware_results))
            
            logger.info(f"Reranking pipeline completed: {len(final_results)} final results")
            return final_results
            
        except Exception as e:
            logger.warning(f"Error in reranking pipeline: {e}. Falling back to simple reranking.")
            return self._simple_rerank(query, results, top_k)
    
    def _simple_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Simple cross-encoder reranking (fallback)."""
        if not self._reranker or not results:
            return results[:top_k] if top_k else results
        
        try:
            pairs = [[query, result["text"]] for result in results]
            scores = self._reranker.predict(pairs)
            
            for i, result in enumerate(results):
                result["rerank_score"] = float(scores[i])
                result["combined_score"] = 0.3 * result.get("score", 0.0) + 0.7 * float(scores[i])
            
            results.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)
            return results[:top_k] if top_k else results
            
        except Exception as e:
            logger.warning(f"Error in simple reranking: {e}")
            return results[:top_k] if top_k else results
    
    def _cross_encoder_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Cross-Encoder reranking on top 50 candidates.
        
        Args:
            query: Original query
            results: Top 50 results from bi-encoder
            
        Returns:
            Reranked results with cross-encoder scores
        """
        if not self._reranker or not results:
            return results
        
        try:
            pairs = [[query, result["text"]] for result in results]
            scores = self._reranker.predict(pairs)
            
            for i, result in enumerate(results):
                rerank_score = float(scores[i])
                result["cross_encoder_score"] = rerank_score
                result["rerank_score"] = rerank_score  # Also set for consistency with simple rerank
                # Weighted combination: 0.2 bi-encoder + 0.8 cross-encoder
                result["stage2_score"] = 0.2 * result.get("score", 0.0) + 0.8 * rerank_score
                # Also set combined_score for consistency (same as stage2_score in this case)
                result["combined_score"] = result["stage2_score"]
            
            # Sort by stage 2 score
            results.sort(key=lambda x: x.get("stage2_score", 0.0), reverse=True)
            logger.info(f"Cross-encoder reranking completed on {len(results)} results")
            return results
            
        except Exception as e:
            logger.warning(f"Error in cross-encoder reranking: {e}")
            return results
    
    def _chunk_aware_scoring(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 3: Chunk-aware scoring.
        Scores chunks based on:
        - Position within document (earlier chunks may be more important)
        - Chunk completeness (full sentences vs fragments)
        - Metadata quality (title, heading proximity)
        
        Args:
            query: Original query
            results: Results from cross-encoder stage
            
        Returns:
            Results with chunk-aware scores
        """
        if not results:
            return results
        
        try:
            for result in results:
                metadata = result.get("metadata", {})
                text = result.get("text", "")
                
                chunk_score = 1.0
                
                # Position-based scoring (earlier chunks get slight boost)
                chunk_index = metadata.get("chunk_index", None)
                total_chunks = metadata.get("total_chunks", None)
                if chunk_index is not None and total_chunks and total_chunks > 1:
                    # Normalize position: earlier chunks get slightly higher score
                    position_factor = 1.0 - (chunk_index / total_chunks) * 0.1  # Max 10% boost
                    chunk_score *= position_factor
                
                # Completeness scoring (full sentences vs fragments)
                sentence_endings = text.count('.') + text.count('!') + text.count('?')
                text_length = len(text)
                if text_length > 0:
                    completeness = min(sentence_endings / (text_length / 100), 1.0)  # Normalize
                    chunk_score *= (0.9 + 0.1 * completeness)  # 0-10% boost for completeness
                
                # Metadata quality scoring
                if metadata.get("is_title", False) or metadata.get("is_heading", False):
                    chunk_score *= 1.15  # 15% boost for titles/headings
                
                if metadata.get("section_name"):
                    chunk_score *= 1.05  # 5% boost for sectioned content
                
                # Store chunk-aware score
                result["chunk_aware_score"] = chunk_score
                # Combine with stage 2 score
                result["stage3_score"] = result.get("stage2_score", result.get("score", 0.0)) * chunk_score
            
            # Sort by stage 3 score
            results.sort(key=lambda x: x.get("stage3_score", 0.0), reverse=True)
            logger.info(f"Chunk-aware scoring completed on {len(results)} results")
            return results
            
        except Exception as e:
            logger.warning(f"Error in chunk-aware scoring: {e}")
            return results
    
    def _context_aware_reranking(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 4: Context-aware reranking.
        Considers:
        - Document-level context (multiple chunks from same document)
        - Semantic coherence with other high-scoring results
        - Query-term density
        
        Args:
            query: Original query
            results: Results from chunk-aware scoring stage
            
        Returns:
            Results with context-aware scores
        """
        if not results:
            return results
        
        try:
            # Group results by document/source
            doc_groups: Dict[str, List[Dict[str, Any]]] = {}
            for result in results:
                metadata = result.get("metadata", {})
                doc_id = metadata.get("file_name") or metadata.get("document_id") or "unknown"
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = []
                doc_groups[doc_id].append(result)
            
            # Calculate document-level scores
            doc_scores: Dict[str, float] = {}
            for doc_id, doc_results in doc_groups.items():
                # Average score of chunks from this document
                avg_score = sum(r.get("stage3_score", 0.0) for r in doc_results) / len(doc_results)
                # Boost if multiple relevant chunks from same document
                diversity_bonus = min(len(doc_results) * 0.05, 0.2)  # Max 20% bonus
                doc_scores[doc_id] = avg_score * (1.0 + diversity_bonus)
            
            # Query-term density scoring
            query_terms = set(query.lower().split())
            
            for result in results:
                metadata = result.get("metadata", {})
                text = result.get("text", "").lower()
                doc_id = metadata.get("file_name") or metadata.get("document_id") or "unknown"
                
                context_score = 1.0
                
                # Document-level context boost
                doc_score = doc_scores.get(doc_id, 0.0)
                if doc_score > 0:
                    # Normalize and apply boost (up to 10%)
                    max_doc_score = max(doc_scores.values()) if doc_scores else 1.0
                    if max_doc_score > 0:
                        doc_factor = doc_score / max_doc_score
                        context_score *= (1.0 + doc_factor * 0.1)
                
                # Query-term density
                text_words = set(text.split())
                matching_terms = len(query_terms.intersection(text_words))
                if len(query_terms) > 0:
                    term_density = matching_terms / len(query_terms)
                    context_score *= (0.95 + 0.05 * term_density)  # 0-5% boost
                
                # Store context-aware score
                result["context_aware_score"] = context_score
                # Combine with stage 3 score
                result["stage4_score"] = result.get("stage3_score", result.get("score", 0.0)) * context_score
            
            # Sort by stage 4 score
            results.sort(key=lambda x: x.get("stage4_score", 0.0), reverse=True)
            logger.info(f"Context-aware reranking completed on {len(results)} results")
            return results
            
        except Exception as e:
            logger.warning(f"Error in context-aware reranking: {e}")
            return results
    
    def _mmr_diversification(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Stage 5: MMR (Maximal Marginal Relevance) diversification.
        Balances relevance and diversity to avoid redundant results.
        
        Args:
            query: Original query
            results: Results from context-aware reranking stage
            top_k: Number of final results to return
            
        Returns:
            Diversified final results
        """
        if not results or top_k <= 0:
            return []
        
        if top_k >= len(results):
            return results
        
        try:
            # Use MMR to select diverse results
            # MMR = argmax[λ * Sim(query, doc) - (1-λ) * max(Sim(doc, selected))]
            lambda_param = 0.7  # Balance between relevance (0.7) and diversity (0.3)
            
            selected = []
            remaining = results.copy()
            
            # Cache embeddings to avoid redundant API calls
            embedding_cache: Dict[str, np.ndarray] = {}
            
            def get_cached_embedding(text: str) -> Optional[np.ndarray]:
                """Get embedding with caching."""
                if not text:
                    return None
                if text not in embedding_cache:
                    try:
                        embedding_cache[text] = np.array(self._get_embedding(text, task_type="RETRIEVAL_DOCUMENT"))
                    except Exception:
                        return None
                return embedding_cache[text]
            
            # Get query embedding for similarity calculation
            try:
                query_embedding = np.array(self._get_embedding(query, task_type="RETRIEVAL_QUERY"))
            except Exception:
                # Fallback: use stage4_score as relevance proxy
                query_embedding = None
            
            # Select first result (highest relevance)
            if remaining:
                selected.append(remaining.pop(0))
            
            # Select remaining results using MMR
            while len(selected) < top_k and remaining:
                best_idx = 0
                best_mmr = float('-inf')
                
                for i, candidate in enumerate(remaining):
                    # Relevance score (stage4_score normalized)
                    relevance = candidate.get("stage4_score", candidate.get("score", 0.0))
                    max_relevance = max(r.get("stage4_score", r.get("score", 0.0)) for r in results)
                    if max_relevance > 0:
                        relevance_norm = relevance / max_relevance
                    else:
                        relevance_norm = 0.0
                    
                    # Diversity: max similarity to already selected results
                    max_similarity = 0.0
                    candidate_text = candidate.get("text", "")
                    
                    if query_embedding is not None:
                        candidate_embedding = get_cached_embedding(candidate_text)
                        if candidate_embedding is not None:
                            # Use embedding-based similarity
                            for selected_result in selected:
                                selected_text = selected_result.get("text", "")
                                if selected_text:
                                    selected_embedding = get_cached_embedding(selected_text)
                                    if selected_embedding is not None:
                                        similarity = np.dot(candidate_embedding, selected_embedding) / (
                                            np.linalg.norm(candidate_embedding) * np.linalg.norm(selected_embedding)
                                        )
                                        max_similarity = max(max_similarity, similarity)
                    
                    # Fallback to text-based similarity if embeddings not available
                    if max_similarity == 0.0:
                        candidate_text_lower = candidate_text.lower()
                        for selected_result in selected:
                            selected_text = selected_result.get("text", "").lower()
                            # Simple word overlap (Jaccard similarity)
                            candidate_words = set(candidate_text_lower.split())
                            selected_words = set(selected_text.split())
                            if len(candidate_words) > 0 and len(selected_words) > 0:
                                overlap = len(candidate_words.intersection(selected_words))
                                union = len(candidate_words.union(selected_words))
                                similarity = overlap / union if union > 0 else 0.0
                                max_similarity = max(max_similarity, similarity)
                    
                    # MMR score
                    mmr_score = lambda_param * relevance_norm - (1 - lambda_param) * max_similarity
                    
                    if mmr_score > best_mmr:
                        best_mmr = mmr_score
                        best_idx = i
                
                # Add best candidate
                selected.append(remaining.pop(best_idx))
            
            # Store final scores
            for i, result in enumerate(selected):
                result["final_score"] = result.get("stage4_score", result.get("score", 0.0))
                result["mmr_rank"] = i + 1
            
            logger.info(f"MMR diversification completed: {len(selected)} final results")
            return selected
            
        except Exception as e:
            logger.warning(f"Error in MMR diversification: {e}. Returning top-k by score.")
            # Fallback: return top-k by score
            return sorted(results, key=lambda x: x.get("stage4_score", x.get("score", 0.0)), reverse=True)[:top_k]
    
    def _extract_entities_and_facts(self, retrieved_docs: List[Dict[str, Any]], original_query: str) -> str:
        """
        Extract entities and key facts from retrieved documents.
        
        Args:
            retrieved_docs: List of retrieved document results
            original_query: Original query for context
            
        Returns:
            String containing extracted entities and facts
        """
        if not retrieved_docs:
            return ""
        
        # Combine text from retrieved documents
        combined_text = "\n\n".join([doc.get("text", "")[:500] for doc in retrieved_docs[:5]])  # Limit to top 5 docs
        
        if not self._genai_client:
            # Simple extraction: return key phrases
            import re
            # Extract capitalized phrases (potential entities)
            entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', combined_text)
            # Return unique entities
            unique_entities = list(set(entities))[:10]
            return ", ".join(unique_entities) if unique_entities else ""
        
        try:
            # Load prompt from YAML
            if self._prompt_loader:
                prompt = self._prompt_loader.get_prompt(
                    "multihop",
                    "extract_entities_and_facts",
                    original_query=original_query,
                    combined_text=combined_text
                )
                prompt_config = self._prompt_loader.get_prompt_config(
                    "multihop",
                    "extract_entities_and_facts"
                )
                temperature = prompt_config.get("temperature", 0.2)
                model = prompt_config.get("model", "gemini-2.0-flash-001")
            else:
                # Fallback to hardcoded prompt
                prompt = f"""Extract key entities, facts, and information from the following retrieved documents that are relevant to answering the query.

Original Query: {original_query}

Retrieved Documents:
{combined_text}

Extract and list:
1. Key entities (people, places, organizations, concepts)
2. Important facts and relationships
3. Relevant details that could help answer the query

Format as a concise summary of extracted information:"""
                temperature = 0.2
                model = "gemini-2.0-flash-001"
            
            contents = prompt
            config = None
            if types:
                try:
                    contents = types.Part.from_text(text=prompt)
                    config = types.GenerateContentConfig(temperature=temperature)
                except Exception:
                    contents = prompt
                    config = None
            
            response = self._genai_client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif isinstance(response, dict):
                response_text = response.get('text') or response.get('content')
            elif isinstance(response, str):
                response_text = response
            
            return response_text.strip() if response_text else ""
            
        except Exception as e:
            logger.warning(f"Error extracting entities/facts: {e}")
            return ""
    
    def _rewrite_query_with_evidence(self, original_query: str, evidence: str, hop_number: int) -> str:
        """
        Rewrite the query using extracted evidence for the next hop.
        
        Args:
            original_query: Original user query
            evidence: Extracted entities and facts from previous hop
            hop_number: Current hop number
            
        Returns:
            Rewritten query for next hop
        """
        if not evidence:
            return original_query
        
        if not self._genai_client:
            # Simple concatenation
            return f"{original_query} Related information: {evidence[:200]}"
        
        try:
            # Load prompt from YAML
            if self._prompt_loader:
                prompt = self._prompt_loader.get_prompt(
                    "multihop",
                    "rewrite_query_with_evidence",
                    original_query=original_query,
                    evidence=evidence,
                    hop_number=hop_number
                )
                prompt_config = self._prompt_loader.get_prompt_config(
                    "multihop",
                    "rewrite_query_with_evidence"
                )
                temperature = prompt_config.get("temperature", 0.3)
                model = prompt_config.get("model", "gemini-2.0-flash-001")
            else:
                # Fallback to hardcoded prompt
                prompt = f"""Given the original query and evidence from previous retrieval, rewrite the query to focus on finding more specific information.

Original Query: {original_query}

Evidence from Hop {hop_number}:
{evidence}

Rewrite the query to:
1. Incorporate relevant entities and facts from the evidence
2. Focus on finding more specific or related information
3. Maintain the original intent while being more targeted

Rewritten query:"""
                temperature = 0.3
                model = "gemini-2.0-flash-001"
            
            contents = prompt
            config = None
            if types:
                try:
                    contents = types.Part.from_text(text=prompt)
                    config = types.GenerateContentConfig(temperature=temperature)
                except Exception:
                    contents = prompt
                    config = None
            
            response = self._genai_client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif isinstance(response, dict):
                response_text = response.get('text') or response.get('content')
            elif isinstance(response, str):
                response_text = response
            
            if response_text:
                rewritten = response_text.strip()
                # Remove quotes if present
                rewritten = rewritten.strip('"\'')
                return rewritten if rewritten else original_query
            
        except Exception as e:
            logger.warning(f"Error rewriting query: {e}")
        
        return original_query
    
    def _should_continue_hopping(self, original_query: str, all_results: List[Dict[str, Any]], current_hop: int) -> bool:
        """
        Determine if we should continue to another hop.
        
        Args:
            original_query: Original user query
            all_results: All results collected so far
            current_hop: Current hop number
            
        Returns:
            True if we should continue, False otherwise
        """
        # Don't exceed max_hops
        if current_hop >= self.max_hops:
            return False
        
        # Need at least some results to continue
        if not all_results:
            return True
        
        # If we have very few results, continue
        if len(all_results) < 3:
            return True
        
        # Use LLM to determine if we have enough information
        if self._genai_client:
            try:
                # Sample some results
                sample_texts = "\n\n".join([r.get("text", "")[:300] for r in all_results[:3]])
                
                # Load prompt from YAML
                if self._prompt_loader:
                    prompt = self._prompt_loader.get_prompt(
                        "multihop",
                        "should_continue_hopping",
                        original_query=original_query,
                        sample_texts=sample_texts
                    )
                    prompt_config = self._prompt_loader.get_prompt_config(
                        "multihop",
                        "should_continue_hopping"
                    )
                    temperature = prompt_config.get("temperature", 0.1)
                    model = prompt_config.get("model", "gemini-2.0-flash-001")
                else:
                    # Fallback to hardcoded prompt
                    prompt = f"""Given the original query and retrieved information, determine if we need to search for more information.

Original Query: {original_query}

Retrieved Information:
{sample_texts}

Do we have sufficient information to answer the query, or should we search for more specific information?

Respond with only "YES" if we have enough information, or "NO" if we need to search more:"""
                    temperature = 0.1
                    model = "gemini-2.0-flash"
                
                contents = prompt
                config = None
                if types:
                    try:
                        contents = types.Part.from_text(text=prompt)
                        config = types.GenerateContentConfig(temperature=temperature)
                    except Exception:
                        contents = prompt
                        config = None
                
                response = self._genai_client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                
                response_text = None
                if hasattr(response, 'text'):
                    response_text = response.text
                elif isinstance(response, dict):
                    response_text = response.get('text') or response.get('content')
                elif isinstance(response, str):
                    response_text = response
                
                if response_text:
                    decision = response_text.strip().upper()
                    return "NO" in decision or "MORE" in decision or "CONTINUE" in decision
                    
            except Exception as e:
                logger.warning(f"Error determining if should continue: {e}")
        
        # Default: continue if we haven't reached max_hops
        return current_hop < self.max_hops
    
    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict] = None,
        use_multihop: Optional[bool] = None,
        use_reranker: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents with optional multihop reasoning and reranking.
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filter_metadata: Metadata filters (e.g., {"file_name": "doc.pdf"})
            use_multihop: Override instance setting for multihop reasoning
            use_reranker: Override instance setting for reranking
            
        Returns:
            List of search results with 'text', 'metadata', and 'score'
        """
        if not self._ensure_initialized():
            return []
        
        use_multihop = use_multihop if use_multihop is not None else self.enable_multihop
        use_reranker = use_reranker if use_reranker is not None else self.use_reranker
        
        try:
            # Multihop reasoning: decompose query and search iteratively
            if use_multihop:
                return self._multihop_search(query, limit, score_threshold, filter_metadata, use_reranker)
            
            # Standard single-hop search
            # Get query embedding (use "RETRIEVAL_QUERY" task type for queries)
            query_embedding = self._get_embedding(query, task_type="RETRIEVAL_QUERY")
            
            # Build filter if needed
            query_filter = None
            if filter_metadata:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=f"metadata.{key}",
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Stage 1: Bi-Encoder (recall) - Retrieve more candidates for comprehensive reranking
            # Retrieve top 50-100 candidates for the reranking pipeline
            if use_reranker:
                # Retrieve more candidates for the full reranking pipeline
                search_limit = max(50, limit * 10)  # At least 50, or 10x the desired limit
            else:
                search_limit = limit
            
            # Use query_points() instead of search() for newer qdrant-client versions
            query_response = self._qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=search_limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = []
            # query_points returns a QueryResponse with points attribute containing ScoredPoint objects
            for result in query_response.points:
                payload = result.payload
                formatted_results.append({
                    "text": payload.get("text", ""),
                    "metadata": payload.get("metadata", {}),
                    "score": result.score  # Bi-encoder similarity score
                })
            
            # Apply comprehensive reranking pipeline if enabled
            if use_reranker:
                formatted_results = self._rerank_results(query, formatted_results, top_k=limit, use_full_pipeline=True)
            else:
                # Just return top-k by bi-encoder score
                formatted_results = sorted(formatted_results, key=lambda x: x.get("score", 0.0), reverse=True)[:limit]
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def _multihop_search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict] = None,
        use_reranker: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform true multihop reasoning search:
        1. Initial retrieval with original query
        2. Extract entities/facts from retrieved documents
        3. Rewrite query using evidence
        4. Evidence-based retrieval
        5. Repeat until satisfied
        6. Final rerank + answer grounding
        
        Args:
            query: Original complex query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_metadata: Metadata filters
            use_reranker: Whether to use reranking
            
        Returns:
            List of search results
        """
        original_query = query
        all_results = []
        seen_texts = set()
        current_query = query
        hop = 1
        
        logger.info(f"Starting multihop search for: {original_query}")
        
        while hop <= self.max_hops:
            logger.info(f"Hop {hop}: Searching with query: {current_query[:80]}...")
            
            # Hop N: Retrieve documents with current query
            hop_results = self._single_hop_search(
                current_query,
                limit=limit * 2,  # Get more results per hop
                score_threshold=score_threshold,
                filter_metadata=filter_metadata
            )
            
            # Add results to collection (deduplicate)
            for result in hop_results:
                text_key = result["text"][:100]
                if text_key not in seen_texts:
                    result["hop"] = hop
                    result["query_used"] = current_query
                    all_results.append(result)
                    seen_texts.add(text_key)
            
            logger.info(f"Hop {hop} retrieved {len(hop_results)} new documents (total: {len(all_results)})")
            
            # Extract entities / facts from retrieved documents
            if hop_results:
                evidence = self._extract_entities_and_facts(hop_results, original_query)
                logger.info(f"Hop {hop} extracted evidence: {evidence[:100] if evidence else 'None'}...")
                
                # Check if we should continue
                if not self._should_continue_hopping(original_query, all_results, hop):
                    logger.info(f"Hop {hop}: Sufficient information retrieved, stopping")
                    break
                
                # Rewrite query using evidence for next hop
                if evidence and hop < self.max_hops:
                    current_query = self._rewrite_query_with_evidence(original_query, evidence, hop)
                    logger.info(f"Hop {hop}: Rewritten query for next hop: {current_query[:80]}...")
                else:
                    # No evidence or last hop, stop
                    break
            else:
                # No results, stop
                logger.info(f"Hop {hop}: No results retrieved, stopping")
                break
            
            hop += 1
        
        logger.info(f"Multihop search completed after {hop} hops, collected {len(all_results)} unique documents")
        
        # Final rerank + answer grounding using comprehensive pipeline
        if use_reranker and all_results:
            all_results = self._rerank_results(original_query, all_results, top_k=limit, use_full_pipeline=True)
        else:
            # Sort by score and limit
            all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            all_results = all_results[:limit]
        
        return all_results
    
    def _single_hop_search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform a single hop search without multihop or reranking.
        Internal method used by multihop search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_metadata: Metadata filters
            
        Returns:
            List of search results
        """
        if not self._ensure_initialized():
            return []
        
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query, task_type="RETRIEVAL_QUERY")
            
            # Build filter if needed
            query_filter = None
            if filter_metadata:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=f"metadata.{key}",
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Search
            query_response = self._qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = []
            for result in query_response.points:
                payload = result.payload
                formatted_results.append({
                    "text": payload.get("text", ""),
                    "metadata": payload.get("metadata", {}),
                    "score": result.score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in single hop search: {e}")
            return []

    
    
    def get_context(self, query: str, limit: int = 3, include_memory: bool = True) -> str:
        """
        Get formatted context string from search results and optionally memory.
        
        Args:
            query: Search query
            limit: Number of results to include
            include_memory: Whether to include memory context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Get RAG results
        results = self.search(query, limit=limit)
        
        if results:
            context_parts.append("Relevant information from documents:")
            
            for i, result in enumerate(results, 1):
                text = result["text"]
                metadata = result.get("metadata", {})
                file_name = metadata.get("file_name", "Unknown")
                # Use final_score from comprehensive reranking pipeline if available
                score = result.get("final_score") or result.get("stage4_score") or result.get("stage3_score") or result.get("stage2_score") or result.get("combined_score") or result.get("score", 0.0)
                
                # Truncate long text
                if len(text) > 500:
                    text = text[:500] + "..."
                
                context_parts.append(
                    f"\n[{i}] From {file_name} (relevance: {score:.3f}):\n{text}"
                )
        
        # Get memory context if enabled
        if include_memory and self.enable_memory and self.memory_manager:
            try:
                memory_context = self.memory_manager.get_context_string(query, agent_id="rag", limit=limit)
                if memory_context:
                    context_parts.append(f"\n{memory_context}")
            except Exception as e:
                logger.warning(f"Failed to get memory context: {e}")
        
        if not context_parts:
            return ""
        
        return "\n".join(context_parts)
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        if not self._ensure_initialized():
            return False
        
        try:
            self._qdrant_client.delete_collection(self.collection_name)
            from qdrant_client.models import Distance, VectorParams
            self._qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self._embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        if not self._ensure_initialized():
            return {}
        
        try:
            collection_info = self._qdrant_client.get_collection(self.collection_name)
            info = {
                "name": self.collection_name,
                "points_count": collection_info.points_count,
                "config": {
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance
                }
            }
            if hasattr(collection_info, "vectors_count"):
                info["vectors_count"] = collection_info.vectors_count
            else:
                info["vectors_count"] = collection_info.points_count  
            return info
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
