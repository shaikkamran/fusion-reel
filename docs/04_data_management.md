# Data Management

## Overview

The data management system handles processing, indexing, and storage of the movie dataset. It manages ~9,700 movies with rich metadata and creates efficient search indices for fast retrieval.

## Dataset

### Source

The system uses the **Movie Search Ranking Dataset (MSRD)**:
- **Location**: `msrd/dataset/movies.csv`
- **Format**: Tab-separated CSV
- **Size**: ~9,700 movies
- **License**: CC-BY-SA 4.0

### Dataset Schema

The dataset contains the following fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | Integer | Unique movie ID (TMDB ID) | 603 |
| title | String | Movie title | "The Matrix" |
| overview | String | Movie description/plot | "Set in the 22nd century..." |
| tags | String | Comma-separated tags | "sci-fi,virtual reality,dystopia" |
| genres | String | Comma-separated genres | "action,sci-fi,thriller" |
| director | String | Director name | "Lilly Wachowski" |
| actors | String | Comma-separated actor names | "Keanu Reeves,Laurence Fishburne" |
| characters | String | Comma-separated character names | "Thomas A. Anderson / Neo,Morpheus" |
| year | Integer | Release year | 1999 |
| votes | Integer | Number of votes | 22351 |
| rating | Float | Average rating | 8.193 |
| popularity | Float | Popularity score | 60.561 |
| budget | Integer | Production budget | 63000000 |
| poster_url | String | Poster image URL | "https://image.tmdb.org/..." |

### Data Quality

**Handled Issues**:
- Missing values: Filled with empty strings or default values (0 for numeric fields)
- Data types: Strict validation for numeric fields (year, rating)
- Encoding: UTF-8 encoding support

**Known Issues**:
- Some movies may have missing metadata
- Inconsistent formatting in some fields (especially names)
- Some numeric fields may contain invalid values

## Indexing Process

### BM25 Index (Whoosh)

**Purpose**: Fast keyword-based search

**Index Location**: `whoosh_index/` directory (configurable)

**Indexing Steps**:
1. **Schema Definition**: Define fields and their types
2. **Data Validation**: Parse and validate numeric fields (year, rating)
3. **Index Creation**: Create Whoosh index directory
4. **Document Addition**: Add each movie as a document with all fields
5. **Commit**: Write index to disk

**Fields Indexed**:
- `id`: Unique identifier (stored)
- `title`: Full-text searchable
- `overview`: Full-text searchable
- `genres`: Keyword field (comma-separated, lowercase)
- `actors`: Full-text searchable
- `characters`: Full-text searchable
- `year`: Numeric (stored)
- `rating`: Numeric (stored)
- `director`: Full-text searchable

**Index Size**: ~few MB

**Indexing Time**: ~10-30 seconds for ~9,700 movies

### Semantic Index (FAISS)

**Purpose**: Semantic similarity search

**Index Location**: 
- `movies_cosine.index`: FAISS index file
- `id_map.pkl`: Document metadata mapping

**Indexing Steps**:
1. **Text Combination**: Combine multiple fields into single text per movie
2. **Embedding Generation**: Generate embeddings using SentenceTransformer
3. **Index Building**: Create FAISS IndexFlatIP with L2 normalization
4. **Document Mapping**: Create mapping from index positions to movie metadata
5. **Save**: Write index and mapping to disk

**Fields Combined**:
- Title
- Overview
- Genres
- Director
- Actors
- Characters

**Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)

**Index Size**: 
- FAISS index: ~15MB (9,700 × 384 × 4 bytes)
- Document map: ~few MB

**Indexing Time**: ~5-10 minutes (includes embedding generation)

## Data Processing

### Preprocessing

**BM25 Indexer**:
- Fills NaN values with empty strings
- Validates and parses numeric fields (year, rating)
- Handles invalid data gracefully (raises errors during indexing)

**Semantic Indexer**:
- Fills NaN values with empty strings
- Combines multiple fields into formatted text
- Creates structured text: "Title: ...\nOverview: ...\nGenres: ..."

### Data Validation

**Year Validation**:
- Must be integer or convertible to integer
- Raises ValueError on invalid data during indexing
- Defaults to 0 for search filters if invalid

**Rating Validation**:
- Must be float or convertible to float
- Raises ValueError on invalid data during indexing
- Defaults to 0.0 for search filters if invalid

**Text Fields**:
- Converted to strings
- Empty strings for missing values
- UTF-8 encoding preserved

## Index Management

### Loading Indices

Indices are loaded on-demand when the search engine is initialized:

```python
engine.load_indices()
```

**Load Time**:
- BM25: ~100-200ms
- Semantic: ~200-500ms

### Index Persistence

- **BM25**: Stored as Whoosh index directory (persistent)
- **Semantic**: Stored as FAISS binary file + pickle file (persistent)

### Index Updates

**Current Limitation**: Indices must be rebuilt to add/update movies

**Process**:
1. Update source CSV file
2. Rebuild BM25 index
3. Rebuild semantic index
4. Reload indices

**Future Improvement**: Incremental indexing not currently supported

## Storage Requirements

### Disk Space

- **Dataset**: ~few MB (CSV file)
- **BM25 Index**: ~few MB (Whoosh)
- **Semantic Index**: ~20-30 MB (FAISS + embeddings + mapping)
- **Total**: ~30-40 MB

### Memory Usage

- **BM25 Index**: ~few MB (loaded into memory)
- **Semantic Index**: ~20-30 MB (embeddings loaded)
- **Embedding Model**: ~80 MB (SentenceTransformer)
- **Total Runtime**: ~100-150 MB

## Data Access Patterns

### Reading Dataset

- **Format**: Tab-separated CSV
- **Library**: pandas
- **Encoding**: UTF-8

### Accessing Indexed Data

**BM25**:
- Direct document retrieval by ID
- Full document metadata available

**Semantic**:
- Document metadata via doc_map
- Limited fields (id, title, year, genres, rating)
- Full metadata requires lookup in original dataset

## Error Handling

### Indexing Errors

- **Invalid Data**: Raises ValueError with descriptive message
- **Missing Files**: Raises FileNotFoundError
- **Permission Errors**: Raises PermissionError

### Search Errors

- **Missing Index**: Raises error if index not loaded
- **Invalid Query**: Handled gracefully (returns empty results)
- **Filter Errors**: Defaults to safe values (0, empty string)

## Configuration

Index paths and settings configured in `config.yaml`:

```yaml
indexer:
  semantic:
    index_path: movies_cosine.index
    doc_map_path: id_map.pkl
  bm25:
    index_dir: whoosh_index

embedding:
  model: all-MiniLM-L6-v2
```

## Limitations

1. **No Incremental Updates**: Must rebuild entire index for updates
2. **Limited Metadata**: Semantic index stores limited metadata
3. **No Data Versioning**: No versioning of indices or dataset
4. **Single Dataset**: Only supports one dataset at a time
5. **No Backup**: No automatic backup of indices
6. **Memory Usage**: Full indices loaded into memory

## Future Improvements

Potential enhancements:
- Incremental indexing for updates
- Index versioning and rollback
- Compression for semantic index
- Lazy loading of indices
- Multiple dataset support
- Index backup and recovery
- Data validation and cleaning pipeline
- Index statistics and monitoring

