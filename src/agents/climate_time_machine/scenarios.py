import json
from google import genai
from google.genai import types

class ScenarioGenerator:
    def __init__(self, client):
        self.client = client
        self.model = "gemini-2.5-flash-lite"

    def generate(self, event):
        prompt = f"""
        Analyze the climate event: "{event}".
        Generate 3 distinct future scenarios:
        1. Best Case (Effective Mitigation)
        2. Worst Case (Cascading Failure)
        3. Most Likely Case (Current Trajectory)
        
        For each scenario, provide:
        - title: Short descriptive title.
        - analysis: Detailed scientific explanation of the chain of events.
        - image_prompts: A list of 5 sequential image prompts that visualize this scenario evolving over 5 years. Each prompt must be photorealistic and detailed.
        
        Return a valid JSON list of objects.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
