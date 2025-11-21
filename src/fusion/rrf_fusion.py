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
        Returns scores normalized to [0, 1] range.
        """
        final_scores = {}
        all_ids = set(bm25_results.keys()) | set(semantic_results.keys())
        
        bm25_ids = list(bm25_results.keys())
        semantic_ids = list(semantic_results.keys())
        
        # Calculate raw scores
        for doc_id in all_ids:
            rank_bm25 = bm25_ids.index(doc_id) if doc_id in bm25_ids else 100
            rank_semantic = semantic_ids.index(doc_id) if doc_id in semantic_ids else 100
            
            # Weighted RRF: multiply each component by its weight
            bm25_score = self.bm25_weight * (1 / (self.k + rank_bm25))
            semantic_score = self.semantic_weight * (1 / (self.k + rank_semantic))
            
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
            normalized_scores = [(doc_id, 1.0) for doc_id in final_scores.keys()]
        else:
            # Min-max normalization: (score - min) / (max - min)
            normalized_scores = [
                (doc_id, (score - min_score) / (max_score - min_score))
                for doc_id, score in final_scores.items()
            ]
        
        return sorted(normalized_scores, key=lambda x: x[1], reverse=True)

