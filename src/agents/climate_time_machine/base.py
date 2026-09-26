from typing import Optional, Any
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from ..base import BaseAgent as CoreBaseAgent

class ClimateBaseAgent(CoreBaseAgent):
    def __init__(
        self,
        name: str,
        google_api_key: Optional[str] = None,
        memory_manager: Optional[Any] = None,
        enable_memory: bool = True
    ):
        super().__init__(
            name=name,
            google_api_key=google_api_key,
            memory_manager=memory_manager,
            enable_memory=enable_memory
        )
        
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=self.api_key,
                temperature=0.3
            )
            
    def get_tools(self):
        return []
        
    def get_system_prompt(self):
        return "You are an advanced climate simulation agent."
