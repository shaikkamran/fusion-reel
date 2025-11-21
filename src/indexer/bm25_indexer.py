import os
import shutil
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, NUMERIC, ID
from whoosh.qparser import MultifieldParser
from whoosh import query as wquery
from whoosh.analysis import StandardAnalyzer


class BM25Indexer:
    """BM25 indexer using Whoosh with individual field search and fuzzy matching."""
    
    BM25_FIELDS = ["title", "overview", "genres", "actors", "characters", "director"]
    FUZZY_FIELDS = ["actors", "characters", "director"]
    MIN_FUZZY_TERM_LENGTH = 2
    FUZZY_MAX_DISTANCE = 1
    
    def __init__(self):
        self.whoosh_index = None
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            title=TEXT(stored=True),
            overview=TEXT(stored=True),
            genres=KEYWORD(stored=True, commas=True, lowercase=True),
            actors=TEXT(stored=True),
            characters=TEXT(stored=True),
            year=NUMERIC(stored=True),
            rating=NUMERIC(stored=True),
            director=TEXT(stored=True)
        )
    
    def index(self, dataframe, index_dir):
        """Build Whoosh index from dataframe."""
        if os.path.exists(index_dir):
            shutil.rmtree(index_dir)
        os.mkdir(index_dir)
        
        ix = create_in(index_dir, self.schema)
        writer = ix.writer()
        dataframe = dataframe.fillna('')
        
        for idx, row in dataframe.iterrows():
            # Strict validation for numeric fields - fail fast on bad data
            year = self._parse_int_year(row.get('year', 0))
            rating = self._parse_float_rating(row.get('rating', 0.0))
            
            writer.add_document(
                id=str(row['id']),
                title=str(row.get('title', '')),
                overview=str(row.get('overview', '')),
                genres=str(row.get('genres', '')),
                actors=str(row.get('actors', '')),
                characters=str(row.get('characters', '')),
                year=year,
                rating=rating,
                director=str(row.get('director', ''))
            )
        
        writer.commit()
        self.whoosh_index = ix
    
    def search(self, query_text, filters=None, limit=20, enable_fuzzy=True):
        """
        Search with BM25 on individual fields, optional fuzzy matching, and hard filters.
        
        Args:
            query_text: Search query string
            filters: Dict with filters (year_min, year_max, genre, director, rating_min, rating_max)
            limit: Maximum number of results
            enable_fuzzy: Whether to enable fuzzy matching on actors/characters/director
            
        Returns:
            Dict mapping document IDs to BM25 scores
        """
        cleaned_query = self._clean_query(query_text)
        
        with self.whoosh_index.searcher() as searcher:
            filter_query = self._build_filters(filters)
            search_query = self._build_search_query(cleaned_query, enable_fuzzy)
            
            results = searcher.search(search_query, filter=filter_query, limit=limit)
            return {r['id']: r.score for r in results}
    
    def load(self, index_dir):
        """Load existing index from directory."""
        self.whoosh_index = open_dir(index_dir)
    
    def get_document(self, doc_id):
        """Retrieve document by ID."""
        with self.whoosh_index.searcher() as s:
            return s.document(id=doc_id)
    
    def _clean_query(self, query_text):
        """Tokenize query and remove stop words."""
        analyzer = StandardAnalyzer()
        tokens = [token.text for token in analyzer(query_text)]
        return " ".join(tokens)
    
    def _build_filters(self, filters):
        """Build Whoosh filter query from filters dict."""
        if not filters:
            return wquery.Every()
        
        filter_queries = []
        
        # Year filter
        if filters.get('year_min') is not None:
            year_min = self._safe_int(filters['year_min'])
            year_max = self._safe_int(filters.get('year_max', year_min))
            filter_queries.append(wquery.NumericRange("year", year_min, year_max))
        
        # Genre filter
        if filters.get('genre'):
            genre_value = str(filters['genre']).lower().strip()
            filter_queries.append(wquery.Term("genres", genre_value))
        
        # Director filter
        if filters.get('director'):
            director_value = str(filters['director']).lower().strip()
            filter_queries.append(wquery.Term("director", director_value))
        
        # Rating filter
        if filters.get('rating_min') is not None:
            rating_min = self._safe_float(filters['rating_min'])
            rating_max = self._safe_float(filters.get('rating_max', rating_min))
            filter_queries.append(wquery.NumericRange("rating", rating_min, rating_max))
        
        # Combine filters with AND
        if not filter_queries:
            return wquery.Every()
        
        combined_filter = filter_queries[0]
        for fq in filter_queries[1:]:
            combined_filter = combined_filter & fq
        
        print(f"Final HARD Filter: {combined_filter}")
        
        return combined_filter
    
    def _build_search_query(self, cleaned_query, enable_fuzzy):
        """Build search query combining BM25 and optional fuzzy matching."""
        if not cleaned_query.strip():
            return wquery.Every()

        # BM25 search on multiple fields
        # Use OR logic between fields, AND logic between terms (default MultifieldParser behavior)
        # parser = MultifieldParser(self.BM25_FIELDS, schema=self.whoosh_index.schema)
        # bm25_query = parser.parse(cleaned_query)
        
        # Parse each term separately and combine with OR for less restrictive matching
        terms = cleaned_query.split()
        term_queries = []
        
        for term in terms:
            # For each term, search across all BM25 fields with OR
            field_queries = [wquery.Term(field, term.lower()) for field in self.BM25_FIELDS]
            term_queries.append(wquery.Or(field_queries))
        
        # Combine all term queries with OR (less restrictive - match if ANY term appears)
        if term_queries:
            bm25_query = wquery.Or(term_queries)
        else:
            bm25_query = wquery.Every()

        print(f"\n\nFinal BM25 Query: {bm25_query}")
        
        if not enable_fuzzy:
            return bm25_query
        
        # Add fuzzy matching for actors, characters, director
        fuzzy_queries = self._build_fuzzy_queries(cleaned_query)
        
        if fuzzy_queries:
            return wquery.Or([bm25_query] + fuzzy_queries)
        
        return bm25_query
    
    def _build_fuzzy_queries(self, cleaned_query):
        """Build fuzzy queries for name fields."""
        fuzzy_queries = []
        terms = cleaned_query.split()
        
        for field in self.FUZZY_FIELDS:
            for term in terms:
                if len(term) > self.MIN_FUZZY_TERM_LENGTH:
                    fuzzy_queries.append(
                        wquery.FuzzyTerm(field, term.lower(), maxdist=self.FUZZY_MAX_DISTANCE)
                    )
        
        return fuzzy_queries
    
    @staticmethod
    def _parse_int_year(value):
        """Parse year value with strict validation. Raises ValueError on invalid data."""
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        try:
            str_value = str(value).strip()
            if str_value.isdigit():
                return int(str_value)
            raise ValueError(f"Invalid year value: {value}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid year value: {value}") from e
    
    @staticmethod
    def _parse_float_rating(value):
        """Parse rating value with strict validation. Raises ValueError on invalid data."""
        if isinstance(value, (int, float)):
            return float(value)
        try:
            str_value = str(value).strip()
            # Allow decimal numbers
            if str_value.replace('.', '').isdigit():
                return float(str_value)
            raise ValueError(f"Invalid rating value: {value}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid rating value: {value}") from e
    
    @staticmethod
    def _safe_int(value, default=0):
        """Safely convert value to int. Used for search filters where defaults are acceptable."""
        if isinstance(value, int):
            return value
        try:
            return int(value) if str(value).isdigit() else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_float(value, default=0.0):
        """Safely convert value to float. Used for search filters where defaults are acceptable."""
        if isinstance(value, (int, float)):
            return float(value)
        try:
            str_value = str(value).replace('.', '')
            return float(value) if str_value.isdigit() else default
        except (ValueError, TypeError):
            return default


if __name__ == "__main__":
    import pandas as pd
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.loader import load_config
    
    df = pd.read_csv('../msrd/dataset/movies.csv', sep='\t').fillna('')
    config = load_config()
    
    indexer = BM25Indexer()
    indexer.load(config['indexer']['bm25']['index_dir'])
    
    query_text = "Indian movies from the combination of Shah rukh khan and karan johar"
    filters = {'rating_min': 8, 'rating_max': 10, "genre":"romance"}
    results = indexer.search(query_text, filters=filters, limit=20, enable_fuzzy=False)
    
    print(f"Found {len(results)} results")
    cols_to_display = ["title", "overview", "genres", "year", "rating", "director", "actors", "characters"]
    
    for count, (doc_id, score) in enumerate(results.items()):
        if count >= 5:
            break
        
        doc_id = int(doc_id)
        print(f"\nDoc ID: {doc_id}, Score: {score:.3f}")
        for col in cols_to_display:
            values = df.loc[df['id'] == doc_id, col].values
            print(f"  {col}: {values[0] if len(values) > 0 else 'N/A'}")
        print("-" * 50)
