# Architecture Overview

## System Architecture

The film search engine follows a modular architecture with clear separation of concerns. The system is designed to be flexible, allowing different search strategies to be configured without code changes.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│  ┌──────────────┐              ┌──────────────┐          │
│  │  Interactive │              │  CLI Single  │          │
│  │     Mode     │              │    Query     │          │
│  └──────┬───────┘              └──────┬───────┘          │
└─────────┼──────────────────────────────┼──────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         │
          ┌──────────────▼──────────────┐
          │     Search Engine            │
          │  (Orchestrator)              │
          └──────────────┬───────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │  Query    │  │   BM25    │  │ Semantic  │
    │  Parser   │  │  Indexer  │  │ Indexer   │
    └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
          │              │              │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │   LLM     │  │  Whoosh   │  │   FAISS   │
    │ Handler   │  │   Index   │  │   Index   │
    └───────────┘  └───────────┘  └───────────┘
                         │              │
                         └──────┬───────┘
                                │
                         ┌──────▼──────┐
                         │   Fusion    │
                         │   Engine    │
                         │    (RRF)    │
                         └─────────────┘
```

## Component Overview

### 1. User Interface Layer

**Components**:
- `app.py`: Interactive CLI application
- `cli.py`: Command-line interface with single query mode

**Responsibilities**:
- User input handling
- Result display formatting
- Error handling and user feedback

### 2. Search Engine (Orchestrator)

**Component**: `search_engine.py`

**Responsibilities**:
- Coordinates all search components
- Implements search strategies
- Manages timing and performance metrics
- Formats and returns results

**Key Methods**:
- `__init__()`: Initialize components based on strategy
- `load_indices()`: Load search indices
- `search()`: Execute search query
- `_parse_query_for_bm25()`: Parse query for BM25 (returns cleaned text + filters)
- `_extract_filters_for_semantic()`: Extract filters for semantic (preserves full query text)
- `_search_bm25()`: Execute BM25 search with cleaned text
- `_search_semantic()`: Execute semantic search with full query text
- `_format_results()`: Format results with source tracking and metadata

### 3. Query Parser

**Components**: 
- `query_parser/regex_parser.py`: Regex-based parsing
- `query_parser/llm_parser.py`: LLM-based parsing

**Responsibilities**:
- Parse natural language queries
- Extract search terms and filters
- Normalize genres and temporal expressions
- Remove stop words (for BM25 preprocessing)

**Parser Selection**:
- **Regex Parser**: Fast, rule-based parsing with stop word removal
- **LLM Parser**: More accurate, uses Gemini API for natural language understanding

**Output Format**:
```json
{
  "search_term": "science fiction movies",  // Cleaned text for BM25
  "filters": {
    "year_min": 1990,
    "year_max": 1999,
    "genre": "sci-fi"
  }
}
```

**Query Processing**:
- **BM25**: Uses cleaned search_term (stop words removed, filters extracted)
- **Semantic**: Uses full original query text, filters extracted separately

### 4. LLM Handler

**Component**: `llm/gemini_handler.py`

**Responsibilities**:
- Interface with Gemini API
- Handle API requests and responses
- Clean response text (remove markdown)

**Configuration**:
- Model selection (gemini-2.0-flash)
- Temperature and top_p parameters

### 5. BM25 Indexer

**Component**: `indexer/bm25_indexer.py`

**Responsibilities**:
- Build Whoosh index from dataset
- Perform keyword-based search
- Apply filters (year, genre, director, rating)
- Support fuzzy matching

**Dependencies**:
- Whoosh library
- Dataset (CSV file)

**Index Structure**:
- Fields: id, title, overview, genres, actors, characters, year, rating, director
- Searchable: title, overview, genres, actors, characters, director
- Filterable: year, rating, genres, director

### 6. Semantic Indexer

**Component**: `indexer/semantic_indexer.py`

**Responsibilities**:
- Build FAISS index from embeddings
- Perform semantic similarity search
- Apply post-filters
- Manage document metadata mapping

**Dependencies**:
- FAISS library
- SentenceTransformers
- Dataset (CSV file)

**Index Structure**:
- Embeddings: 384-dimensional vectors (all-MiniLM-L6-v2) or 768-dimensional (nomic-embed-text-v1)
- Index Type: IndexFlatIP with L2 normalization
- Document Map: Mapping from index positions to movie metadata

**Embedding Models**:
- Default: `all-MiniLM-L6-v2` (384 dimensions, ~80MB)
- Alternative: `nomic-ai/nomic-embed-text-v1` (768 dimensions, ~547MB, higher quality)

### 7. Fusion Engine

**Component**: `fusion/rrf_fusion.py`

**Responsibilities**:
- Combine results from multiple search methods
- Implement Reciprocal Rank Fusion (RRF)
- Weight results from different sources
- Track result sources (BM25, Semantic, or Both)
- Normalize final scores

**Algorithm**:
- RRF with configurable weights
- Rank-based scoring
- Source tracking for each result
- Min-max normalization

**Output Format**:
- Returns tuples: `(doc_id, score, source)`
- Source can be: `'bm25'`, `'semantic'`, or `'both'`

### 8. Configuration Management

**Component**: `config/loader.py`

**Responsibilities**:
- Load YAML configuration
- Merge environment variables
- Set defaults
- Validate configuration

**Configuration Sources**:
- `config.yaml`: Main configuration file
- `.env`: Environment variables (API keys)

## Data Flow

### Query Processing Flow

1. **User Input**: User enters natural language query
2. **Query Preprocessing**:
   - **For BM25**: Parse query using `parser.bm25_strategy` → extract filters → remove stop words → cleaned text
   - **For Semantic**: Extract filters using `parser.semantic_strategy` → preserve full query text
3. **Search Execution**:
   - BM25 search with cleaned text + filters (if enabled)
   - Semantic search with full query text + filters (if enabled)
4. **Result Fusion**: Combine results using RRF with source tracking (if both enabled)
5. **Result Formatting**: Format results with metadata and source information
6. **Output**: Display results using Rich console formatting

### Index Building Flow

1. **Data Loading**: Load dataset from CSV
2. **Preprocessing**: Clean and validate data
3. **Index Building**:
   - BM25: Create Whoosh index
   - Semantic: Generate embeddings and create FAISS index
4. **Index Persistence**: Save indices to disk
5. **Index Loading**: Load indices on startup

## Search Strategies

The system supports three search strategies, configured via `config.yaml`:

### 1. bm25
- **Components**: BM25 Indexer + Parser (regex or llm)
- **Use Case**: Fast keyword search with cleaned text
- **Query Processing**: Cleaned text (stop words removed, filters extracted)
- **Performance**: ~50-150ms

### 2. semantic
- **Components**: Semantic Indexer + Parser (regex or llm)
- **Use Case**: Semantic understanding with full query context
- **Query Processing**: Full original query text preserved
- **Performance**: ~200-500ms

### 3. fusion (Recommended)
- **Components**: BM25 Indexer + Semantic Indexer + Fusion + Parsers
- **Use Case**: Best accuracy, combines both methods
- **Query Processing**: 
  - BM25: Cleaned text + filters
  - Semantic: Full text + filters
- **Source Tracking**: Results include source (BM25, Semantic, or Both)
- **Performance**: ~600-1500ms

## Configuration System

### Configuration File Structure

```yaml
search_engine:
  strategy: fusion  # 'bm25', 'semantic', or 'fusion'

parser:
  bm25_strategy: regex    # 'regex' or 'llm' - for BM25 preprocessing
  semantic_strategy: regex  # 'regex' or 'llm' - for semantic filter extraction

llm:
  enable_parser: true
  provider: gemini
  model: gemini-2.0-flash
  temperature: 0.0
  top_p: 0.95

indexer:
  semantic:
    index_path: movies_cosine.index
    doc_map_path: id_map.pkl
  bm25:
    index_dir: whoosh_index

bm25:
  enable_fuzzy: true
  enable_filters: false

semantic:
  apply_filters: true  # Post-filtering on semantic results

fusion:
  strategy: rrf
  k: 60
  semantic_weight: 1.5
  bm25_weight: 1.0

search:
  bm25_limit: 20
  faiss_k: 100
  final_limit: 50

embedding:
  model: all-MiniLM-L6-v2  # or nomic-ai/nomic-embed-text-v1
```

### Environment Variables

- `GEMINI_API_KEY`: API key for Gemini (loaded from .env)

## Module Dependencies

```
search_engine.py
├── config.loader
├── llm.gemini_handler
├── query_parser.llm_parser
├── indexer.bm25_indexer
├── indexer.semantic_indexer
└── fusion.rrf_fusion

app.py / cli.py
└── search_engine.SearchEngine
```

## Design Patterns

### Strategy Pattern
- Different search strategies implemented as configuration
- Components initialized based on strategy
- No code changes needed to switch strategies

### Factory Pattern
- Configuration loader creates appropriate components
- Components initialized based on configuration

### Facade Pattern
- SearchEngine acts as facade for complex search operations
- Simplifies interface for UI components

## Extensibility

### Adding New Search Methods

1. Create new indexer class
2. Add to SearchEngine initialization
3. Add search method
4. Update strategy configuration

### Adding New Filters

1. Update LLM parser prompt
2. Add filter handling in BM25 indexer
3. Add filter handling in semantic indexer
4. Update configuration schema

### Adding New Fusion Methods

1. Create new fusion class
2. Add to SearchEngine initialization
3. Update configuration options

## Error Handling

- **Configuration Errors**: Validated at startup
- **API Errors**: Caught and handled gracefully
- **Index Errors**: Checked before search
- **Query Errors**: Return empty results, no crash

## Performance Considerations

- **Lazy Loading**: Indices loaded on-demand
- **Result Limiting**: Limits candidates before fusion
- **Efficient Data Structures**: Optimized for lookups
- **Index Persistence**: Indices saved to disk for reuse

## Security Considerations

- **API Keys**: Stored in environment variables, not in code
- **Input Validation**: Queries validated before processing
- **Error Messages**: Don't expose sensitive information

## Testing Considerations

- **Unit Tests**: Individual components testable
- **Integration Tests**: End-to-end search tests
- **Mock Components**: LLM handler can be mocked
- **Test Data**: Can use subset of dataset

## Future Architecture Improvements

See [Future Roadmap](10_future_roadmap.md) for planned architectural enhancements.

