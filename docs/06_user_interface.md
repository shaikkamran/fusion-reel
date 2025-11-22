# User Interface

## Overview

The film search engine provides a Command Line Interface (CLI) for interacting with the search system. The interface is designed to be intuitive and provide clear feedback to users.

## Command Line Interface (CLI)

### Interactive Mode

**Entry Point**: `python app.py`

**Features**:
- Interactive prompt for entering queries
- Real-time search results display
- Clear formatting with separators
- Exit commands: 'exit' or 'bye'
- Error handling with graceful recovery

**Usage**:
```bash
cd src
python app.py
```

**Example Session**:
```
Loading indices...
Indices loaded!

┌─────────────────────────────────────────────────────────────┐
│ Movie Search Engine - Interactive Mode                      │
│                                                             │
│ Search Strategy: fusion                                     │
│ Type 'exit' or 'bye' to quit                               │
└─────────────────────────────────────────────────────────────┘

Enter search query: sci-fi movies from the 90s

┌─────────────────────────────────────────────────────────────┐
│ BM25 Query (cleaned): 'science fiction movies'             │
│ Filters: {'year_min': 1990, 'year_max': 1999}             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Semantic Query (full): 'sci-fi movies from the 90s'        │
│ Filters: {'year_min': 1990, 'year_max': 1999}              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Top Results                                                 │
└─────────────────────────────────────────────────────────────┘
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Rank ┃ Title                                                ┃ Year ┃ Score  ┃ Source        ┃ Genres                 ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ The Matrix                                           │ 1999 │ 0.987  │ BM25+Semantic │ sci-fi, action         │
│ 2    │ Terminator 2: Judgment Day                           │ 1991 │ 0.945  │ BM25+Semantic │ sci-fi, action         │
│ 3    │ Star Wars: Episode IV - A New Hope                   │ 1977 │ 0.923  │ Semantic      │ sci-fi, adventure       │
...

Enter search query: exit

Goodbye!
```

**Note**: The interface uses Rich console formatting for enhanced readability with colors, tables, and panels.

### Single Query Mode

**Entry Point**: `python -m src.cli search <query>`

**Features**:
- Single query execution
- Table or JSON output format
- Configurable via command-line arguments
- Detailed timing information

**Usage**:
```bash
# Table output (default)
python -m src.cli search "romantic movies from 2000"

# JSON output
python -m src.cli search "action movies" --format json

# Custom config file
python -m src.cli search "comedy movies" --config custom_config.yaml
```

**Table Output Example**:
```
┌─────────────────────────────────────────────────────────────┐
│ SEARCH RESULTS                                              │
└─────────────────────────────────────────────────────────────┘
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Rank ┃ Title                                                ┃ Year ┃ Score  ┃ Source        ┃ Genres                 ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ The Matrix                                           │ 1999 │ 0.987  │ BM25+Semantic │ sci-fi, action         │
│ 2    │ Terminator 2: Judgment Day                           │ 1991 │ 0.945  │ BM25+Semantic │ sci-fi, action         │
│ 3    │ Star Wars: Episode IV - A New Hope                   │ 1977 │ 0.923  │ Semantic      │ sci-fi, adventure       │
...

┌─────────────────────────────────────────────────────────────┐
│ Top Results Details                                         │
└─────────────────────────────────────────────────────────────┘
┌─ [1] The Matrix (1999) ────────────────────────────────────┐
│ Score: 0.987 | Source: BM25+Semantic                        │
│ Rating: 8.7                                                  │
│ Director: The Wachowskis                                     │
│ Actors: Keanu Reeves, Laurence Fishburne                    │
│ Genres: sci-fi, action                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Timing Breakdown                                            │
└─────────────────────────────────────────────────────────────┘
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric              ┃ Time                                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Parse Time           │ 0.342s                               │
│ Bm25 Time            │ 0.023s                               │
│ Semantic Time        │ 0.156s                               │
│ Fusion Time          │ 0.002s                               │
│ Format Time          │ 0.001s                               │
│ Total Time           │ 0.524s                               │
└─────────────────────────────────────────────────────────────┘
```

**Note**: Output uses Rich console formatting with colors, tables, and panels for enhanced readability.

**JSON Output Example**:
```json
{
  "results": [
    {
      "title": "The Matrix",
      "year": 1999,
      "score": 0.987
    },
    {
      "title": "Terminator 2: Judgment Day",
      "year": 1991,
      "score": 0.945
    }
  ],
  "timing": {
    "parse_time": 0.342,
    "bm25_time": 0.023,
    "semantic_time": 0.156,
    "fusion_time": 0.002,
    "format_time": 0.001,
    "total_time": 0.524
  },
  "count": 10
}
```

## Output Format

### Result Display

Each result shows:
- **Rank**: Position in results (1, 2, 3, ...)
- **Title**: Movie title
- **Year**: Release year
- **Score**: Relevance score (0.0 to 1.0)
- **Source**: Which search method found the result (BM25, Semantic, or Both)
- **Genres**: Movie genres

**Top Results Details** (for top 5 results):
- **Score** and **Source**: Relevance score and search method
- **Rating**: Movie rating (if available)
- **Director**: Director name (if available)
- **Actors**: Main actors (if available)
- **Genres**: Full genre list

### Result Limits

- **Top Results Shown**: 10 results in interactive mode
- **Total Results**: Up to 50 results (configurable)
- **Truncation**: Shows "... and X more results" if more than 10

### Timing Information

Detailed timing breakdown for each query:
- **Parse Time**: LLM query parsing time
- **BM25 Time**: Keyword search time
- **Semantic Time**: Semantic search time
- **Fusion Time**: Result fusion time
- **Format Time**: Result formatting time
- **Total Time**: End-to-end query time

## User Experience Features

### Query Feedback

- **Parsed Query Display**: Shows how the query was interpreted
- **Filter Display**: Shows extracted filters (year, genre, etc.)
- **Raw Query Display**: Shows original query if parsing disabled

### Error Handling

- **Empty Queries**: Skipped gracefully
- **API Errors**: Displayed with error message, continues operation
- **Keyboard Interrupt**: Graceful exit (Ctrl+C)
- **Invalid Queries**: Returns empty results, no crash

### Visual Formatting

The interface uses **Rich console** library for enhanced formatting:
- **Color-coded Output**: Different colors for different information types
- **Tables**: Formatted tables with borders and alignment
- **Panels**: Information grouped in styled panels
- **Source Indicators**: Color-coded source labels (BM25=cyan, Semantic=yellow, Both=cyan+yellow)
- **Truncation**: Long titles and text truncated with ellipsis
- **Spacing**: Appropriate spacing for readability

## Command-Line Arguments

### Search Command

```
python -m src.cli search <query> [OPTIONS]

Arguments:
  query                 Search query string

Options:
  --config, -c PATH     Path to config file (default: config.yaml)
  --format, -f FORMAT   Output format: table or json (default: table)
  --help, -h            Show help message
```

### Examples

```bash
# Basic search
python -m src.cli search "sci-fi movies"

# JSON output for scripting
python -m src.cli search "romantic comedies" --format json

# Custom configuration
python -m src.cli search "action movies" --config /path/to/config.yaml
```

## Configuration Display

The interface displays current configuration:
- **Search Strategy**: Shows active search strategy
- **Index Status**: Shows when indices are loaded

## Limitations

### Current Limitations

1. **No Web UI**: CLI only, no web interface
2. **No Query History**: No history of previous queries
3. **No Query Suggestions**: No autocomplete or suggestions
4. **Limited Result Details**: Top 5 results show full details, others show summary
5. **No Pagination**: All results shown at once (up to limit)
6. **No Export**: Cannot export results to file
7. **No Filtering UI**: Filters extracted automatically, no manual filter UI
8. **Rich Formatting**: Requires terminal that supports Rich console (most modern terminals)

### Missing Features

- **Result Details**: Cannot view full movie metadata
- **Sorting Options**: Results sorted by score only
- **Filter Refinement**: Cannot refine filters after search
- **Query Editing**: Cannot edit previous queries
- **Batch Queries**: Cannot process multiple queries at once
- **Result Comparison**: Cannot compare multiple results

## Accessibility

### Text-Based Interface

- **Screen Reader Friendly**: Text-only output
- **Terminal Compatible**: Works in any terminal
- **No Dependencies**: No GUI libraries required

### Usability

- **Clear Prompts**: Obvious input prompts
- **Helpful Messages**: Clear error messages
- **Exit Commands**: Multiple ways to exit ('exit', 'bye', Ctrl+C)

## Future Enhancements

### Potential Web UI Features

If a web interface were to be added:

1. **Search Bar**: Prominent search input
2. **Filter Sidebar**: Manual filter controls
3. **Result Cards**: Rich result display with posters
4. **Pagination**: Navigate through results
5. **Sort Options**: Sort by relevance, year, rating
6. **Result Details**: Expandable result details
7. **Query History**: Recent queries dropdown
8. **Export Options**: Export results to CSV/JSON

### Potential CLI Enhancements

1. **Query History**: Navigate previous queries (up/down arrows)
2. **Result Paging**: Page through results (more/less)
3. **Result Details**: View full metadata for specific result
4. **Query Templates**: Pre-defined query templates
5. **Batch Mode**: Process queries from file
6. **Export Mode**: Export results to file
7. **Interactive Filters**: Refine filters after search

## Code Locations

- **Interactive CLI**: `src/app.py`
- **Command-Line CLI**: `src/cli.py`
- **Result Formatting**: `src/cli.py` (format_table, format_json functions)

## Usage Tips

1. **Use Natural Language**: Write queries as you would ask a person
2. **Be Specific**: More specific queries yield better results
3. **Check Parsed Query**: Verify the system understood your query correctly
4. **Review Timing**: Use timing info to understand performance
5. **Use JSON Format**: For scripting or integration with other tools

