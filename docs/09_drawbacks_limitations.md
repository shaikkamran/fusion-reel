# Drawbacks & Limitations

## Overview

This document details the known limitations, drawbacks, and areas for improvement in the current film search engine implementation. These limitations are acknowledged and documented to set proper expectations and guide future development.

## Critical Limitations

### 1. API Dependency for Query Parsing

**Issue**: LLM-based query parsing requires an external API (Gemini)

**Impact**:
- Requires internet connection
- Incurs per-query costs
- Subject to API rate limits
- Adds latency (~200-500ms per query)

**Workaround**: Can disable LLM parsing, but reduces query understanding

**Severity**: Medium (can be mitigated by disabling LLM parsing)

### 2. Post-filtering for Semantic Search

**Issue**: Filters are applied after semantic search, not before

**Impact**:
- Less efficient (searches more candidates than needed)
- Performance degrades as filter selectivity decreases
- Wastes computation on filtered-out results

**Workaround**: None currently

**Severity**: Medium (acceptable for current dataset size)

### 3. No Incremental Index Updates

**Issue**: Indices must be completely rebuilt to add/update movies

**Impact**:
- Cannot add new movies without rebuilding entire index
- Time-consuming process (~10 minutes for full rebuild)
- No real-time updates

**Workaround**: Rebuild indices when dataset changes

**Severity**: Medium (acceptable for static datasets)

### 4. Limited Actor Filtering

**Issue**: Actor names are extracted but not used as hard filters

**Impact**:
- Actor filtering relies on text matching, not structured filtering
- May match character names or other mentions
- Less precise than dedicated actor filtering

**Workaround**: None currently

**Severity**: Low-Medium (fuzzy matching helps but not ideal)

## Functional Limitations

### 5. Single Genre Filtering

**Issue**: Only one genre can be filtered at a time

**Impact**:
- Cannot search for "action AND comedy" movies
- Cannot use OR logic for genres
- Less flexible filtering

**Workaround**: None currently

**Severity**: Low (most queries use single genre)

### 6. No Query Caching

**Issue**: Every query hits the API and indices, even for repeated queries

**Impact**:
- Wasted API calls for repeated queries
- Slower response for cached queries
- Higher costs

**Workaround**: None currently

**Severity**: Low (can be added easily)

### 7. Limited Result Metadata

**Issue**: Results only show title, year, and score

**Impact**:
- Cannot see full movie details without additional lookup
- No genre, director, actors shown in results
- Limited context for decision-making

**Workaround**: Look up full details in original dataset

**Severity**: Low (can be enhanced)

### 8. No Web Interface

**Issue**: CLI-only interface

**Impact**:
- Less accessible to non-technical users
- No visual result display
- No interactive filtering

**Workaround**: None currently

**Severity**: Low (acceptable for prototype)

## Performance Limitations

### 9. Single-threaded Execution

**Issue**: Queries processed sequentially, no parallelization

**Impact**:
- Cannot handle multiple queries concurrently
- No benefit from multi-core CPUs
- Limited throughput

**Workaround**: None currently

**Severity**: Low (acceptable for prototype scale)

### 10. Full Index Loading

**Issue**: Entire indices loaded into memory

**Impact**:
- High memory usage (~100-150 MB)
- Doesn't scale to very large datasets
- Slower startup time

**Workaround**: None currently

**Severity**: Low (acceptable for current dataset size)

### 11. No Result Pagination

**Issue**: All results shown at once (up to limit)

**Impact**:
- May show too many results
- No way to navigate through large result sets
- Limited to 50 results maximum

**Workaround**: Adjust final_limit in config

**Severity**: Low (acceptable for most use cases)

## Data Quality Limitations

### 12. Missing Data Handling

**Issue**: Movies with missing metadata are excluded from filtered results

**Impact**:
- May miss relevant movies due to missing data
- Inconsistent behavior depending on data completeness
- No graceful degradation

**Workaround**: None currently

**Severity**: Low (depends on dataset quality)

### 13. No Data Validation Pipeline

**Issue**: Limited validation of input data

**Impact**:
- Invalid data may cause errors
- Inconsistent data formats not handled
- No data quality metrics

**Workaround**: Manual data cleaning

**Severity**: Low (acceptable for controlled dataset)

## Usability Limitations

### 14. No Query History

**Issue**: Cannot access previous queries

**Impact**:
- Cannot easily repeat searches
- No learning from past queries
- Less convenient for iterative exploration

**Workaround**: None currently

**Severity**: Low (minor inconvenience)

### 15. No Query Suggestions

**Issue**: No autocomplete or query suggestions

**Impact**:
- Users must type full queries
- No guidance on query formulation
- May lead to poor queries

**Workaround**: None currently

**Severity**: Low (acceptable for prototype)

### 16. Limited Error Messages

**Issue**: Error messages may not be user-friendly

**Impact**:
- Users may not understand what went wrong
- Technical errors exposed to users
- Less helpful debugging

**Workaround**: None currently

**Severity**: Low (acceptable for technical users)

## Scalability Limitations

### 17. No Horizontal Scaling

**Issue**: Single instance only, no distributed architecture

**Impact**:
- Cannot scale to handle high load
- Single point of failure
- Limited throughput

**Workaround**: None currently

**Severity**: Low (acceptable for prototype)

### 18. Linear Memory Growth

**Issue**: Memory usage grows linearly with dataset size

**Impact**:
- May not scale to very large datasets (>1M movies)
- Requires more memory as dataset grows
- May hit memory limits

**Workaround**: Index sharding, compression

**Severity**: Low (acceptable for current scale)

### 19. No Index Sharding

**Issue**: Single index for entire dataset

**Impact**:
- Cannot distribute search across multiple machines
- Limited scalability
- Single point of failure

**Workaround**: None currently

**Severity**: Low (acceptable for current scale)

## Accuracy Limitations

### 20. LLM Parsing Accuracy

**Issue**: LLM may occasionally misinterpret queries

**Impact**:
- Incorrect filters extracted
- Wrong search terms
- Poor results

**Workaround**: Review parsed query, adjust query phrasing

**Severity**: Low (generally accurate, edge cases exist)

### 21. Synonym Handling

**Issue**: Relies on LLM and embedding model for synonyms

**Impact**:
- May miss some synonym relationships
- Not all synonyms handled correctly
- Depends on model quality

**Workaround**: Use more explicit queries

**Severity**: Low (generally works well)

### 22. Fuzzy Matching Limitations

**Issue**: Fuzzy matching only on actors, characters, director fields

**Impact**:
- May miss matches due to typos in other fields
- Limited fuzzy matching coverage
- May produce false positives

**Workaround**: None currently

**Severity**: Low (acceptable for most cases)

## Cost Limitations

### 23. API Costs

**Issue**: Per-query API costs for LLM parsing

**Impact**:
- Costs scale with query volume
- May be expensive at scale
- Requires API key management

**Workaround**: Disable LLM parsing, use local LLM

**Severity**: Low (minimal costs for prototype)

### 24. No Cost Optimization

**Issue**: No caching or cost-saving measures

**Impact**:
- Every query incurs full costs
- No optimization for repeated queries
- Higher costs than necessary

**Workaround**: None currently

**Severity**: Low (acceptable for prototype)

## Security Limitations

### 25. API Key Management

**Issue**: API keys stored in environment variables

**Impact**:
- Requires careful key management
- May be exposed if not handled properly
- No key rotation mechanism

**Workaround**: Use secure environment variable management

**Severity**: Low (standard practice, but could be improved)

### 26. No Input Sanitization

**Issue**: Limited input validation and sanitization

**Impact**:
- May be vulnerable to injection attacks
- No protection against malicious input
- Potential security issues

**Workaround**: None currently

**Severity**: Low (CLI interface reduces risk)

## Monitoring Limitations

### 27. No Performance Monitoring

**Issue**: No persistent performance metrics

**Impact**:
- Cannot track performance over time
- No alerts on degradation
- Limited visibility into system health

**Workaround**: Manual timing inspection

**Severity**: Low (acceptable for prototype)

### 28. No Error Logging

**Issue**: Errors not logged persistently

**Impact**:
- Cannot debug issues after the fact
- No error tracking
- Limited observability

**Workaround**: None currently

**Severity**: Low (acceptable for prototype)

## Language Limitations

### 29. English-Only

**Issue**: Optimized for English queries only

**Impact**:
- Doesn't work well for other languages
- Embedding model is English-focused
- LLM parsing optimized for English

**Workaround**: None currently

**Severity**: Low (acceptable for English-speaking users)

## Summary

### High Priority Limitations
- None (all limitations are acceptable for prototype)

### Medium Priority Limitations
1. API dependency for query parsing
2. Post-filtering for semantic search
3. No incremental index updates
4. Limited actor filtering

### Low Priority Limitations
- All other limitations listed above

## Mitigation Strategies

### Short-term
1. Add query caching to reduce API calls
2. Implement pre-filtering for semantic search
3. Add more result metadata to output
4. Improve error messages

### Long-term
1. Support incremental index updates
2. Implement proper actor filtering
3. Add web interface
4. Support multiple languages
5. Add monitoring and logging
6. Implement horizontal scaling

## Conclusion

While the system has several limitations, they are mostly acceptable for a prototype implementation. The most significant limitations are:
- API dependency (can be mitigated)
- Post-filtering inefficiency (acceptable for current scale)
- No incremental updates (acceptable for static datasets)

Future improvements should prioritize:
1. Performance optimizations (caching, pre-filtering)
2. Usability enhancements (web UI, better results)
3. Scalability improvements (incremental updates, sharding)

