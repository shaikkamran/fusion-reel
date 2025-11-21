import json

class LLMParser:
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
    
    def parse(self, query):
        """Parse query using LLM"""
        prompt = f"""
You are a movie search query parser. Extract search parameters from the user query.

Rules:
1. 'search_term': The main topic/plot/vibe. Add 1-2 synonyms.
2. 'filters': Extract constraints (year, genre, rating, director).
3. 'genres': Normalize to standard genres (e.g., 'sci-fi' -> 'science fiction').

User Query: "{query}"

Respond ONLY in JSON format:
{{
    "search_term": "string",
    "filters": {{
        "year_min": int or null,
        "year_max": int or null,
        "genre": "string" or null,
        "rating_min": float or null,
        "director": "string" or null
    }}
}}
"""
        response_text = self.llm_handler.generate(prompt)
        return json.loads(response_text)

