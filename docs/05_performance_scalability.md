# Performance & Scalability

## Overview

This document details the performance characteristics and scalability considerations of the film search engine. The system is designed to handle ~9,700 movies with sub-2-second query response times.

## Performance Metrics

### Query Response Times

Typical query response times (measured on standard hardware):

| Search Strategy | Average Time | P95 Time | Components |
|----------------|--------------|----------|------------|
| bm25_only | 50-150ms | 200ms | BM25 search + formatting |
| semantic_only | 200-500ms | 800ms | Embedding + FAISS search + formatting |
| llm_bm25 | 300-700ms | 1000ms | LLM parse + BM25 search + formatting |
| llm_semantic | 500-1200ms | 2000ms | LLM parse + embedding + FAISS search + formatting |
| llm_bm25_semantic | 600-1500ms | 2500ms | LLM parse + BM25 + semantic + fusion + formatting |

**Note**: Times vary based on:
- API latency (for LLM parsing)
- Hardware (CPU, memory)
- Query complexity
- Index size

### Component Timing Breakdown

Typical timing breakdown for `llm_bm25_semantic` strategy:

```
Total Time: ~1000ms
├── Parse Time: 200-500ms (LLM API call)
├── BM25 Time: 10-50ms (Whoosh search)
├── Semantic Time: 50-200ms (embedding + FAISS)
├── Fusion Time: 1-5ms (RRF calculation)
└── Format Time: 1-10ms (result formatting)
```

### Index Load Times

- **BM25 Index**: 100-200ms
- **Semantic Index**: 200-500ms
- **Total Load Time**: 300-700ms (one-time cost at startup)

### Index Build Times

- **BM25 Index**: 10-30 seconds (for ~9,700 movies)
- **Semantic Index**: 5-10 minutes (includes embedding generation)
- **Total Build Time**: ~10 minutes

## Scalability Analysis

### Current Capacity

**Dataset Size**: ~9,700 movies
**Query Throughput**: ~1-2 queries per second (single-threaded)
**Concurrent Users**: Not tested (single-threaded implementation)

### Scalability Bottlenecks

#### 1. LLM API Latency

**Issue**: Each query requires API call to Gemini
- **Impact**: Adds 200-500ms per query
- **Scalability**: Limited by API rate limits
- **Cost**: Per-query API costs

**Mitigation Options**:
- Query caching
- Batch processing
- Alternative LLM providers
- Local LLM models

#### 2. Embedding Generation

**Issue**: Query embedding generation adds latency
- **Impact**: Adds 50-100ms per semantic query
- **Scalability**: CPU-bound, scales with hardware

**Mitigation Options**:
- GPU acceleration
- Embedding caching
- Faster embedding models
- Batch embedding generation

#### 3. Memory Usage

**Issue**: Full indices loaded into memory
- **Current**: ~100-150 MB
- **Scalability**: Linear with dataset size

**Projected Memory**:
- 50,000 movies: ~500-750 MB
- 100,000 movies: ~1-1.5 GB
- 1,000,000 movies: ~10-15 GB

**Mitigation Options**:
- Lazy loading
- Index sharding
- Memory-mapped indices
- Compression

#### 4. Index Size

**Issue**: Semantic index grows linearly with dataset
- **Current**: ~20-30 MB
- **Scalability**: ~3 KB per movie

**Projected Size**:
- 50,000 movies: ~150 MB
- 100,000 movies: ~300 MB
- 1,000,000 movies: ~3 GB

**Mitigation Options**:
- Index compression
- Quantization
- Smaller embedding dimensions
- Hierarchical indices

### Scalability Limits

**Estimated Limits** (without optimization):

| Dataset Size | Feasible | Performance Impact |
|--------------|----------|---------------------|
| ~10,000 movies | ✅ Yes | No impact |
| ~50,000 movies | ✅ Yes | Slight degradation |
| ~100,000 movies | ⚠️ Possible | Noticeable degradation |
| ~1,000,000 movies | ❌ No | Significant degradation |

**With Optimizations**:
- Caching: 2-5x improvement
- GPU acceleration: 5-10x improvement
- Index optimization: 2-3x improvement
- Distributed search: Linear scaling

## Optimization Strategies

### Implemented Optimizations

1. **FAISS Index**: Efficient similarity search
2. **Whoosh Index**: Fast keyword search
3. **L2 Normalization**: Enables cosine similarity via inner product
4. **Result Limiting**: Limits candidates before fusion
5. **Efficient Data Structures**: Optimized data structures for lookups

### Potential Optimizations

#### 1. Query Caching

**Impact**: 2-5x speedup for repeated queries
**Implementation**: Cache parsed queries and results
**Trade-off**: Memory usage vs. speed

#### 2. Embedding Caching

**Impact**: Eliminates embedding generation time
**Implementation**: Cache query embeddings
**Trade-off**: Memory usage vs. speed

#### 3. Pre-filtering for Semantic Search

**Impact**: Reduces FAISS search space
**Implementation**: Apply filters before FAISS search
**Trade-off**: Complexity vs. efficiency

#### 4. Index Sharding

**Impact**: Enables distributed search
**Implementation**: Split index across multiple shards
**Trade-off**: Complexity vs. scalability

#### 5. GPU Acceleration

**Impact**: 5-10x speedup for embeddings
**Implementation**: Use GPU for embedding generation
**Trade-off**: Hardware cost vs. speed

#### 6. Result Caching

**Impact**: Instant results for cached queries
**Implementation**: Cache final results with TTL
**Trade-off**: Memory vs. speed, freshness

## Cost Analysis

### API Costs (Gemini)

- **Model**: gemini-2.0-flash
- **Cost per Query**: ~$0.0001-0.0005 (estimated)
- **Monthly Cost** (1000 queries): ~$0.10-0.50
- **Scalability**: Linear with query volume

### Infrastructure Costs

- **Compute**: Minimal (CPU-only)
- **Storage**: ~30-40 MB (negligible)
- **Memory**: ~100-150 MB (negligible)
- **Total**: Effectively free for small-scale deployment

### Cost Optimization

- **Disable LLM Parsing**: Eliminates API costs (reduces accuracy)
- **Query Caching**: Reduces API calls
- **Local LLM**: One-time setup cost, no per-query costs

## Performance Monitoring

### Metrics to Track

1. **Query Latency**: P50, P95, P99
2. **Component Timing**: Parse, search, fusion times
3. **Error Rate**: Failed queries, API errors
4. **Cache Hit Rate**: If caching implemented
5. **Memory Usage**: Peak memory, average memory
6. **Index Size**: Growth over time

### Current Monitoring

- **Timing Breakdown**: Printed for each query
- **No Persistent Logging**: Metrics not persisted
- **No Alerting**: No alerts on performance degradation

## Benchmarking

### Test Queries

Sample queries for benchmarking:
- "sci-fi movies from the 90s"
- "romantic comedies"
- "war movies about love"
- "funny films from early 2000s"
- "comedy films in the 80s starring Eddie Murphy"

### Benchmark Results

**Hardware**: Standard laptop (CPU-only)
**Dataset**: ~9,700 movies

| Query | Strategy | Time (ms) |
|-------|----------|-----------|
| "sci-fi movies" | llm_bm25_semantic | 800-1200 |
| "romantic comedies" | llm_bm25_semantic | 700-1100 |
| "war movies" | llm_bm25_semantic | 900-1300 |

## Recommendations

### For Current Scale (~10K movies)

✅ **Current performance is adequate**
- Response times meet <2s target
- No immediate optimizations needed

### For Medium Scale (~50K movies)

⚠️ **Consider optimizations**:
1. Implement query caching
2. Enable pre-filtering for semantic search
3. Monitor memory usage
4. Consider GPU for embeddings

### For Large Scale (~100K+ movies)

🔧 **Required optimizations**:
1. Implement index sharding
2. Use GPU acceleration
3. Implement distributed search
4. Add result caching
5. Consider alternative architectures

## Limitations

1. **Single-threaded**: No parallel query processing
2. **No Caching**: Every query hits API/index
3. **Memory-bound**: Full indices in memory
4. **API Dependency**: LLM parsing requires API
5. **No Load Balancing**: Single instance only
6. **No Monitoring**: Limited performance visibility

## Future Improvements

See [Future Roadmap](10_future_roadmap.md) for planned performance improvements.

