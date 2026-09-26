import os
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MemoryManager:
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        neo4j_url: Optional[str] = None,
        neo4j_username: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        collection_name: str = "convolve_mas_memory",
        google_api_key: Optional[str] = None
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.neo4j_url = neo4j_url or os.getenv("NEO4J_URL")
        self.neo4j_username = neo4j_username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.collection_name = collection_name
        self._memory = None
        self._initialized = False
        
    def _ensure_initialized(self):
        if self._initialized:
            return True
            
        if not self.qdrant_url or not self.qdrant_api_key:
            logger.warning("Qdrant not configured. Memory features disabled.")
            return False
        
        try:
            from mem0 import Memory
            
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": self.collection_name,
                        "url": self.qdrant_url,
                        "api_key": self.qdrant_api_key,
                        "embedding_model_dims": 768
                    }
                },
                "llm": {
                    "provider": "gemini",
                    "config": {
                        "model": "gemini-2.0-flash",
                        "api_key": self.google_api_key
                    }
                },
                "embedder": {
                    "provider": "gemini",
                    "config": {
                        "model": "gemini-embedding-001",
                        "api_key": self.google_api_key
                    }
                }
            }
            
            if self.neo4j_url and self.neo4j_password:
                config["graph_store"] = {
                    "provider": "neo4j",
                    "config": {
                        "url": self.neo4j_url,
                        "username": self.neo4j_username,
                        "password": self.neo4j_password
                    }
                }
                logger.info("Mem0g mode: Graph memory enabled with Neo4j")
            
            self._memory = Memory.from_config(config)
            self._initialized = True
            logger.info("Memory manager initialized")
            return True
            
        except ImportError:
            logger.error("mem0ai not installed. Run: pip install 'mem0ai[graph]'")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}")
            return False
    
    def add(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        if not self._ensure_initialized():
            return None
        
        retries = 3
        delay = 5
        
        for attempt in range(retries):
            try:
                meta = metadata or {}
                meta["timestamp"] = datetime.now(timezone.utc).isoformat()
                meta["agent_id"] = agent_id
                return self._memory.add(content, user_id=agent_id, metadata=meta)
            except Exception as e:
                is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                if is_rate_limit and attempt < retries - 1:
                    logger.warning(f"Rate limit hit (add), retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Failed to add memory: {e}")
                    return None
    
    def search(self, query: str, agent_id: str, limit: int = 5) -> List[Dict]:
        if not self._ensure_initialized():
            return []
            
        retries = 3
        delay = 5
        
        for attempt in range(retries):
            try:
                response = self._memory.search(query, user_id=agent_id, limit=limit)
                
                final_results = []
                
                # Handle Mem0g dict response (Vector + Graph)
                if isinstance(response, dict):
                    # Add vector results
                    if "results" in response and isinstance(response["results"], list):
                        final_results.extend(response["results"])
                    
                    # Add graph relations as formatted text memories
                    if "relations" in response and isinstance(response["relations"], list):
                        for rel in response["relations"]:
                            src = rel.get("source")
                            relation = rel.get("relationship", rel.get("relation"))
                            target = rel.get("target", rel.get("destination"))
                            
                            if src and relation and target:
                                final_results.append({
                                    "memory": f"Relationship: {src} {relation} {target}",
                                    "score": 1.0, # Artificial score for graph hits
                                    "id": f"rel_{src}_{relation}_{target}"
                                })
                
                # Handle standard list response (Vector only)
                elif isinstance(response, list):
                    final_results = response
                
                return final_results
            except Exception as e:
                is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                if is_rate_limit and attempt < retries - 1:
                    logger.warning(f"Rate limit hit (search), retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Failed to search memory: {e}")
                    return []
        return []
    
    def get_all(self, agent_id: str) -> List[Dict]:
        if not self._ensure_initialized():
            return []
            
        retries = 3
        delay = 5
            
        for attempt in range(retries):
            try:
                response = self._memory.get_all(user_id=agent_id)
                
                final_results = []
                
                if isinstance(response, dict):
                    if "results" in response and isinstance(response["results"], list):
                        final_results.extend(response["results"])
                    
                    if "relations" in response and isinstance(response["relations"], list):
                         for rel in response["relations"]:
                            src = rel.get("source")
                            relation = rel.get("relationship", rel.get("relation"))
                            target = rel.get("target", rel.get("destination"))
                            if src and relation and target:
                                final_results.append({
                                    "memory": f"{src} {relation} {target}",
                                    "id": f"rel_{src}_{relation}_{target}"
                                })
                elif isinstance(response, list):
                    final_results = response
                    
                return final_results
            except Exception as e:
                is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                if is_rate_limit and attempt < retries - 1:
                    logger.warning(f"Rate limit hit (get_all), retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Failed to get memories: {e}")
                    return []
        return []
    
    def get_context_string(self, query: str, agent_id: str, limit: int = 3) -> str:
        memories = self.search(query, agent_id, limit)
        if not memories:
            return ""
        context_parts = ["Relevant context from memory:"]
        for mem in memories:
            memory_text = mem.get("memory", mem.get("text", ""))
            if memory_text:
                context_parts.append(f"- {memory_text}")
        return "\n".join(context_parts)
    
    def delete(self, memory_id: str) -> bool:
        if not self._ensure_initialized():
            return False
        try:
            self._memory.delete(memory_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    def clear_agent_memories(self, agent_id: str) -> bool:
        if not self._ensure_initialized():
            return False
        try:
            self._memory.delete_all(user_id=agent_id)
            return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False
