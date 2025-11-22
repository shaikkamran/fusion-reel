class RRFFusion:
    def __init__(self, k=60, semantic_weight=2, bm25_weight=1.0):
        """
        Initialize RRF fusion with configurable weights.
        
        Args:
            k: RRF constant (higher = less rank sensitivity)
            semantic_weight: Weight multiplier for semantic search results (default 1.5 = 50% more weight)
            bm25_weight: Weight multiplier for BM25 search results (default 1.0)
        """
        self.k = k
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
    
    def fuse(self, bm25_results, semantic_results):
        """
        Combine results using Reciprocal Rank Fusion with weighted contributions.
        
        Higher semantic_weight prioritizes semantic search results.
        Returns list of tuples: (doc_id, score, sources) where sources indicates
        which search methods found this result ('bm25', 'semantic', or 'both').
        """
        final_scores = {}
        sources = {}
        all_ids = set(bm25_results.keys()) | set(semantic_results.keys())
        
        bm25_ids = list(bm25_results.keys())
        semantic_ids = list(semantic_results.keys())
        
        # Calculate raw scores and track sources
        for doc_id in all_ids:
            in_bm25 = doc_id in bm25_ids
            in_semantic = doc_id in semantic_ids
            
            # Track source
            if in_bm25 and in_semantic:
                sources[doc_id] = 'both'
            elif in_bm25:
                sources[doc_id] = 'bm25'
            else:
                sources[doc_id] = 'semantic'
            
            rank_bm25 = bm25_ids.index(doc_id) if in_bm25 else 100
            rank_semantic = semantic_ids.index(doc_id) if in_semantic else 100
            
            # Weighted RRF: multiply each component by its weight
            bm25_score = self.bm25_weight * (1 / (self.k + rank_bm25)) if in_bm25 else 0
            semantic_score = self.semantic_weight * (1 / (self.k + rank_semantic)) if in_semantic else 0
            
            score = bm25_score + semantic_score
            final_scores[doc_id] = score
        
        # Normalize scores to [0, 1] range
        if not final_scores:
            return []
        
        max_score = max(final_scores.values())
        min_score = min(final_scores.values())
        
        # Avoid division by zero
        if max_score == min_score:
            # All scores are the same, return normalized to 1.0
            normalized_scores = [
                (doc_id, 1.0, sources.get(doc_id, 'unknown'))
                for doc_id in final_scores.keys()
            ]
        else:
            # Min-max normalization: (score - min) / (max - min)
            normalized_scores = [
                (doc_id, (score - min_score) / (max_score - min_score), sources.get(doc_id, 'unknown'))
                for doc_id, score in final_scores.items()
            ]
        
        return sorted(normalized_scores, key=lambda x: x[1], reverse=True)

