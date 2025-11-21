import json

class LLMParser:
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
    
    def parse(self, query):
        """Parse query using LLM"""
        prompt = f"""
You are a movie search query parser. Extract search parameters from the user query.

Rules:
1. 'search_term': The main topic/plot/vibe. Add 1-2 synonyms remove common irrelevant words.
2. 'filters': Extract constraints (year, genre, rating, director).
3. 'genres': Normalize to standard genres like (action
  adventure
  animation
  children
  comedy
  crime
  documentary
  drama
  family
  fantasy
  film-noir
  history
  horror
  imax
  music
  musical
  mystery
  romance
  sci-fi
  science fiction
  thriller
  tv movie
  war
  western).
If only one year is given then the year_max should be the same as the year_min.
but if its given as a range infer it that way, do the same with rating_min and rating_max
User Query: "{query}"

Respond ONLY in JSON format:
{{
    "search_term": "string",
    "filters": {{
        "year_min": int or null,
        "year_max": int or null,
        "genre": "string" or null,
        "rating_min": float or null,
        "rating_max": float or null,
        "director": "string" or null
    }}
}}
"""
        response_text = self.llm_handler.generate(prompt)
        return json.loads(response_text)

