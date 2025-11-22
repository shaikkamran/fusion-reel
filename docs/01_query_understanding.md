# Query Understanding

## Overview

The query understanding component is responsible for parsing natural language queries and extracting structured search parameters. This enables users to express their movie search needs in natural language rather than using structured query syntax.

## Implementation

### LLM-Based Query Parser

The system uses an LLM-based parser (`LLMParser`) that leverages Google's Gemini API to understand natural language queries. The parser extracts:

1. **Search Term**: The main topic, plot, or vibe of the movie
2. **Filters**: Structured constraints including:
   - Year ranges (year_min, year_max)
   - Genres
   - Directors
   - Rating ranges (rating_min, rating_max)

### Query Parsing Process

1. **Input**: Natural language query (e.g., "sci-fi movies from the 90s with Tom Hanks")
2. **LLM Processing**: The query is sent to Gemini with a structured prompt that instructs the model to:
   - Extract the main search term
   - Identify and normalize synonyms (e.g., "sci-fi" → "science fiction")
   - Extract temporal expressions (e.g., "90s" → year_min: 1990, year_max: 1999)
   - Identify celebrity names (actors, directors)
   - Normalize genres to standard genre names
3. **Output**: Structured JSON with search_term and filters dictionary

### Supported Query Patterns

#### Temporal Expressions
- **Decades**: "90s", "80s" → Automatically converted to year ranges (1990-1999, 1980-1989)
- **Year Ranges**: "early 2000s" → 2000-2004, "late 90s" → 1995-1999
- **Single Years**: "2001" → year_min: 2001, year_max: 2001

#### Genre Normalization
The parser normalizes genre mentions to standard genre names:
- "sci-fi" → "science fiction"
- "rom-com" → "romance"
- Genre list includes: action, adventure, animation, children, comedy, crime, documentary, drama, family, fantasy, film-noir, history, horror, imax, music, musical, mystery, romance, sci-fi, science fiction, thriller, tv movie, war, western

#### Celebrity Recognition
- Actor names: Extracted from queries (e.g., "Tom Hanks", "Eddie Murphy")
- Director names: Identified when mentioned (e.g., "movies by Christopher Nolan")
- Character names: Can be extracted but currently not used for filtering

#### Synonym Handling
The LLM parser handles synonyms automatically:
- "sci-fi" → "science fiction"
- "romantic" → "romance"
- "funny" → "comedy"
- "war" → "war" (genre)

### Code Implementation

The query parser is implemented in `src/query_parser/llm_parser.py`:

```python
class LLMParser:
    def parse(self, query):
        # Sends structured prompt to Gemini API
        # Returns JSON with search_term and filters
```

The parser uses a carefully crafted prompt that:
- Instructs the model on extraction rules
- Provides genre normalization guidelines
- Handles edge cases (single years, ranges, etc.)
- Ensures JSON output format

### Integration with Search Engine

The parsed query is used differently for BM25 and semantic search:

1. **For BM25 Search**:
   - **Cleaned Text**: Stop words removed, filters extracted from query text
   - **Filters**: Applied as hard filters in BM25 search
   - Uses cleaned search term for keyword matching

2. **For Semantic Search**:
   - **Full Query Text**: Original query text preserved (no text modification)
   - **Filters**: Extracted separately and applied as post-filters
   - Uses full query context for semantic understanding

### Parser Configuration

The system supports separate parser strategies for BM25 and semantic search:

```yaml
parser:
  bm25_strategy: regex    # 'regex' or 'llm' - for BM25 query parsing
  semantic_strategy: regex  # 'regex' or 'llm' - for semantic filter extraction
```

**Parser Options**:
- **regex**: Fast regex-based parsing with stop word removal
- **llm**: LLM-based parsing using Gemini API (more accurate but slower)

**BM25 Processing**:
- Query is parsed using `bm25_strategy`
- Filters are extracted and removed from query text
- Stop words are removed from remaining text
- Cleaned text + filters sent to BM25 indexer

**Semantic Processing**:
- Original query text is preserved (no modification)
- Filters are extracted separately using `semantic_strategy`
- Full query text + filters sent to semantic indexer

### Regex Parser

The regex parser (`RegexParser`) provides:
- Stop word removal using Whoosh StandardAnalyzer
- Filter extraction (year, genre, rating)
- Text cleaning for BM25 optimization

### LLM Parser

The LLM parser (`LLMParser`) provides:
- Natural language understanding
- Synonym handling
- More accurate filter extraction
- Better handling of complex queries

### Example Queries

| Natural Language Query | Parsed Search Term | Filters |
|------------------------|-------------------|---------|
| "sci-fi movies from the 90s" | "science fiction movies" | year_min: 1990, year_max: 1999 |
| "romantic comedies starring Julia Roberts" | "romantic comedy" | genre: "romance" |
| "war movies about love" | "war movies love" | genre: "war" |
| "funny films from early 2000s" | "funny comedy films" | year_min: 2000, year_max: 2004 |
| "comedy films in the 80s starring Eddie Murphy" | "comedy films" | year_min: 1980, year_max: 1989, genre: "comedy" |

### Limitations

1. **API Dependency**: Requires Gemini API key and internet connection
2. **Cost**: Each query incurs API costs (though minimal with Gemini Flash)
3. **Language**: Currently optimized for English queries
4. **Accuracy**: LLM parsing may occasionally misinterpret complex queries
5. **Actor Filtering**: Actor names are extracted but filtering by actors is not fully implemented in BM25 indexer (fuzzy matching exists but not exact actor filtering)

### Fallback Behavior

If LLM parsing fails or is disabled:
- The raw query is used as the search term
- No filters are applied
- Search still works but with reduced precision

### Performance Considerations

- **Parsing Time**: Typically 200-500ms per query (depends on API latency)
- **Caching**: Not currently implemented (could cache parsed queries)
- **Error Handling**: JSON parsing errors are caught and raw query is used as fallback

