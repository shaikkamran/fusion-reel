# Intelligent Filtering

## Overview

The intelligent filtering system allows users to specify constraints on movie metadata through natural language queries. These filters are extracted by the LLM parser and applied during search to narrow down results.

## Supported Filters

### Year Range Filtering

**Extraction**: Temporal expressions in queries are automatically converted to year ranges.

**Examples**:
- "90s" → `year_min: 1990, year_max: 1999`
- "early 2000s" → `year_min: 2000, year_max: 2004`
- "late 80s" → `year_min: 1985, year_max: 1989`
- "2001" → `year_min: 2001, year_max: 2001`
- "1995 to 2000" → `year_min: 1995, year_max: 2000`

**Implementation**:
- In BM25: Applied as `NumericRange` filter (hard constraint)
- In Semantic: Applied as post-filter after search

### Genre Filtering

**Extraction**: Genre mentions are normalized to standard genre names.

**Supported Genres**:
action, adventure, animation, children, comedy, crime, documentary, drama, family, fantasy, film-noir, history, horror, imax, music, musical, mystery, romance, sci-fi, science fiction, thriller, tv movie, war, western

**Examples**:
- "sci-fi movies" → `genre: "sci-fi"`
- "romantic comedies" → `genre: "romance"`
- "action films" → `genre: "action"`

**Implementation**:
- In BM25: Applied as exact `Term` filter on genres field (case-insensitive)
- In Semantic: Applied as post-filter checking if genre string contains the filter value

**Limitations**:
- Only single genre filtering supported (not multiple genres)
- Genre normalization depends on LLM accuracy

### Director Filtering

**Extraction**: Director names are extracted from queries when mentioned.

**Examples**:
- "movies by Christopher Nolan" → `director: "Christopher Nolan"`
- "Steven Spielberg films" → `director: "Steven Spielberg"`

**Implementation**:
- In BM25: Applied as exact `Term` filter on director field (case-insensitive)
- In Semantic: Not currently implemented as post-filter

**Limitations**:
- Requires exact name match (case-insensitive)
- Fuzzy matching not applied to director filter
- May miss variations in name formatting

### Rating Filtering

**Extraction**: Rating constraints can be extracted from queries (though less common in natural language).

**Examples**:
- "highly rated movies" → Could extract `rating_min: 7.0` (not currently implemented)
- "movies rated above 8" → `rating_min: 8.0, rating_max: 10.0`

**Implementation**:
- In BM25: Applied as `NumericRange` filter on rating field
- In Semantic: Not currently implemented as post-filter

**Limitations**:
- Rating filtering is less commonly used in natural language queries
- Requires explicit mention of ratings in query

### Actor Filtering

**Status**: **Partially Implemented**

**Extraction**: Actor names are extracted from queries.

**Examples**:
- "movies with Tom Hanks" → Actor name extracted but filtering not fully implemented
- "starring Eddie Murphy" → Actor name extracted

**Current Implementation**:
- Actor names are extracted by LLM parser
- Fuzzy matching exists in BM25 search on actors field
- Exact actor filtering not implemented as hard filter

**Limitations**:
- No dedicated actor filter field in BM25 schema
- Relies on text matching in actors field
- May match character names or other mentions

## Filter Application Logic

### BM25 Filtering

Filters are applied as **hard constraints** using Whoosh query filters:

1. **Year Filter**: `NumericRange("year", year_min, year_max)`
2. **Genre Filter**: `Term("genres", genre_value)`
3. **Director Filter**: `Term("director", director_value)`
4. **Rating Filter**: `NumericRange("rating", rating_min, rating_max)`

All filters are combined with **AND** logic - all conditions must be satisfied.

**Configuration**:
```yaml
bm25:
  enable_filters: false  # Currently disabled by default
```

**Note**: Filters are implemented but disabled by default in the current configuration.

### Semantic Search Filtering

Filters are applied as **post-filters** after semantic search:

1. Results are retrieved from FAISS index
2. Each result is checked against filters
3. Results not matching filters are removed
4. Remaining results are returned

**Limitations**:
- Less efficient than pre-filtering (searches more candidates than needed)
- Only year and genre filters are currently implemented
- Director and rating filters not implemented

## Filter Combination

### Multiple Filters

When multiple filters are extracted from a query, they are combined with **AND** logic:

**Example Query**: "comedy films in the 80s starring Eddie Murphy"

**Extracted Filters**:
- `genre: "comedy"`
- `year_min: 1980, year_max: 1989`
- Actor: "Eddie Murphy" (extracted but not used as hard filter)

**Result**: Movies that are:
- Comedy genre AND
- Released between 1980-1989 AND
- (Actor matching handled via text search, not hard filter)

### Filter Priority

Filters are applied in the following order:
1. Year range (if specified)
2. Genre (if specified)
3. Director (if specified)
4. Rating (if specified)
5. Actor (via text matching, not hard filter)

## Edge Cases and Handling

### Missing Data

- **Missing Year**: Movies without year are excluded from year-filtered results
- **Missing Genre**: Movies without genre are excluded from genre-filtered results
- **Missing Director**: Movies without director are excluded from director-filtered results
- **Missing Rating**: Movies without rating are excluded from rating-filtered results

### Invalid Filter Values

- **Invalid Years**: Non-numeric years are handled gracefully (defaults to 0)
- **Invalid Ratings**: Non-numeric ratings are handled gracefully (defaults to 0.0)
- **Unknown Genres**: Genre filters use exact matching, so unknown genres won't match

### Filter Conflicts

- **Conflicting Filters**: If filters are too restrictive, may return zero results
- **No Results**: System returns empty result set (no fallback to less restrictive filters)

## Configuration

Filtering behavior can be controlled via `config.yaml`:

```yaml
bm25:
  enable_filters: false  # Enable/disable BM25 hard filtering

search:
  bm25_limit: 20         # Results before filtering
  faiss_k: 100          # Candidates for semantic post-filtering
```

## Performance Impact

### BM25 Filtering (Hard Filters)

- **Efficiency**: Very efficient - filters applied during index search
- **Performance**: Minimal overhead (~1-5ms)
- **Scalability**: Scales well with index size

### Semantic Post-filtering

- **Efficiency**: Less efficient - searches more candidates than needed
- **Performance**: Overhead depends on number of candidates (k parameter)
- **Scalability**: Performance degrades as k increases

## Limitations

1. **Single Genre**: Only one genre filter supported at a time
2. **Actor Filtering**: Not fully implemented as hard filter
3. **Post-filtering**: Semantic search uses post-filtering (less efficient)
4. **Filter Accuracy**: Depends on LLM parser accuracy
5. **No Soft Filters**: All filters are hard constraints (no partial matching)
6. **Limited Filter Types**: Only year, genre, director, rating supported

## Future Improvements

Potential enhancements:
- Multiple genre filtering (AND/OR logic)
- Actor filtering as hard constraint
- Pre-filtering for semantic search
- Soft filters with scoring
- More filter types (budget, popularity, votes)
- Filter suggestions based on query

