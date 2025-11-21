import json
from google import genai

class GeminiHandler:
    def __init__(self, api_key, model="gemini-2.0-flash", temperature=0.0, top_p=0.95):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
    
    def generate(self, prompt, **kwargs):
        """Generate response from Gemini"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
            }
        )
        
        text = response.text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()

