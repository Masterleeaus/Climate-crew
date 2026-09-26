"""
Memory module for Convolve_MAS agents.
Provides hierarchical memory with working, episodic, semantic, and shared tiers.
"""

from .memory_manager import MemoryManager
from .advanced_memory import AdvancedMemoryManager
from .working_memory import WorkingMemory, WorkingMemoryItem
from .episodic_memory import EpisodicMemory, EpisodicMemoryItem
from .semantic_memory import SemanticMemory, Entity, Relationship, Fact
from .shared_pool import SharedMemoryPool, SharedMemoryItem
from .consolidator import MemoryConsolidator
from .performance_store import PerformanceStore, RoutingRecord, AgentStats

__all__ = [
    "MemoryManager",  # Legacy
    "AdvancedMemoryManager",
    "WorkingMemory",
    "WorkingMemoryItem",
    "EpisodicMemory",
    "EpisodicMemoryItem",
    "SemanticMemory",
    "Entity",
    "Relationship",
    "Fact",
    "SharedMemoryPool",
    "SharedMemoryItem",
    "MemoryConsolidator",
    "PerformanceStore",
    "RoutingRecord",
    "AgentStats",
]

