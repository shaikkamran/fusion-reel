# Content Search

## Overview

The content search component provides two complementary search methods: BM25 keyword search and semantic search. These can be used independently or combined via fusion for optimal results.

## BM25 Keyword Search

### Implementation

BM25 search is implemented using **Whoosh**, a pure-Python full-text search library. The BM25 indexer (`BM25Indexer`) provides:

- **Multi-field Search**: Searches across title, overview, genres, actors, characters, and director fields
- **Fuzzy Matching**: Supports fuzzy matching on actor, character, and director names
- **Hard Filtering**: Applies filters (year, genre, director, rating) as hard constraints

### Indexed Fields

The BM25 index includes the following fields:

1. **title** (TEXT): Movie title
2. **overview** (TEXT): Movie description/plot
3. **genres** (KEYWORD): Comma-separated genre list
4. **actors** (TEXT): Comma-separated actor names
5. **characters** (TEXT): Character names from the movie
6. **director** (TEXT): Director name
7. **year** (NUMERIC): Release year
8. **rating** (NUMERIC): Movie rating

### Search Process

1. **Query Preprocessing**: 
   - Query is parsed using configured parser (`parser.bm25_strategy`: regex or llm)
   - Filters are extracted (year, genre, rating)
   - Query text is cleaned: stop words removed, filter text removed
   - Cleaned text + filters sent to BM25 indexer
2. **Query Construction**: 
   - Terms are searched across all BM25 fields with OR logic
   - Each term can match in any field
   - Terms are combined with OR for less restrictive matching
3. **Fuzzy Matching** (optional): For actors, characters, and director fields:
   - Terms longer than 2 characters get fuzzy matching
   - Maximum edit distance of 1 character
   - Helps with name misspellings
4. **Filtering**: Hard filters are applied:
   - Year range: NumericRange query
   - Genre: Exact term match (case-insensitive)
   - Director: Exact term match (case-insensitive)
   - Rating: NumericRange query
5. **Scoring**: BM25 relevance scoring based on term frequency and inverse document frequency

### Configuration

BM25 search can be configured via `config.yaml`:

```yaml
bm25:
  enable_fuzzy: true      # Enable fuzzy matching
  enable_filters: false   # Enable hard filtering (currently disabled by default)

search:
  bm25_limit: 20         # Maximum results from BM25 search
```

### Strengths

- **Exact Matches**: Excellent for exact keyword matches
- **Fast**: Very fast search performance
- **Fuzzy Matching**: Handles name misspellings
- **Filtering**: Efficient hard filtering on structured fields

### Limitations

- **Synonym Handling**: Limited synonym understanding (relies on exact term matches)
- **Semantic Understanding**: Cannot understand semantic relationships (e.g., "space movies" vs "sci-fi")
- **Field Matching**: Current implementation uses OR logic between terms, which may be too permissive

## Semantic Search

### Implementation

Semantic search is implemented using **FAISS** (Facebook AI Similarity Search) and **Sentence Transformers**. The semantic indexer (`SemanticIndexer`) provides:

- **Embedding-based Search**: Converts queries and documents to dense vector embeddings
- **Cosine Similarity**: Uses cosine similarity for relevance scoring
- **Post-filtering**: Applies filters after semantic search (less efficient than pre-filtering)

### Embedding Model

The system supports multiple embedding models, configurable via `config.yaml`:

**Default Model**: `all-MiniLM-L6-v2`
- **Model Size**: ~80MB
- **Embedding Dimension**: 384
- **Speed**: Fast inference (~100ms for 9,700 documents)
- **Quality**: Good balance between speed and quality

**Alternative Model**: `nomic-ai/nomic-embed-text-v1`
- **Model Size**: ~547MB
- **Embedding Dimension**: 768
- **Speed**: Slightly slower but higher quality embeddings
- **Quality**: Better semantic understanding

Configuration:
```yaml
embedding:
  model: all-MiniLM-L6-v2  # or nomic-ai/nomic-embed-text-v1
```

### Index Construction

1. **Text Combination**: For each movie, combines multiple fields:
   - Title
   - Overview
   - Genres
   - Director
   - Actors
   - Characters
2. **Embedding Generation**: Converts combined text to embeddings using SentenceTransformer
3. **Index Building**: Creates FAISS IndexFlatIP (Inner Product) index with L2 normalization
4. **Document Mapping**: Maintains mapping from index positions to movie metadata

### Search Process

1. **Query Preprocessing**:
   - Original query text is preserved (no modification)
   - Filters are extracted separately using configured parser (`parser.semantic_strategy`: regex or llm)
   - Full query text + filters sent to semantic indexer
2. **Query Embedding**: Converts full query text to embedding vector
3. **Similarity Search**: Performs k-nearest neighbor search in FAISS index
4. **Post-filtering**: Applies filters (year, genre) to results after search
5. **Scoring**: Returns cosine similarity scores (normalized to [0, 1])

### Configuration

Semantic search can be configured via `config.yaml`:

```yaml
embedding:
  model: all-MiniLM-L6-v2  # or nomic-ai/nomic-embed-text-v1

semantic:
  apply_filters: true      # Enable post-filtering on semantic results

search:
  faiss_k: 100             # Number of candidates to retrieve
```

### Strengths

- **Semantic Understanding**: Understands meaning and context
- **Synonym Handling**: Naturally handles synonyms (e.g., "sci-fi" vs "science fiction")
- **Conceptual Matching**: Can match concepts even without exact keywords
- **Robust**: Handles variations in query phrasing

### Limitations

- **Post-filtering**: Filters applied after search (less efficient)
- **Index Size**: Requires storing embeddings (~1.5MB for 9,700 movies)
- **Model Dependency**: Quality depends on embedding model choice
- **Computational Cost**: Embedding generation adds latency

## Hybrid Search (Fusion)

### Reciprocal Rank Fusion (RRF)

When both BM25 and semantic search are enabled, results are combined using **Reciprocal Rank Fusion**:

1. **Independent Searches**: Both BM25 and semantic search run independently
2. **Rank-based Scoring**: Each result gets a score based on its rank in each search:
   - `score = weight * (1 / (k + rank))`
   - Lower rank (better position) = higher score
3. **Weighted Combination**: Scores are weighted:
   - Semantic weight: 1.5 (default)
   - BM25 weight: 1.0 (default)
4. **Normalization**: Final scores normalized to [0, 1] range
5. **Sorting**: Results sorted by combined score

### RRF Parameters

```yaml
fusion:
  k: 60                    # RRF constant (higher = less rank sensitivity)
  semantic_weight: 1.5     # Weight multiplier for semantic results
  bm25_weight: 1.0         # Weight multiplier for BM25 results
```

### Benefits of Fusion

- **Complementary Strengths**: BM25 excels at exact matches, semantic excels at meaning
- **Better Coverage**: Combines precision of BM25 with recall of semantic search
- **Robust Ranking**: More stable ranking across different query types

### Example

Query: "space movies with aliens"

- **BM25 Results**: Movies with exact keywords "space", "aliens" ranked highly
- **Semantic Results**: Movies about space exploration, extraterrestrial life ranked highly
- **Fused Results**: Combines both, giving preference to movies that appear in both result sets

## Search Strategies

The system supports three search strategies (configured in `config.yaml`):

1. **bm25**: BM25 search only (fast, exact matches)
   - Uses configured parser (`parser.bm25_strategy`) for query preprocessing
   - Returns cleaned text with filters extracted
   
2. **semantic**: Semantic search only (semantic understanding)
   - Uses full original query text
   - Filters extracted separately using `parser.semantic_strategy`
   
3. **fusion**: Hybrid search with RRF fusion (recommended)
   - Combines BM25 and semantic search
   - BM25 uses cleaned text, semantic uses full text
   - Results include source tracking (BM25, Semantic, or Both)
   - Best accuracy by combining both methods

**Parser Configuration**:
```yaml
parser:
  bm25_strategy: regex    # 'regex' or 'llm' - for BM25 preprocessing
  semantic_strategy: regex  # 'regex' or 'llm' - for semantic filter extraction
```

Parser selection is independent of search strategy - you can use regex for BM25 and LLM for semantic, or vice versa.

## Performance Characteristics

### BM25 Search
- **Index Load Time**: ~100-200ms
- **Search Time**: ~10-50ms per query
- **Memory**: ~few MB for index

### Semantic Search
- **Index Load Time**: ~200-500ms
- **Search Time**: ~50-200ms per query (includes embedding generation)
- **Memory**: ~tens of MB for embeddings

### Hybrid Search (Fusion)
- **Total Time**: Sum of BM25 + semantic + fusion time
- **Typical**: 100-400ms total
- **Source Tracking**: Results include source information (BM25, Semantic, or Both)

## Code Locations

- BM25 Indexer: `src/indexer/bm25_indexer.py`
- Semantic Indexer: `src/indexer/semantic_indexer.py`
- Fusion: `src/fusion/rrf_fusion.py`
- Search Engine: `src/search_engine.py`

