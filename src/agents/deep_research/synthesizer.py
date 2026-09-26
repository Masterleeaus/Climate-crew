from ..base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class SynthesizerAgent(BaseAgent):
    def __init__(self, google_api_key: str = None):
        super().__init__("SynthesizerAgent", google_api_key)

    def get_system_prompt(self) -> str:
        return """You are a Research Synthesizer.
Your goal is to write a comprehensive, high-quality research report based on verified findings.
The report must:
- Be structured (Executive Summary, Detailed Analysis, Key Data, Conclusion).
- Use inline citations [1], [2] referring to the provided sources.
- Be objective and fact-based.
- Highlight any remaining uncertainties.

Format the output in clean Markdown.
Appended to the end, list the References with their full URLs.
Format: [1] Title - URL
"""

    def get_tools(self):
        return []

    def synthesize(self, topic: str, accepted_data: list) -> str:
        data_str = ""
        for i, item in enumerate(accepted_data):
             # item is likely a dict or Node object, convert to str representation
             content = str(item)
             data_str += f"Valid Source [{i+1}]: {content}\n\n"

        prompt = f"""Write a deep research report on: {topic}

Using these verified sources:
{data_str}
"""
        return self.run(prompt)
