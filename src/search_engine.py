import time
from sentence_transformers import SentenceTransformer
from config.loader import load_config
from llm.gemini_handler import GeminiHandler
from indexer.semantic_indexer import SemanticIndexer
from indexer.bm25_indexer import BM25Indexer
from query_parser.llm_parser import LLMParser
from fusion.rrf_fusion import RRFFusion

class SearchEngine:
    def __init__(self, config):
        self.config = config
        
        # Initialize embedder
        self.embedder = SentenceTransformer(config['embedding']['model'])
        
        # Initialize LLM handler
        llm_cfg = config['llm']
        self.llm_handler = GeminiHandler(
            api_key=llm_cfg['api_key'],
            model=llm_cfg['model'],
            temperature=llm_cfg['temperature'],
            top_p=llm_cfg['top_p']
        )
        
        # Initialize indexers
        self.semantic_indexer = SemanticIndexer()
        self.bm25_indexer = BM25Indexer()
        
        # Initialize parser
        self.parser = LLMParser(self.llm_handler)
        
        # Initialize fusion
        fusion_cfg = config['fusion']
        self.fusion = RRFFusion(k=fusion_cfg['k'])
    
    def load_indices(self):
        """Load existing indices"""
        idx_cfg = self.config['indexer']
        self.semantic_indexer.load(
            idx_cfg['semantic']['index_path'],
            idx_cfg['semantic']['doc_map_path']
        )
        self.bm25_indexer.load(idx_cfg['bm25']['index_dir'])
    
    def search(self, query):
        """Search and return results"""
        start_time = time.time()
        
        # Parse query
        parsed = self.parser.parse(query)
        term = parsed['search_term']
        filters = parsed['filters']
        
        print(f"Parsed: '{term}' | Filters: {filters}")
        
        # Search both indexers
        search_cfg = self.config['search']
        bm25_results = self.bm25_indexer.search(term, filters, limit=search_cfg['bm25_limit'])
        semantic_results = self.semantic_indexer.search(
            term, self.embedder, filters, k=search_cfg['faiss_k']
        )
        
        # Fuse results
        fused = self.fusion.fuse(bm25_results, semantic_results)
        
        # Format output
        output = []
        for doc_id, score in fused[:search_cfg['final_limit']]:
            doc = self.bm25_indexer.get_document(doc_id)
            if doc:
                output.append({
                    "title": doc['title'],
                    "year": doc['year'],
                    "score": round(score, 3)
                })
        
        print(f"Total search time: {time.time() - start_time:.2f}s\n")
        return output
