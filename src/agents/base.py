from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime
import os
import logging
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langsmith import traceable

if TYPE_CHECKING:
    from ..memory import MemoryManager, AdvancedMemoryManager
    from ..rag import RAGManager
    from .protocols.message_bus import MessageBus
    from .protocols.negotiation import InfoRequest, InfoResponse

logging.basicConfig(level=logging.INFO)


class BaseAgent(ABC):    
    def __init__(
        self,
        name: str,
        google_api_key: Optional[str] = None,
        memory_manager: Optional['MemoryManager'] = None,
        advanced_memory: Optional['AdvancedMemoryManager'] = None,
        enable_memory: bool = True,
        rag_manager: Optional['RAGManager'] = None,
        enable_rag: bool = True,
        tool_builder: Optional[Any] = None,
        use_advanced_memory: bool = True  # Use new hierarchical memory
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = None
        self.tool_builder = tool_builder
        self.llm_with_tools = None
        
        # Memory integration
        self.memory = memory_manager  # Legacy memory
        self.advanced_memory = advanced_memory  # New hierarchical memory
        self.enable_memory = enable_memory
        self.use_advanced_memory = use_advanced_memory
        
        # RAG integration
        self.rag = rag_manager
        self.enable_rag = enable_rag
        
        # Dynamic Tool Loading (Self-Evolution)
        from ..utils.dynamic_tool_loader import DynamicToolLoader
        self.tool_loader = DynamicToolLoader()
        
        # Collaboration capabilities
        self.message_bus: Optional['MessageBus'] = None
        self.negotiation_protocol = None
        
        # Performance tracking for meta-learning
        self.last_performance: Dict[str, Any] = {
            "query": "",
            "latency_ms": 0.0,
            "reflexion_score": 1.0,
            "success": True
        }
        
        self.conversation_history: List[Dict] = []
        self._max_history_turns = 6  # Keep last 3 conversation turns
        
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=self.api_key,
                temperature=0.3
            )
    
    def set_memory_manager(self, memory_manager: 'MemoryManager'):
        self.memory = memory_manager
    
    def set_advanced_memory(self, advanced_memory: 'AdvancedMemoryManager'):
        self.advanced_memory = advanced_memory
        
    def set_tool_builder(self, tool_builder: Any):
        self.tool_builder = tool_builder

    def set_rag_manager(self, rag_manager: 'RAGManager'):
        self.rag = rag_manager
    
    def set_message_bus(self, bus: 'MessageBus'):
        """Set the message bus for inter-agent communication."""
        self.message_bus = bus
    
    def set_negotiation_protocol(self, protocol):
        """Set the negotiation protocol for peer requests."""
        self.negotiation_protocol = protocol
    
    def request_from_peer(self, peer_name: str, query: str, context: Optional[Dict] = None) -> str:
        """
        Request information from a peer agent.
        
        Args:
            peer_name: Name of the peer agent to ask
            query: The question to ask
            context: Optional context to provide
            
        Returns:
            Response from the peer agent
        """
        if not self.negotiation_protocol:
            self.logger.warning("No negotiation protocol set, cannot request from peer")
            return "Peer communication not available"
        
        from .protocols.negotiation import InfoRequest, RequestPriority
        
        response = self.negotiation_protocol.request_info(
            from_agent=self.name,
            to_agent=peer_name,
            query=query,
            context=context,
            priority=RequestPriority.NORMAL
        )
        
        if response.can_help:
            return response.content
        else:
            return f"Peer {peer_name} could not help with this query."
    
    def can_help_with(self, query: str) -> tuple[bool, float]:
        """
        Check if this agent can help with a query.
        Override in subclasses for domain-specific logic.
        
        Returns:
            Tuple of (can_help, confidence)
        """
        # Default: use system prompt keyword matching
        system_prompt = self.get_system_prompt().lower()
        query_lower = query.lower()
        
        # Simple overlap check
        query_words = set(query_lower.split())
        prompt_words = set(system_prompt.split())
        overlap = len(query_words & prompt_words) / max(len(query_words), 1)
        
        can_help = overlap > 0.1
        confidence = min(1.0, overlap * 2)
        
        return can_help, confidence
    
    def broadcast_knowledge(self, content: str, importance: float = 0.5):
        """Broadcast knowledge to other agents via message bus."""
        if self.message_bus:
            from .protocols.message_bus import MessageType
            self.message_bus.broadcast(
                content=content,
                source_agent=self.name,
                message_type=MessageType.KNOWLEDGE_SHARE,
                metadata={"importance": importance}
            )
    
    def bind_tools(self, tools: List[Callable]):
        if self.llm:
            self.llm_with_tools = self.llm.bind_tools(tools)
    
    @abstractmethod
    def get_tools(self) -> List[Callable]:
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        pass
    
    def _get_memory_context(self, query: str) -> str:
        """Get memory context from hierarchical memory system."""
        if not self.enable_memory:
            return ""
        
        try:
            # Use advanced memory if available
            if self.use_advanced_memory and self.advanced_memory:
                return self.advanced_memory.get_context_string(query, self.name, limit=3)
            # Fallback to legacy memory
            elif self.memory:
                return self.memory.get_context_string(query, agent_id=self.name, limit=3)
            return ""
        except Exception as e:
            self.logger.warning(f"Failed to retrieve memory context: {e}")
            return ""
    
    def _get_rag_context(self, query: str) -> str:
        if not self.rag or not self.enable_rag:
            return ""
        
        try:
            return self.rag.get_context(query, limit=3)
        except Exception as e:
            self.logger.warning(f"Failed to retrieve RAG context: {e}")
            return ""
    
    def _store_memory(self, content: str, metadata: Optional[Dict] = None, 
                      tier: str = "episodic", share: bool = False, importance: float = 0.5):
        """Store memory in appropriate tier of hierarchical memory."""
        if not self.enable_memory:
            return
        
        try:
            # Use advanced memory if available
            if self.use_advanced_memory and self.advanced_memory:
                # Store in working memory for session context
                if tier == "working":
                    self.advanced_memory.add_to_working(content, self.name)
                # Store in episodic memory
                elif tier == "episodic":
                    self.advanced_memory.add_to_episodic(content, self.name, importance, metadata)
                
                # Share important knowledge across agents
                if share:
                    self.advanced_memory.share(content, self.name, "global", importance)
            # Fallback to legacy memory
            elif self.memory:
                self.memory.add(content, agent_id=self.name, metadata=metadata)
        except Exception as e:
            self.logger.warning(f"Failed to store memory: {e}")

    def store_to_working_memory(self, content: str, item_type: str = "context"):
        """Add item to session working memory buffer."""
        if self.advanced_memory:
            self.advanced_memory.add_to_working(content, self.name, item_type)

    def share_knowledge(self, content: str, importance: float = 0.5):
        """Share knowledge to cross-agent shared pool."""
        if self.advanced_memory:
            self.advanced_memory.share(content, self.name, "global", importance)

    def get_all_memories(self) -> List[Dict]:
        if not self.memory:
            return []
        return self.memory.get_all(self.name)
    
    def _update_conversation_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only the last N messages
        if len(self.conversation_history) > self._max_history_turns:
            self.conversation_history = self.conversation_history[-self._max_history_turns:]
    
    def clear_memories(self) -> bool:
        if not self.memory:
            return False
        return self.memory.clear_agent_memories(self.name)

    @traceable(name="tool_execution", run_type="tool")
    def _execute_tool(self, tool: Callable, tool_args: dict, tool_name: str) -> Any:
        """Execute a tool with LangSmith tracing."""
        self.logger.info(f"[TRACE] Executing tool: {tool_name} with args: {tool_args}")
        return tool.invoke(tool_args)
    
    def _run_without_llm(self, query: str) -> str:
        return "Agent is running in offline mode. LLM not configured."

    @traceable(name="agent_run", run_type="chain")
    def run(self, query: str) -> str:
        try:
            tools = self.get_tools()
            
            dynamic_tools = self.tool_loader.load_tools()
            tools.extend(dynamic_tools)
            
            if self.tool_builder:
                @tool
                def ask_tool_builder(problem_description: str) -> str:
                    """
                    Use this tool when you cannot solve a problem with your existing tools.
                    It will write and execute a custom Python script to solve it.
                    Describe the problem in detail, including any specific numbers or formulas.
                    """
                    return self.tool_builder.build_and_execute(problem_description)
                
                tools.append(ask_tool_builder)
            
            if not self.llm:
                return self._run_without_llm(query)
            
            self.bind_tools(tools)
            
            # Get memory context (conversation memory)
            memory_context = self._get_memory_context(query)
            
            # Get RAG context (document retrieval)
            rag_context = self._get_rag_context(query)
            
            # Build system prompt with memory and RAG context
            system_prompt = self.get_system_prompt()
            context_parts = []
            if memory_context:
                context_parts.append(memory_context)
            if rag_context:
                context_parts.append(rag_context)
            
            if context_parts:
                system_prompt = f"{system_prompt}\n\n" + "\n\n".join(context_parts)
            
            # Build messages with conversation history
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history,
                {"role": "user", "content": query}
            ]
            
            response = self.llm_with_tools.invoke(messages)
            
            if response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    for t in tools:
                        if t.name == tool_name:
                            try:
                                start_time = time.time()
                                result = self._execute_tool(t, tool_args, tool_name)
                                duration_ms = (time.time() - start_time) * 1000
                                self.logger.info(f"[TRACE] Tool '{tool_name}' completed in {duration_ms:.2f}ms")
                            except Exception as e:
                                result = f"Tool execution failed: {str(e)}"
                                self.logger.error(f"[TRACE] Tool '{tool_name}' failed: {e}")
                                
                            tool_results.append({
                                "tool": tool_name,
                                "args": tool_args,
                                "result": result
                            })
                            
                            # Store significant tool results in memory
                            if self.memory and self.enable_memory:
                                self._store_memory(
                                    f"Query: {query}\nTool: {tool_name}\nResult: {str(result)[:500]}",
                                    metadata={"type": "tool_result", "tool": tool_name}
                                )
                            break
                
                messages.append({"role": "assistant", "content": str(response.tool_calls)})
                messages.append({"role": "user", "content": f"Tool results: {tool_results}\n\nCRITICAL: Do NOT return JSON or tool calls. Synthesize these results into a clear, helpful natural language response for the user."})
                
                final_response = self.llm.invoke(messages)
                response_content = final_response.content
                
                # Check if response_content is a list (some models return blocks)
                if isinstance(response_content, list):
                    # Join text blocks
                    text_parts = []
                    for part in response_content:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                    response_content = "\n".join(text_parts)
                elif not isinstance(response_content, str):
                    # Fallback string conversion
                    response_content = str(response_content)
            else:
                response_content = response.content
                if isinstance(response_content, list):
                     text_parts = []
                     for part in response_content:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                     response_content = "\n".join(text_parts)
                elif not isinstance(response_content, str):
                    response_content = str(response_content)
            
            # Update conversation history
            self._update_conversation_history("user", query)
            self._update_conversation_history("assistant", response_content)
            
            # REFLEXION LOOP (Self-Correction)
            # Only reflect if response is substantial (not just an error or short ack)
            if self.llm and len(response_content) > 50:
                critique_result = self._reflect(query, response_content)
                if critique_result["score"] < 0.8:
                     self.log(f"Reflexion triggered. Score: {critique_result['score']}. Critique: {critique_result['critique']}")
                     
                     # Re-prompt with critique
                     refinement_prompt = f"""
                     Your previous answer was critiqued:
                     "{critique_result['critique']}"
                     
                     Please rewrite your answer to address these issues. Ensure accuracy and completeness.
                     Original Answer:
                     {response_content}
                     """
                     
                     messages.append({"role": "user", "content": refinement_prompt})
                     final_response = self.llm.invoke(messages)
                     response_content = final_response.content
                     
                     # Check format again
                     if isinstance(response_content, list):
                        text_parts = [p if isinstance(p, str) else p.get("text", "") for p in response_content]
                        response_content = "\n".join(text_parts)
                     elif not isinstance(response_content, str):
                        response_content = str(response_content)
                        
                     self._update_conversation_history("assistant", response_content)
            
            return response_content
            
        except Exception as e:
            import traceback
            print(f"CRITICAL ERROR CAUGHT IN BASEAGENT.RUN: {e}")
            traceback.print_exc()
            self.logger.error(f"Error in agent run: {e}")
            return f"I encountered an internal error while processing your request: {str(e)}"

    def _reflect(self, query: str, response: str) -> Dict:
        if not self.llm:
            return {"score": 1.0, "critique": "No LLM to critique."}
            
        prompt = f"""
        You are a Critical Reviewer. Evaluate the following AI response to a user query.
        
        User Query: "{query}"
        AI Response: "{response}"
        
        Check for:
        1. Hallucinations (claims without data).
        2. Failure to answer the specific question.
        3. Vagueness.
        
        Output valid JSON:
        {{
            "score": <float 0.0 to 1.0>,
            "critique": "<short explanation of what is wrong, or 'Looks good' if score > 0.8>"
        }}
        """
        
        try:
            from google.genai import types
            # Use a lightweight model or same model for speed
            critique_resp = self.llm.invoke([{"role": "user", "content": prompt}])
            content = critique_resp.content
            
            # Naive JSON parsing
            import json
            import re
            
            # Find JSON block
            match = re.search(r"\{.*\}", str(content), re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                return {"score": 1.0, "critique": "Could not parse critique."}
        except Exception as e:
            self.logger.warning(f"Reflexion failed: {e}")
            return {"score": 1.0, "critique": "Error during reflection."}

    def log(self, message: str):
        self.logger.info(f"[{self.name}] {message}")
