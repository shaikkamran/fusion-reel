import re
import json
from whoosh.analysis import StandardAnalyzer


class RegexParser:

    def __init__(self) -> None:
        pass

    def remove_stop_words(
        self,
        query_text,
        additional_tokens=["movies", "movie", "genre", "director", "cast", "actor",'actors','characters','films','film'],
    ):
        analyzer = StandardAnalyzer()
        tokens = [token.text for token in analyzer(query_text)]
        tokens = [token for token in tokens if token not in additional_tokens]
        return " ".join(tokens)

    def normalise_keywords(self, query_text):
        # query_text = self.remove_stop_words(query_text)
        query_text = query_text.lower()

        query_text = query_text.replace(" ", "_")
        return query_text

    def extract_search_term(
        self,
        query_text,
        tokens=[
            "adventure",
            "animation",
            "children",
            "comedy",
            "crime",
            "documentary",
            "drama",
            "family",
            "fantasy",
            "film-noir",
            "history",
            "horror",
            "imax",
            "music",
            "musical",
            "mystery",
            "romance",
            "sci-fi",
            "science fiction",
            "thriller",
            "tv movie",
            "war",
            "western",
        ],
    ):

        # Write a regex to extract the search term from the query text
        regex = r"(" + "|".join(tokens) + r")"
        match = re.search(regex, query_text)
        if match:
            return match.group(1)
        return None
    
    def extract_year_range(self, query_text):
        """
        Extract year range from query text and remove it from the query.
        Handles formats like: "1999", "2000-2005", "90s", "early 2000s", "late 80s", etc.
        
        Returns:
            tuple: (year_min, year_max, cleaned_query_text)
        """
        year_min = None
        year_max = None
        cleaned_query = query_text
        
        # Pattern 1: Explicit year ranges like "2000-2005", "1995 to 2000"
        range_pattern = r'\b((?:19|20)\d{2})\s*(?:-|to)\s*((?:19|20)\d{2})\b'
        match = re.search(range_pattern, query_text, re.IGNORECASE)
        if match:
            year_min = int(match.group(1))
            year_max = int(match.group(2))
            cleaned_query = re.sub(range_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Pattern 2: Single explicit year like "1999", "2001"
        if year_min is None:
            single_year_pattern = r'\b(19|20)\d{2}\b'
            match = re.search(single_year_pattern, query_text)
            if match:
                year_value = int(match.group(0))
                year_min = year_value
                year_max = year_value
                cleaned_query = re.sub(single_year_pattern, '', cleaned_query).strip()
        
        # Pattern 3: Decade patterns like "90s", "80s", "2000s"
        if year_min is None:
            decade_pattern = r'\b(\d{2})s\b'
            match = re.search(decade_pattern, query_text, re.IGNORECASE)
            if match:
                decade = int(match.group(1))
                if decade >= 20:  # 20s, 30s, ..., 90s -> 1920s, 1930s, ..., 1990s
                    year_min = 1900 + decade
                else:  # 00s, 10s -> 2000s, 2010s
                    year_min = 2000 + decade
                year_max = year_min + 9
                cleaned_query = re.sub(decade_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Pattern 4: Temporal expressions like "early 2000s", "late 90s", "mid 80s"
        if year_min is None:
            temporal_pattern = r'\b(early|late|mid)\s+(\d{2})s\b'
            match = re.search(temporal_pattern, query_text, re.IGNORECASE)
            if match:
                period = match.group(1).lower()
                decade = int(match.group(2))
                if decade >= 20:  # 20s, 30s, ..., 90s -> 1920s, 1930s, ..., 1990s
                    base_year = 1900 + decade
                else:  # 00s, 10s -> 2000s, 2010s
                    base_year = 2000 + decade
                
                if period == 'early':
                    year_min = base_year
                    year_max = base_year + 4
                elif period == 'late':
                    year_min = base_year + 5
                    year_max = base_year + 9
                else:  # mid
                    year_min = base_year + 3
                    year_max = base_year + 6
                
                cleaned_query = re.sub(temporal_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Pattern 5: "early 2000s" with full year
        if year_min is None:
            temporal_full_pattern = r'\b(early|late|mid)\s+((?:19|20)\d{2})s?\b'
            match = re.search(temporal_full_pattern, query_text, re.IGNORECASE)
            if match:
                period = match.group(1).lower()
                year = int(match.group(2))
                decade_start = (year // 10) * 10
                
                if period == 'early':
                    year_min = decade_start
                    year_max = decade_start + 4
                elif period == 'late':
                    year_min = decade_start + 5
                    year_max = decade_start + 9
                else:  # mid
                    year_min = decade_start + 3
                    year_max = decade_start + 6
                
                cleaned_query = re.sub(temporal_full_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Clean up extra spaces
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
        
        return year_min, year_max, cleaned_query
    
    def extract_genre(self, query_text):
        """
        Extract genre from query text and remove it from the query.
        
        Returns:
            tuple: (genre_value, cleaned_query_text)
        """
        genre_value = None
        cleaned_query = query_text
        
        # Genre tokens (normalized versions)
        genre_tokens = [
            "adventure", "animation", "children", "comedy", "crime",
            "documentary", "drama", "family", "fantasy", "film-noir",
            "history", "horror", "imax", "music", "musical",
            "mystery", "romance", "sci-fi", "science fiction",
            "thriller", "tv movie", "war", "western"
        ]
        
        # Genre synonyms mapping
        genre_synonyms = {
            "rom-com": "romance",
            "romcom": "romance",
            "romantic": "romance",
            "sci-fi": "sci-fi",
            "science fiction": "science fiction",
            "scifi": "sci-fi",
            "scifi": "sci-fi",
            "action": "action",
            "comedy": "comedy",
            "drama": "drama",
            "horror": "horror",
            "thriller": "thriller",
            "war": "war",
            "western": "western",
            "fantasy": "fantasy",
            "mystery": "mystery",
            "crime": "crime",
            "adventure": "adventure",
            "animation": "animation",
            "family": "family",
            "musical": "musical",
            "documentary": "documentary"
        }
        
        # Try to match genre tokens (case-insensitive)
        query_lower = query_text.lower()
        for genre in genre_tokens:
            # Match whole words only
            pattern = r'\b' + re.escape(genre.lower()) + r'\b'
            if re.search(pattern, query_lower):
                genre_value = genre
                cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
                break
        
        # Try synonyms if no direct match
        if genre_value is None:
            for synonym, normalized_genre in genre_synonyms.items():
                pattern = r'\b' + re.escape(synonym.lower()) + r'\b'
                if re.search(pattern, query_lower):
                    genre_value = normalized_genre
                    cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
                    break
        
        # Clean up extra spaces
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
        
        return genre_value, cleaned_query
    
    def extract_rating(self, query_text):
        """
        Extract rating from query text and remove it from the query.
        Handles formats like: "rated 8", "above 7.5", "below 6", "8+", ">7", etc.
        
        Returns:
            tuple: (rating_min, rating_max, cleaned_query_text)
        """
        rating_min = None
        rating_max = None
        cleaned_query = query_text
        
        # Pattern 1: "rated 8", "rating 7.5", "score 8.5"
        rated_pattern = r'\b(rated|rating|score)\s+(\d+(?:\.\d+)?)\b'
        match = re.search(rated_pattern, query_text, re.IGNORECASE)
        if match:
            rating_value = float(match.group(2))
            rating_min = rating_value
            rating_max = rating_value
            cleaned_query = re.sub(rated_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Pattern 2: "above 7", "below 6", "over 8", "under 5"
        if rating_min is None:
            comparison_pattern = r'\b(above|below|over|under|more than|less than)\s+(\d+(?:\.\d+)?)\b'
            match = re.search(comparison_pattern, query_text, re.IGNORECASE)
            if match:
                comparison = match.group(1).lower()
                rating_value = float(match.group(2))
                if comparison in ['above', 'over', 'more than']:
                    rating_min = rating_value
                    rating_max = 10.0  # Assuming max rating is 10
                else:  # below, under, less than
                    rating_min = 0.0
                    rating_max = rating_value
                cleaned_query = re.sub(comparison_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Pattern 3: "8+", ">7", "<6", ">=8.5", "<=7.5"
        if rating_min is None:
            operator_pattern = r'\b([<>]=?)\s*(\d+(?:\.\d+)?)\b|(\d+(?:\.\d+)?)\s*\+'
            match = re.search(operator_pattern, query_text)
            if match:
                if match.group(3):  # "8+" format
                    rating_value = float(match.group(3))
                    rating_min = rating_value
                    rating_max = 10.0
                else:  # ">7", "<6", ">=8.5", "<=7.5"
                    operator = match.group(1)
                    rating_value = float(match.group(2))
                    if operator == '>=' or operator == '>':
                        rating_min = rating_value
                        rating_max = 10.0
                    else:  # <= or <
                        rating_min = 0.0
                        rating_max = rating_value
                cleaned_query = re.sub(operator_pattern, '', cleaned_query).strip()
        
        # Pattern 4: "highly rated", "well rated", "top rated"
        if rating_min is None:
            high_rated_pattern = r'\b(highly|well|top|best)\s+rated\b'
            if re.search(high_rated_pattern, query_text, re.IGNORECASE):
                rating_min = 7.0  # Default threshold for "highly rated"
                rating_max = 10.0
                cleaned_query = re.sub(high_rated_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Pattern 5: Rating range like "7-8", "6.5 to 8.5"
        if rating_min is None:
            range_pattern = r'\b(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:rated|rating|score)?\b'
            match = re.search(range_pattern, query_text, re.IGNORECASE)
            if match:
                rating_min = float(match.group(1))
                rating_max = float(match.group(2))
                cleaned_query = re.sub(range_pattern, '', cleaned_query, flags=re.IGNORECASE).strip()
        
        # Clean up extra spaces
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
        
        return rating_min, rating_max, cleaned_query
    
    def parse(self, query_text):
        """
        Parse query text and extract all filters (year, genre, rating) while cleaning the query.
        
        Returns:
            dict: {
                'search_term': cleaned query text,
                'filters': {
                    'year_min': int or None,
                    'year_max': int or None,
                    'genre': str or None,
                    'rating_min': float or None,
                    'rating_max': float or None
                }
            }
        """
        # Extract filters in order: year, genre, rating
        # Each extraction removes the matched text from the query
        year_min, year_max, query_text = self.extract_year_range(query_text)
        genre_value, query_text = self.extract_genre(query_text)
        rating_min, rating_max, query_text = self.extract_rating(query_text)
        
        # Clean up the final search term
        search_term = self.remove_stop_words(query_text)
        
        return {
            'search_term': search_term,
            'filters': {
                'year_min': year_min,
                'year_max': year_max,
                'genre': genre_value,
                'rating_min': rating_min,
                'rating_max': rating_max
            }
        }
    
    


if __name__ == "__main__":
    import json
    
    regex_parser = RegexParser()
    
    # Test cases
    test_queries = [
        "sci-fi movies from 1999",
        "romance movies from the 90s",
        "action movies from early 2000s",
        "comedy films rated 8",
        "drama movies above 7.5",
        "horror films from 1995 to 2000 rated above 8",
        "adventure romance movies",
        "war movies from late 80s with rating 7+",
    ]
    
    print("Testing RegexParser extraction methods:\n")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\nOriginal Query: '{query}'")
        result = regex_parser.parse(query)
        print(f"Parsed Result:")
        print(json.dumps(result, indent=2))
        print("-" * 80)
