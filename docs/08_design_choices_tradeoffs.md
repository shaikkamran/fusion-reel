# Design Choices & Trade-offs

## Overview

This document explains the key design decisions made in building the film search engine and the trade-offs involved in each choice.

## Core Design Decisions

### 1. Hybrid Search Architecture

**Decision**: Combine BM25 keyword search with semantic search using fusion

**Rationale**:
- BM25 excels at exact keyword matches
- Semantic search excels at understanding meaning and synonyms
- Combining both provides better coverage and accuracy

**Trade-offs**:
- ✅ **Pros**: Best of both worlds, higher accuracy
- ❌ **Cons**: Higher latency, more complex, requires both indices

**Alternative Considered**: Single search method (BM25 or semantic only)
- **Rejected**: Lower accuracy, missing complementary strengths

### 2. LLM-Based Query Parsing

**Decision**: Use LLM (Gemini) to parse natural language queries

**Rationale**:
- Enables natural language understanding
- Handles synonyms, temporal expressions, and complex queries
- No need for complex rule-based parsing

**Trade-offs**:
- ✅ **Pros**: Natural language support, handles edge cases, flexible
- ❌ **Cons**: API dependency, cost per query, latency (~200-500ms)

**Alternatives Considered**:
- **Rule-based parsing**: Rejected - too brittle, doesn't handle variations
- **Local LLM**: Considered but requires more setup and resources

### 3. Reciprocal Rank Fusion (RRF)

**Decision**: Use RRF to combine BM25 and semantic search results

**Rationale**:
- Simple and effective fusion method
- No need for training data
- Works well with different score distributions

**Trade-offs**:
- ✅ **Pros**: Simple, effective, no training needed
- ❌ **Cons**: May not be optimal, doesn't consider score magnitudes

**Alternatives Considered**:
- **Score normalization + weighted sum**: More complex, requires tuning
- **Learning-to-rank**: Requires training data, more complex
- **Chosen**: RRF for simplicity and effectiveness

### 4. Post-filtering for Semantic Search

**Decision**: Apply filters after semantic search (post-filtering)

**Rationale**:
- FAISS doesn't natively support filtering
- Simpler implementation
- Works for current dataset size

**Trade-offs**:
- ✅ **Pros**: Simple implementation, works with FAISS
- ❌ **Cons**: Less efficient (searches more candidates than needed)

**Alternatives Considered**:
- **Pre-filtering**: Would require filtering dataset before indexing
- **Filtered FAISS indices**: More complex, requires multiple indices
- **Chosen**: Post-filtering for simplicity

### 5. Configuration-Driven Strategy Selection

**Decision**: Make search strategy configurable via YAML

**Rationale**:
- Allows testing different strategies without code changes
- Easy to switch between strategies
- Supports different use cases (speed vs. accuracy)

**Trade-offs**:
- ✅ **Pros**: Flexible, testable, no code changes needed
- ❌ **Cons**: More complex initialization logic

**Alternative Considered**: Hard-coded strategy
- **Rejected**: Less flexible, requires code changes to test alternatives

### 6. Sentence Transformers for Embeddings

**Decision**: Use `all-MiniLM-L6-v2` for semantic search

**Rationale**:
- Good balance between speed and quality
- Small model size (~80MB)
- Fast inference (~100ms for 9,700 documents)

**Trade-offs**:
- ✅ **Pros**: Fast, small, good quality
- ❌ **Cons**: Not state-of-the-art quality, English-only

**Alternatives Considered**:
- **Larger models** (e.g., all-mpnet-base-v2): Better quality but slower
- **Multilingual models**: More complex, larger
- **Chosen**: Balance of speed and quality for prototype

### 7. Whoosh for BM25 Search

**Decision**: Use Whoosh library for BM25 indexing

**Rationale**:
- Pure Python (easy to deploy)
- Good performance for dataset size
- Supports fuzzy matching and filtering

**Trade-offs**:
- ✅ **Pros**: Pure Python, good features, easy to use
- ❌ **Cons**: Slower than C-based alternatives (Lucene, Elasticsearch)

**Alternatives Considered**:
- **Elasticsearch**: More powerful but requires separate service
- **Lucene**: Faster but requires Java
- **Chosen**: Whoosh for simplicity and Python compatibility

### 8. FAISS for Semantic Search

**Decision**: Use FAISS for similarity search

**Rationale**:
- Very fast similarity search
- Efficient for dense vectors
- Supports large-scale search

**Trade-offs**:
- ✅ **Pros**: Very fast, efficient, scalable
- ❌ **Cons**: Requires pre-computed embeddings, less flexible than some alternatives

**Alternatives Considered**:
- **Annoy**: Similar performance, different API
- **Elasticsearch with dense vectors**: More complex setup
- **Chosen**: FAISS for performance and ease of use

### 9. CLI-Only Interface

**Decision**: Implement CLI interface only (no web UI)

**Rationale**:
- Faster to implement
- Sufficient for prototype
- Easy to use for technical users

**Trade-offs**:
- ✅ **Pros**: Fast to build, simple, no web dependencies
- ❌ **Cons**: Less accessible to non-technical users

**Alternative Considered**: Web interface
- **Rejected**: More development time, requires web framework

### 10. In-Memory Index Loading

**Decision**: Load full indices into memory

**Rationale**:
- Fastest access
- Simple implementation
- Works for current dataset size

**Trade-offs**:
- ✅ **Pros**: Very fast, simple
- ❌ **Cons**: Memory usage, doesn't scale to very large datasets

**Alternatives Considered**:
- **Memory-mapped indices**: More complex, slower access
- **Lazy loading**: More complex, slower first access
- **Chosen**: In-memory for simplicity and speed

## Component-Specific Decisions

### Query Parser

**Decision**: Single-pass LLM parsing with structured output

**Trade-offs**:
- ✅ **Pros**: Simple, handles complex queries
- ❌ **Cons**: Single attempt, may miss edge cases

**Alternative**: Multi-pass parsing with refinement
- **Rejected**: More complex, higher latency

### BM25 Indexer

**Decision**: OR logic between terms, OR logic between fields

**Trade-offs**:
- ✅ **Pros**: More permissive, higher recall
- ❌ **Cons**: May return less relevant results

**Alternative**: AND logic between terms
- **Rejected**: Too restrictive, lower recall

### Semantic Indexer

**Decision**: Combine multiple fields into single text

**Trade-offs**:
- ✅ **Pros**: Simple, captures all information
- ❌ **Cons**: Doesn't weight fields differently

**Alternative**: Weighted field combination
- **Rejected**: More complex, requires tuning

### Fusion Engine

**Decision**: Weighted RRF with semantic_weight > bm25_weight

**Trade-offs**:
- ✅ **Pros**: Prioritizes semantic results, better for meaning
- ❌ **Cons**: May underweight exact keyword matches

**Alternative**: Equal weights
- **Rejected**: Doesn't leverage semantic search strengths

## Performance vs. Accuracy Trade-offs

### Speed Optimizations

1. **Result Limiting**: Limit candidates before fusion
   - **Trade-off**: Faster but may miss relevant results

2. **Embedding Model**: Use smaller, faster model
   - **Trade-off**: Faster but lower quality

3. **No Caching**: Every query hits API/index
   - **Trade-off**: Simpler but slower for repeated queries

### Accuracy Optimizations

1. **Hybrid Search**: Combine BM25 and semantic
   - **Trade-off**: More accurate but slower

2. **LLM Parsing**: Parse queries with LLM
   - **Trade-off**: Better understanding but API latency

3. **Fuzzy Matching**: Enable fuzzy matching in BM25
   - **Trade-off**: Better recall but more false positives

## Cost vs. Quality Trade-offs

### API Costs

**Decision**: Use Gemini API for query parsing

**Trade-offs**:
- ✅ **Pros**: High quality parsing
- ❌ **Cons**: Per-query costs

**Alternative**: Disable LLM parsing
- **Trade-off**: No costs but lower query understanding

### Infrastructure Costs

**Decision**: CPU-only, no GPU

**Trade-offs**:
- ✅ **Pros**: Lower infrastructure costs
- ❌ **Cons**: Slower embedding generation

**Alternative**: GPU acceleration
- **Trade-off**: Faster but higher costs

## Scalability Trade-offs

### Current Design

**Decision**: Single instance, in-memory indices

**Trade-offs**:
- ✅ **Pros**: Simple, fast for current scale
- ❌ **Cons**: Doesn't scale horizontally

**Alternative**: Distributed architecture
- **Trade-off**: More scalable but more complex

### Index Design

**Decision**: Single index per search method

**Trade-offs**:
- ✅ **Pros**: Simple, fast
- ❌ **Cons**: Must rebuild for updates

**Alternative**: Incremental indexing
- **Trade-off**: More complex but supports updates

## Usability Trade-offs

### Interface Design

**Decision**: CLI-only interface

**Trade-offs**:
- ✅ **Pros**: Fast to build, simple
- ❌ **Cons**: Less accessible

**Alternative**: Web interface
- **Trade-off**: More accessible but more development

### Output Format

**Decision**: Show top 10 results with scores

**Trade-offs**:
- ✅ **Pros**: Simple, clear
- ❌ **Cons**: Limited detail, no pagination

**Alternative**: Rich result display
- **Trade-off**: More informative but more complex

## Maintenance Trade-offs

### Code Complexity

**Decision**: Modular design with clear separation

**Trade-offs**:
- ✅ **Pros**: Easier to maintain, testable
- ❌ **Cons**: More files, more abstraction

**Alternative**: Monolithic design
- **Trade-off**: Simpler structure but harder to maintain

### Configuration

**Decision**: YAML configuration file

**Trade-offs**:
- ✅ **Pros**: Easy to modify, no code changes
- ❌ **Cons**: More configuration to manage

**Alternative**: Hard-coded configuration
- **Trade-off**: Simpler but less flexible

## Lessons Learned

### What Worked Well

1. **Hybrid Search**: Combining BM25 and semantic search provides best results
2. **Configuration-Driven**: Easy to test different strategies
3. **Modular Design**: Easy to understand and modify
4. **LLM Parsing**: Handles natural language well

### What Could Be Improved

1. **Caching**: Would significantly improve performance
2. **Pre-filtering**: More efficient than post-filtering
3. **Error Handling**: Could be more robust
4. **Monitoring**: Need better performance visibility

### Recommendations for Future

1. **Add Caching**: Cache parsed queries and results
2. **Optimize Filtering**: Implement pre-filtering for semantic search
3. **Add Monitoring**: Track performance metrics
4. **Consider GPU**: For larger scale deployments
5. **Web UI**: For better accessibility

## Conclusion

The design choices prioritize:
1. **Accuracy**: Hybrid search with LLM parsing
2. **Simplicity**: CLI interface, straightforward architecture
3. **Flexibility**: Configuration-driven strategy selection
4. **Speed**: Fast enough for prototype (<2s target)

Trade-offs were made to balance these priorities within the time constraints of a prototype implementation.

