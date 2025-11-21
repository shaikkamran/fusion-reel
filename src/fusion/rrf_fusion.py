class RRFFusion:
    def __init__(self, k=60):
        self.k = k
    
    def fuse(self, bm25_results, semantic_results):
        """Combine results using Reciprocal Rank Fusion"""
        final_scores = {}
        all_ids = set(bm25_results.keys()) | set(semantic_results.keys())
        
        bm25_ids = list(bm25_results.keys())
        semantic_ids = list(semantic_results.keys())
        
        for doc_id in all_ids:
            rank_bm25 = bm25_ids.index(doc_id) if doc_id in bm25_ids else 100
            rank_semantic = semantic_ids.index(doc_id) if doc_id in semantic_ids else 100
            
            score = (1 / (self.k + rank_bm25)) + (1 / (self.k + rank_semantic))
            final_scores[doc_id] = score
        
        return sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

