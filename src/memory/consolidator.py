"""
Memory Consolidator - Background process for memory maintenance.
Consolidates episodic memories into semantic facts and prunes old memories.
"""
import os
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Background process that:
    1. Extracts entities/relationships from episodic memories
    2. Stores them in semantic memory (Neo4j)
    3. Marks episodic memories as consolidated
    4. Prunes old, low-importance memories
    """
    
    def __init__(
        self,
        episodic_memory,
        semantic_memory,
        google_api_key: Optional[str] = None,
        consolidation_interval_hours: float = 6,
        max_memory_age_days: int = 30,
        min_importance_threshold: float = 0.3
    ):
        self.episodic = episodic_memory
        self.semantic = semantic_memory
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.interval_hours = consolidation_interval_hours
        self.max_age_days = max_memory_age_days
        self.min_importance = min_importance_threshold
        self._running = False
        self._llm = None
    
    def _ensure_llm(self):
        """Initialize LLM for entity extraction."""
        if self._llm:
            return True
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.google_api_key,
                temperature=0.1
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize consolidator LLM: {e}")
            return False
    
    async def run(self):
        """Start the background consolidation loop."""
        self._running = True
        logger.info(f"Memory consolidator started (interval: {self.interval_hours}h)")
        
        while self._running:
            try:
                await self.consolidate()
            except Exception as e:
                logger.error(f"Consolidation error: {e}")
            
            await asyncio.sleep(self.interval_hours * 3600)
    
    def stop(self):
        """Stop the consolidation loop."""
        self._running = False
        logger.info("Memory consolidator stopped")
    
    async def consolidate(self):
        """Run a single consolidation cycle."""
        logger.info("Starting memory consolidation cycle...")
        
        # 1. Get recent unconsolidated memories
        # For now, we'll search for recent memories
        memories = self.episodic.search(
            query="important climate information",  # Broad search
            agent_id="*",  # All agents (needs custom handling)
            limit=50,
            apply_recency=False
        )
        
        if not memories:
            logger.info("No memories to consolidate")
            return
        
        # 2. Extract entities and relationships
        for memory in memories:
            if memory.consolidated:
                continue
            
            if memory.importance < self.min_importance:
                continue
            
            try:
                extracted = await self._extract_knowledge(memory.content)
                
                # 3. Store in semantic memory
                if extracted.get("entities"):
                    for entity in extracted["entities"]:
                        from .semantic_memory import Entity
                        self.semantic.add_entity(Entity(
                            name=entity["name"],
                            entity_type=entity.get("type", "unknown")
                        ))
                
                if extracted.get("relationships"):
                    for rel in extracted["relationships"]:
                        from .semantic_memory import Relationship
                        self.semantic.add_relationship(Relationship(
                            source=rel["source"],
                            relation_type=rel["relation"],
                            target=rel["target"],
                            source_agent=memory.agent_id
                        ))
                
                if extracted.get("facts"):
                    for fact in extracted["facts"]:
                        from .semantic_memory import Fact
                        self.semantic.add_fact(Fact(
                            content=fact["content"],
                            entity=fact.get("entity", "general"),
                            source_agent=memory.agent_id
                        ))
                
                # 4. Mark as consolidated
                self.episodic.mark_consolidated(memory.id)
                
            except Exception as e:
                logger.warning(f"Failed to consolidate memory {memory.id}: {e}")
        
        # 5. Prune old memories
        await self._prune_old_memories()
        
        logger.info("Memory consolidation cycle complete")
    
    async def _extract_knowledge(self, content: str) -> Dict[str, Any]:
        """Use LLM to extract entities, relationships, and facts from text."""
        if not self._ensure_llm():
            return {}
        
        prompt = f"""Extract structured knowledge from the following text.
Return JSON with:
- entities: list of {{name, type}} where type is one of: location, organization, event, concept, metric
- relationships: list of {{source, relation, target}}
- facts: list of {{content, entity}} where entity is the main subject

Text: {content}

Return ONLY valid JSON, no markdown:"""
        
        try:
            response = self._llm.invoke([{"role": "user", "content": prompt}])
            result_text = response.content
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.warning(f"Knowledge extraction failed: {e}")
            return {}
    
    async def _prune_old_memories(self):
        """Remove old, low-importance memories."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        logger.info(f"Pruning memories older than {self.max_age_days} days")
        # Would need to implement get_old_memories and delete in episodic memory
        # For now, just log
        pass
    
    def consolidate_sync(self):
        """Synchronous wrapper for consolidation (for testing)."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.consolidate())
        finally:
            loop.close()
