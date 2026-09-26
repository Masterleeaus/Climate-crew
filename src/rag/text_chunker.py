"""
Text chunking utilities for splitting documents into manageable pieces.
Supports both fixed-size and semantic chunking.
"""

import logging
from typing import List, Dict, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for semantic chunking
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class TextChunker:
    """Split text into chunks for embedding and retrieval."""
    
    def __init__(
        self,
        chunk_size: int = 100000,
        chunk_overlap: int = 2000,
        separators: Optional[List[str]] = None,
        use_semantic_chunking: bool = False,
        semantic_model: str = "all-MiniLM-L6-v2",
        semantic_threshold: float = 0.5
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to prefer when splitting
            use_semantic_chunking: Use semantic similarity for chunking instead of fixed-size
            semantic_model: Sentence transformer model for semantic chunking
            semantic_threshold: Similarity threshold for grouping sentences semantically
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.use_semantic_chunking = use_semantic_chunking
        self.semantic_model = semantic_model
        self.semantic_threshold = semantic_threshold
        self._semantic_model = None
        
        if self.use_semantic_chunking:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self._semantic_model = SentenceTransformer(self.semantic_model)
                    logger.info(f"Semantic chunking enabled with model: {self.semantic_model}")
                except Exception as e:
                    logger.warning(f"Failed to load semantic model: {e}. Falling back to fixed-size chunking.")
                    self.use_semantic_chunking = False
            else:
                logger.warning("sentence-transformers not available. Falling back to fixed-size chunking.")
                self.use_semantic_chunking = False
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with 'text' and 'metadata'
        """
        if not text or not text.strip():
            return []
        
        if self.use_semantic_chunking and self._semantic_model:
            return self._semantic_chunk_text(text, metadata)
        else:
            return self._fixed_size_chunk_text(text, metadata)
    
    def _fixed_size_chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """Split text using fixed-size chunking."""
        chunks = []
        metadata = metadata or {}
        
        # Try to split by separators in order of preference
        current_text = text
        chunk_id = 0
        
        while current_text:
            # Find the best split point
            chunk_text, remaining_text = self._split_at_separator(
                current_text,
                self.chunk_size
            )
            
            if chunk_text:
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": len(chunks),
                    "chunk_size": len(chunk_text)
                }
                chunks.append({
                    "text": chunk_text.strip(),
                    "metadata": chunk_meta
                })
                chunk_id += 1
            
            if not remaining_text or remaining_text == current_text:
                break
            
            # Handle overlap
            if self.chunk_overlap > 0 and remaining_text:
                overlap_text = chunk_text[-self.chunk_overlap:] if chunk_text else ""
                current_text = overlap_text + remaining_text
            else:
                current_text = remaining_text
        
        logger.info(f"Created {len(chunks)} chunks from text (size: {len(text)})")
        return chunks
    
    def _semantic_chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """Split text using semantic similarity."""
        metadata = metadata or {}
        
        # Split text into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        # Get embeddings for all sentences
        try:
            embeddings = self._semantic_model.encode(sentences, normalize_embeddings=True)
        except Exception as e:
            logger.warning(f"Error encoding sentences: {e}. Falling back to fixed-size chunking.")
            return self._fixed_size_chunk_text(text, metadata)
        
        # Group sentences by semantic similarity
        chunks = []
        current_chunk = [sentences[0]]
        current_embedding = embeddings[0]
        chunk_id = 0
        
        for i in range(1, len(sentences)):
            # Calculate similarity with current chunk centroid
            similarity = np.dot(current_embedding, embeddings[i])
            
            # Check if we should start a new chunk
            should_split = (
                similarity < self.semantic_threshold or
                len(' '.join(current_chunk)) > self.chunk_size
            )
            
            if should_split and len(current_chunk) > 0:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": len(chunks),
                    "chunk_size": len(chunk_text),
                    "chunking_method": "semantic"
                }
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_meta
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and len(current_chunk) > 0:
                    overlap_sentences = current_chunk[-max(1, len(current_chunk) // 4):]
                    current_chunk = overlap_sentences + [sentences[i]]
                    # Recalculate embedding for overlap + new sentence
                    overlap_text = ' '.join(overlap_sentences)
                    new_text = ' '.join([overlap_text, sentences[i]])
                    current_embedding = self._semantic_model.encode([new_text], normalize_embeddings=True)[0]
                else:
                    current_chunk = [sentences[i]]
                    current_embedding = embeddings[i]
            else:
                # Add to current chunk
                current_chunk.append(sentences[i])
                # Update centroid embedding (simple average)
                current_embedding = (current_embedding * (len(current_chunk) - 1) + embeddings[i]) / len(current_chunk)
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_meta = {
                **metadata,
                "chunk_id": chunk_id,
                "chunk_index": len(chunks),
                "chunk_size": len(chunk_text),
                "chunking_method": "semantic"
            }
            chunks.append({
                "text": chunk_text,
                "metadata": chunk_meta
            })
        
        logger.info(f"Created {len(chunks)} semantic chunks from text (size: {len(text)})")
        return chunks
    
    def _split_at_separator(self, text: str, max_size: int) -> tuple[str, str]:
        """
        Split text at the best separator within max_size.
        
        Returns:
            Tuple of (chunk_text, remaining_text)
        """
        if len(text) <= max_size:
            return text, ""
        
        # Try each separator in order
        for separator in self.separators:
            if not separator:
                # Last resort: hard cut
                return text[:max_size], text[max_size:]
            
            # Find last occurrence of separator within max_size
            search_text = text[:max_size]
            last_index = search_text.rfind(separator)
            
            if last_index > 0:
                split_point = last_index + len(separator)
                return text[:split_point], text[split_point:]
        
        # Fallback: hard cut
        return text[:max_size], text[max_size:]
    
    def chunk_documents(self, documents: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Chunk a list of documents.
        
        Args:
            documents: List of document dictionaries with 'text' and 'metadata'
            
        Returns:
            List of chunk dictionaries
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_text(
                doc.get("text", ""),
                metadata=doc.get("metadata", {})
            )
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} total chunks from {len(documents)} documents")
        return all_chunks
