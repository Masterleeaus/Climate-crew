"""
Article-specific chat manager with RAG.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from google import genai

from .models import ArticleChatRequest, ArticleChatResponse
from .qdrant_manager import NewsQdrantManager
from ..rag.rag_manager import RAGManager
from ..memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ArticleChatManager:
    """Manage chat conversations about specific articles with persistent memory."""
    
    def __init__(
        self,
        qdrant_manager: NewsQdrantManager,
        google_api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        memory_manager: Optional[MemoryManager] = None
    ):
        self.qdrant_manager = qdrant_manager
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set")
        
        self._genai_client = genai.Client(api_key=self.google_api_key)
        
        # Initialize memory manager for persistent conversation storage
        if memory_manager:
            self.memory_manager = memory_manager
        else:
            try:
                self.memory_manager = MemoryManager(google_api_key=self.google_api_key)
                logger.info("Memory manager initialized for article chat")
            except Exception as e:
                logger.warning(f"Failed to initialize memory manager: {e}. Using in-memory storage only.")
                self.memory_manager = None
        
        # In-memory conversation cache for quick access (backed by persistent memory)
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history from cache or persistent memory."""
        # Check in-memory cache first
        if conversation_id in self._conversations:
            return self._conversations[conversation_id]
        
        # Load from persistent memory if available
        if self.memory_manager:
            try:
                memories = self.memory_manager.get_all(agent_id=conversation_id)
                # Convert memories to conversation format
                history = []
                for mem in memories:
                    memory_text = mem.get("memory", mem.get("text", ""))
                    if not memory_text:
                        continue
                    
                    metadata = mem.get("metadata", {})
                    # Extract role from metadata (we store it explicitly)
                    role = metadata.get("role")
                    if not role:
                        # Try to infer from memory text format "Role: content"
                        if memory_text.startswith("User:"):
                            role = "user"
                            content = memory_text[5:].strip()
                        elif memory_text.startswith("Assistant:"):
                            role = "assistant"
                            content = memory_text[10:].strip()
                        else:
                            # Default to user if unclear
                            role = "user"
                            content = memory_text
                    else:
                        # Extract content (remove role prefix if present)
                        if memory_text.startswith(f"{role.capitalize()}: "):
                            content = memory_text[len(f"{role.capitalize()}: "):].strip()
                        else:
                            content = memory_text
                    
                    history.append({
                        "role": role,
                        "content": content,
                        "timestamp": metadata.get("timestamp", datetime.utcnow().isoformat())
                    })
                
                # Sort by timestamp to maintain conversation order
                history.sort(key=lambda x: x.get("timestamp", ""))
                
                # Cache in memory
                if history:
                    self._conversations[conversation_id] = history
                return history
            except Exception as e:
                logger.warning(f"Failed to load conversation history from memory: {e}")
        
        return []
    
    def _add_to_conversation(self, conversation_id: str, role: str, content: str):
        """Add message to conversation history (both cache and persistent memory)."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to in-memory cache
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append(message)
        
        # Store in persistent memory
        if self.memory_manager:
            try:
                # Format message for memory storage
                memory_content = f"{role.capitalize()}: {content}"
                metadata = {
                    "role": role,
                    "conversation_id": conversation_id,
                    "timestamp": message["timestamp"],
                    "type": "conversation_message"
                }
                self.memory_manager.add(
                    content=memory_content,
                    agent_id=conversation_id,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Failed to store message in persistent memory: {e}")
        
        # Keep conversation history manageable (last 20 messages in cache)
        if len(self._conversations[conversation_id]) > 20:
            self._conversations[conversation_id] = self._conversations[conversation_id][-20:]
    
    def _retrieve_article_context(self, article_id: str, query: str) -> str:
        """Retrieve relevant chunks from article using RAG."""
        article = self.qdrant_manager.get_article_by_id(article_id)
        if not article:
            return ""
        
        # Get all chunks for the article
        chunks = self.qdrant_manager._get_all_chunks_for_article(article_id)
        
        if not chunks:
            return article.content
        
        # Use RAG manager to find most relevant chunks
        try:
            rag_manager = self.qdrant_manager.rag_manager
            
            # Get query embedding for semantic search
            query_embedding = rag_manager._get_embedding(query, task_type="RETRIEVAL_QUERY")
            
            # Search within article chunks with lower threshold to get more context
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            query_response = self.qdrant_manager._qdrant_client.query_points(
                collection_name=self.qdrant_manager.collection_name,
                query=query_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="article_id",
                            match=MatchValue(value=article_id)
                        )
                    ]
                ),
                limit=10,  # Get more chunks for better context
                score_threshold=0.3  # Lower threshold to get more relevant content
            )
            
            # Combine relevant chunks, sorted by score (highest first)
            relevant_chunks = []
            scored_chunks = [(result.score, result.payload.get("text", "")) for result in query_response.points]
            scored_chunks.sort(reverse=True, key=lambda x: x[0])  # Sort by score descending
            
            # Use top chunks, but also ensure we have enough content
            for score, text in scored_chunks:
                if text.strip():
                    relevant_chunks.append(text)
            
            # If we have good semantic matches, use them
            if relevant_chunks:
                context = "\n\n".join(relevant_chunks)
                # If context is too short, supplement with more chunks
                if len(context) < 500 and len(chunks) > len(relevant_chunks):
                    # Add a few more chunks from the article
                    remaining_chunks = [chunk["text"] for chunk in chunks if chunk["text"] not in relevant_chunks]
                    context += "\n\n" + "\n\n".join(remaining_chunks[:3])
                return context
            else:
                # Fallback: use first several chunks to ensure we have content
                return "\n\n".join([chunk["text"] for chunk in chunks[:8]])
        
        except Exception as e:
            logger.error(f"Error retrieving article context: {e}")
            # Fallback to full article content or first chunks
            if article.content:
                return article.content
            return "\n\n".join([chunk["text"] for chunk in chunks[:10]])
    
    def chat(
        self,
        request: ArticleChatRequest
    ) -> ArticleChatResponse:
        """Chat about a specific article."""
        # Get or create conversation ID
        conversation_id = request.conversation_id or f"article_{request.article_id}_{datetime.utcnow().timestamp()}"
        
        # Get article
        article = self.qdrant_manager.get_article_by_id(request.article_id)
        if not article:
            raise ValueError(f"Article {request.article_id} not found")
        
        # Retrieve relevant context from article
        article_context = self._retrieve_article_context(request.article_id, request.message)
        
        # Get conversation history (from persistent memory if available)
        history = self._get_conversation_history(conversation_id)
        
        # Build prompt with conversation history
        conversation_context = ""
        if history:
            conversation_context = "\n\nPrevious conversation:\n"
            # Include more history for better context (last 10 messages = 5 exchanges)
            for msg in history[-10:]:
                role_label = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"{role_label}: {msg['content']}\n"
        
        # Also retrieve relevant memories if available
        memory_context = ""
        if self.memory_manager and history:
            try:
                # Search for relevant memories related to this conversation
                memory_results = self.memory_manager.search(
                    query=f"{request.message} {article.title}",
                    agent_id=conversation_id,
                    limit=3
                )
                if memory_results:
                    memory_context = "\n\nRelevant context from previous conversations:\n"
                    for mem in memory_results:
                        memory_text = mem.get("memory", mem.get("text", ""))
                        if memory_text:
                            memory_context += f"- {memory_text}\n"
            except Exception as e:
                logger.debug(f"Failed to retrieve memory context: {e}")
        
        # Include summary if available
        summary_section = ""
        if article.summary:
            summary_section = f"\nArticle Summary: {article.summary}\n"
        
        prompt = f"""You are an expert climate news analyst helping users understand news articles. Answer the user's question based on the article content provided below.

Article Information:
- Title: {article.title}
- Source: {article.source}
- Published: {article.published_at.strftime('%Y-%m-%d')}
- URL: {article.url}
{summary_section}
Article Content:
{article_context}
{conversation_context}{memory_context}
User Question: {request.message}

Your task:
1. Read the article content carefully
2. Answer the user's question using specific information from the article
3. Provide a clear, informative answer that directly addresses the question
4. Include relevant details, numbers, and facts from the article when available
5. If the article mentions how something works (like how green tech cuts energy bills), explain it based on what the article says
6. Be helpful and comprehensive - don't just say "the article doesn't specify" if you can infer or explain based on the content
7. If you need to make reasonable inferences from the article content, do so and note that you're inferring

Answer the question now:"""
        
        # Generate response
        try:
            # Import types for config if available
            try:
                from google.genai import types
                config = types.GenerateContentConfig(
                    temperature=0.7,  # Slightly creative but still factual
                    top_p=0.95,
                    top_k=40
                )
            except ImportError:
                config = None
            
            # Use the direct generate_content method with model parameter
            response = self._genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                answer = response.text
            elif isinstance(response, dict):
                answer = response.get('text', '') or response.get('content', '')
            else:
                answer = str(response)
            
            # Extract citations (simple - in production, use more sophisticated extraction)
            citations = []
            if article.url:
                citations.append({
                    "type": "article",
                    "title": article.title,
                    "url": article.url,
                    "source": article.source
                })
            
            # Get related articles
            related_articles = []
            if not request.deep_research:
                related = self.qdrant_manager.get_related_articles(request.article_id, limit=3)
                related_articles = [
                    {
                        "id": r.id,
                        "title": r.title,
                        "url": r.url,
                        "source": r.source
                    }
                    for r in related
                ]
            
            # Store in conversation history
            self._add_to_conversation(conversation_id, "user", request.message)
            self._add_to_conversation(conversation_id, "assistant", answer)
            
            return ArticleChatResponse(
                answer=answer,
                citations=citations,
                related_articles=related_articles,
                conversation_id=conversation_id,
                deep_research_used=False
            )
        
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise ValueError(f"Failed to generate response: {str(e)}")
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history for a specific conversation."""
        # Clear in-memory cache
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
        
        # Clear persistent memory
        if self.memory_manager:
            try:
                return self.memory_manager.clear_agent_memories(agent_id=conversation_id)
            except Exception as e:
                logger.error(f"Failed to clear conversation from memory: {e}")
                return False
        
        return True
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """Get a summary of the conversation."""
        history = self._get_conversation_history(conversation_id)
        if not history:
            return None
        
        # Count messages
        user_messages = sum(1 for msg in history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in history if msg["role"] == "assistant")
        
        return f"Conversation has {len(history)} messages ({user_messages} user, {assistant_messages} assistant)"
