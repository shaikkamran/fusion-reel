# Film Search Engine - Movie Search Ranking Dataset (MSRD)

A natural language movie search engine prototype that understands complex queries and returns relevant results from a dataset of ~9,700 movies.

## Overview

This search engine bridges the gap between human language and structured movie data, enabling users to find movies using natural language queries like:
- "sci-fi movies from the 90s with Tom Hanks"
- "war movies about love"
- "funny films from the early 2000s"
- "comedy films in the 80s starring Eddie Murphy"

## Features

- **Natural Language Understanding**: LLM-based query parsing to extract search intent and filters
- **Hybrid Search**: Combines BM25 keyword search with semantic search for better relevance
- **Intelligent Filtering**: Supports filtering by year ranges, genres, actors, directors, and ratings
- **Multiple Search Strategies**: Configurable search strategies (BM25, semantic, or fusion)
- **Flexible Parsing**: Separate parser configuration for BM25 and semantic (regex or LLM)
- **Rich Console Output**: Beautiful formatted output with colors, tables, and metadata
- **Source Tracking**: Results show which search method found them (BM25, Semantic, or Both)
- **Fast Performance**: Optimized indexing and search algorithms for sub-2-second response times
- **CLI Interface**: Interactive command-line interface for easy querying

## Architecture

The system consists of several key components:

1. **Query Parser**: Configurable parser (regex or LLM) that extracts search terms and filters
   - **Regex Parser**: Fast rule-based parsing with stop word removal
   - **LLM Parser**: Gemini-based natural language understanding
   - Separate parsers for BM25 (cleaned text) and semantic (full text) processing
2. **BM25 Indexer**: Whoosh-based keyword search index for exact matches and fuzzy matching
3. **Semantic Indexer**: FAISS-based semantic search using sentence transformers
4. **Fusion Engine**: RRF (Reciprocal Rank Fusion) to combine results from multiple search methods
5. **Search Engine**: Orchestrates all components based on configured strategy

## Dataset

The system uses the **Movie Search Ranking Dataset (MSRD)** which contains:
- ~9,700 movies with rich metadata (titles, descriptions, genres, cast, crew, tags, ratings, etc.)
- Tab-separated CSV format with fields: id, title, overview, tags, genres, director, actors, characters, year, votes, rating, popularity, budget, poster_url

## Quick Start

### Prerequisites

- Python 3.8+
- Required packages (see `requirements.txt`)
- Gemini API key (for LLM-based query parsing)

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd fusion-reel/src
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file in the src directory
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

4. Prepare the dataset:
   - The dataset should be located at `../msrd/dataset/movies.csv`
   - Ensure the CSV file is tab-separated

5. Build indices (if not already built):
   - BM25 index: Run the BM25 indexer to create Whoosh indices
   - Semantic index: Run the semantic indexer to create FAISS indices

### Running Queries

#### Interactive Mode (CLI)
```bash
python app.py
```

#### Single Query Mode
```bash
python -m src.cli search "sci-fi movies from the 90s"
```

#### JSON Output
```bash
python -m src.cli search "romantic comedies" --format json
```

## Configuration

The system is configured via `config.yaml`. Key settings include:

- **Search Strategy**: Choose from `bm25`, `semantic`, or `fusion`
- **Parser Configuration**: Separate parser strategies for BM25 and semantic (`regex` or `llm`)
- **LLM Settings**: Configure model, temperature, and API provider
- **Indexer Paths**: Specify paths to BM25 and semantic indices
- **Search Limits**: Configure result limits for BM25, FAISS, and final output
- **Fusion Parameters**: Adjust RRF fusion weights and constants
- **Embedding Model**: Choose embedding model (default: `all-MiniLM-L6-v2`, alternative: `nomic-ai/nomic-embed-text-v1`)

## Search Strategies

1. **bm25**: BM25 keyword search with cleaned text preprocessing
   - Uses configured parser (`parser.bm25_strategy`) for query cleaning
   - Stop words removed, filters extracted
   - Fast and precise for exact matches

2. **semantic**: Semantic search with full query context
   - Uses full original query text (no modification)
   - Filters extracted separately using `parser.semantic_strategy`
   - Better semantic understanding

3. **fusion**: Hybrid search combining BM25 and semantic (recommended)
   - BM25 uses cleaned text, semantic uses full text
   - Results include source tracking (BM25, Semantic, or Both)
   - Best accuracy by combining both methods

## Project Structure

```
fusion-reel/
├── src/
│   ├── app.py                 # Interactive CLI application
│   ├── cli.py                 # Command-line interface
│   ├── search_engine.py       # Main search engine orchestrator
│   ├── config.yaml            # Configuration file
│   ├── requirements.txt       # Python dependencies
│   ├── indexer/               # Search indexers
│   │   ├── bm25_indexer.py    # BM25/Whoosh indexer
│   │   └── semantic_indexer.py # FAISS semantic indexer
│   ├── query_parser/          # Query parsing components
│   │   ├── regex_parser.py    # Regex-based query parser
│   │   └── llm_parser.py      # LLM-based query parser
│   ├── utils/                 # Utility functions
│   │   └── formatters.py     # Rich console formatters
│   ├── llm/                   # LLM handlers
│   │   └── gemini_handler.py  # Gemini API handler
│   ├── fusion/                # Result fusion algorithms
│   │   └── rrf_fusion.py      # Reciprocal Rank Fusion
│   └── config/                # Configuration management
│       └── loader.py          # Config loader
├── msrd/                      # Dataset directory
│   └── dataset/
│       └── movies.csv         # Movie metadata (tab-separated)
└── docs/                      # Documentation files
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Query Understanding](docs/01_query_understanding.md) - How natural language queries are parsed
- [Content Search](docs/02_content_search.md) - BM25 and semantic search implementation
- [Intelligent Filtering](docs/03_intelligent_filtering.md) - Filtering capabilities and logic
- [Data Management](docs/04_data_management.md) - Dataset processing and indexing
- [Performance & Scalability](docs/05_performance_scalability.md) - Performance characteristics and optimizations
- [User Interface](docs/06_user_interface.md) - CLI and interface details
- [Architecture Overview](docs/07_architecture_overview.md) - System architecture and components
- [Design Choices & Trade-offs](docs/08_design_choices_tradeoffs.md) - Design decisions and rationale
- [Drawbacks & Limitations](docs/09_drawbacks_limitations.md) - Known limitations and issues
- [Future Roadmap](docs/10_future_roadmap.md) - Planned improvements and enhancements

## Performance

- **Query Response Time**: Typically < 2 seconds for most queries
- **Index Size**: 
  - BM25 index: ~few MB (Whoosh)
  - Semantic index: ~tens of MB (FAISS + embeddings)
- **Memory Usage**: Moderate (depends on embedding model and index size)
- **Output Formatting**: Rich console formatting with colors, tables, and panels

## Limitations

- LLM parser requires API key (costs apply) - regex parser available as alternative
- Semantic search requires pre-computed embeddings
- Filtering capabilities are limited to predefined fields
- No web UI (CLI only, but with Rich console formatting)
- Limited to English language queries
- Rich formatting requires terminal that supports Rich console (most modern terminals)

See [Drawbacks & Limitations](docs/09_drawbacks_limitations.md) for detailed information.

## License

The dataset is shared under CC-BY-SA 4.0 license. See `msrd/LICENSE.md` for details.

## Contributing

This is a prototype implementation. For production use, consider:
- Adding caching mechanisms
- Implementing query rewriting
- Adding evaluation metrics
- Building a web frontend
- Supporting multiple languages

See [Future Roadmap](docs/10_future_roadmap.md) for planned improvements.

## Contact

For questions or issues, please refer to the documentation files in the `docs/` directory.

