"""
Semantic Memory - Permanent knowledge graph storage using Neo4j.
Stores extracted entities, facts, and relationships.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an entity in semantic memory."""
    name: str
    entity_type: str  # "location", "organization", "concept", "event", etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source: str
    relation_type: str  # "located_in", "causes", "affects", "related_to", etc.
    target: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_agent: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass 
class Fact:
    """Represents a semantic fact/claim."""
    content: str
    entity: str
    source_agent: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SemanticMemory:
    """
    Permanent semantic memory using Neo4j graph database.
    - Stores entities, relationships, and facts
    - Supports graph queries for knowledge retrieval
    - Facts are never auto-deleted (permanent knowledge)
    """
    
    def __init__(
        self,
        neo4j_url: Optional[str] = None,
        neo4j_username: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        self.neo4j_url = neo4j_url or os.getenv("NEO4J_URL")
        self.neo4j_username = neo4j_username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self._driver = None
        self._initialized = False
    
    def _ensure_initialized(self) -> bool:
        """Lazy initialization of Neo4j driver."""
        if self._initialized:
            return True
        
        if not self.neo4j_url or not self.neo4j_password:
            logger.warning("Neo4j not configured. Semantic memory disabled.")
            return False
        
        try:
            from neo4j import GraphDatabase
            
            self._driver = GraphDatabase.driver(
                self.neo4j_url,
                auth=(self.neo4j_username, self.neo4j_password)
            )
            # Verify connection
            self._driver.verify_connectivity()
            self._initialized = True
            logger.info("Semantic memory initialized with Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic memory: {e}")
            return False
    
    def add_entity(self, entity: Entity) -> bool:
        """Add or update an entity in the graph."""
        if not self._ensure_initialized():
            return False
        
        try:
            with self._driver.session() as session:
                query = """
                MERGE (e:Entity {name: $name})
                SET e.entity_type = $entity_type,
                    e.properties = $properties,
                    e.last_updated = $last_updated
                ON CREATE SET e.first_seen = $first_seen
                """
                session.run(
                    query,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    properties=str(entity.properties),
                    first_seen=entity.first_seen.isoformat(),
                    last_updated=entity.last_updated.isoformat()
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add entity: {e}")
            return False
    
    def add_relationship(self, relationship: Relationship) -> bool:
        """Add a relationship between entities."""
        if not self._ensure_initialized():
            return False
        
        try:
            with self._driver.session() as session:
                query = f"""
                MERGE (s:Entity {{name: $source}})
                MERGE (t:Entity {{name: $target}})
                MERGE (s)-[r:{relationship.relation_type.upper().replace(' ', '_')}]->(t)
                SET r.source_agent = $source_agent,
                    r.created_at = $created_at,
                    r.properties = $properties
                """
                session.run(
                    query,
                    source=relationship.source,
                    target=relationship.target,
                    source_agent=relationship.source_agent,
                    created_at=relationship.created_at.isoformat(),
                    properties=str(relationship.properties)
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add relationship: {e}")
            return False
    
    def add_fact(self, fact: Fact) -> bool:
        """Add a fact linked to an entity."""
        if not self._ensure_initialized():
            return False
        
        try:
            with self._driver.session() as session:
                query = """
                MERGE (e:Entity {name: $entity})
                CREATE (f:Fact {
                    content: $content,
                    source_agent: $source_agent,
                    confidence: $confidence,
                    created_at: $created_at
                })
                MERGE (f)-[:ABOUT]->(e)
                """
                session.run(
                    query,
                    entity=fact.entity,
                    content=fact.content,
                    source_agent=fact.source_agent,
                    confidence=fact.confidence,
                    created_at=fact.created_at.isoformat()
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add fact: {e}")
            return False
    
    def search_entity(self, name: str) -> Optional[Dict]:
        """Search for an entity and its relationships."""
        if not self._ensure_initialized():
            return None
        
        try:
            with self._driver.session() as session:
                query = """
                MATCH (e:Entity {name: $name})
                OPTIONAL MATCH (e)-[r]->(related)
                OPTIONAL MATCH (f:Fact)-[:ABOUT]->(e)
                RETURN e, collect(DISTINCT {relation: type(r), target: related.name}) as relations,
                       collect(DISTINCT f.content) as facts
                """
                result = session.run(query, name=name)
                record = result.single()
                
                if record:
                    entity = record["e"]
                    return {
                        "name": entity["name"],
                        "entity_type": entity.get("entity_type"),
                        "relations": [r for r in record["relations"] if r["target"]],
                        "facts": record["facts"]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to search entity: {e}")
            return None
    
    def get_related_entities(self, name: str, depth: int = 2) -> List[Dict]:
        """Get entities related to a given entity up to N hops."""
        if not self._ensure_initialized():
            return []
        
        try:
            with self._driver.session() as session:
                query = f"""
                MATCH path = (e:Entity {{name: $name}})-[*1..{depth}]-(related:Entity)
                RETURN DISTINCT related.name as name, related.entity_type as type
                LIMIT 20
                """
                result = session.run(query, name=name)
                return [{"name": r["name"], "type": r["type"]} for r in result]
        except Exception as e:
            logger.error(f"Failed to get related entities: {e}")
            return []
    
    def get_context_string(self, query: str, limit: int = 5) -> str:
        """Extract entity names from query and get their knowledge."""
        # Simple keyword extraction - in production, use NER
        # For now, just return empty if not initialized
        if not self._ensure_initialized():
            return ""
        
        # This would use NER to extract entities from query
        # then fetch their facts and relationships
        return ""
    
    def close(self):
        """Close the Neo4j driver."""
        if self._driver:
            self._driver.close()
