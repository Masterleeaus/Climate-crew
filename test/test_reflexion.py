
import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch, ANY

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.base import BaseAgent
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
load_dotenv()

class TestReflexionReal(unittest.TestCase):
    
    def setUp(self):
        self.agent = BaseAgent("TestAgent", google_api_key=os.getenv("GOOGLE_API_KEY"))
        # Ensure LLM is 'present' even if key is dummy
        self.agent.llm = MagicMock()

    def test_reflexion_retry_flow(self):
        """
        Verify the full flow:
        1. Agent generates weak response.
        2. _reflect is called -> Critic generates critique.
        3. Agent is re-prompted with critique.
        4. Agent generates refined response.
        """
        
        # We mock the invoke method to return a sequence of responses
        # 1. Initial response (weak)
        # 2. Critic response (critique JSON)
        # 3. Refined response (strong)
        
        initial_weak_response = "The weather is okay. " + ("x" * 60) # Ensure > 50 chars
        critique_json = json.dumps({"score": 0.4, "critique": "Too vague. Specify temperature."})
        refined_response = "The temperature is 25C and sunny."
        
        self.agent.llm.invoke.side_effect = [
            AIMessage(content=initial_weak_response), # Run 1
            AIMessage(content=critique_json),         # Reflection
            AIMessage(content=refined_response)       # Run 2 (Refinement)
        ]
        
        # Execute run
        final_answer = self.agent.run("What is the weather?")
        
        # ASSERTIONS
        
        # 1. Verify Final Answer is the refined one
        self.assertEqual(final_answer, refined_response)
        
        # 2. Verify Call Count: 
        # Call 1: "What is the weather?"
        # Call 2: Critic prompt
        # Call 3: "Your answer was critiqued..."
        self.assertEqual(self.agent.llm.invoke.call_count, 3)
        
        # 3. Verify the Prompt content for Refinement (Call 3)
        # The 3rd call shoud contain the critique
        refinement_call_args = self.agent.llm.invoke.call_args_list[2]
        messages_sent = refinement_call_args[0][0] # First arg is messages list
        last_message = messages_sent[-1].content
        
        self.assertIn("Your previous answer was critiqued", last_message)
        self.assertIn("Too vague", last_message)
        self.assertIn("Original Answer", last_message)

    def test_json_parsing_resilience(self):        
        # Case 1: JSON wrapped in markdown
        malformed_json = "Here is the critique: ```json\n{\"score\": 0.5, \"critique\": \"Bad.\"}\n```"
        self.agent.llm.invoke.return_value = AIMessage(content=malformed_json)
        
        result = self.agent._reflect("query", "response")
        self.assertEqual(result["score"], 0.5)
        self.assertEqual(result["critique"], "Bad.")
        
        # Case 2: Totally garbage output -> Should default to Score 1.0 (Pass) to avoid crashing
        garbage_json = "I cannot critique this."
        self.agent.llm.invoke.return_value = AIMessage(content=garbage_json)
        
        result = self.agent._reflect("query", "response")
        self.assertEqual(result["score"], 1.0) # Falback success equivalent

if __name__ == "__main__":
    unittest.main()
