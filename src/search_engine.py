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
        self.strategy = config['search_engine']['strategy']
        
        # Initialize components based on strategy
        self.embedder = None
        self.llm_handler = None
        self.parser = None
        self.semantic_indexer = None
        self.bm25_indexer = None
        self.fusion = None
        
        # Initialize embedder (needed for semantic search)
        if self._needs_semantic():
            self.embedder = SentenceTransformer(config['embedding']['model'])
        
        # Initialize LLM handler and parser (needed for LLM-based strategies)
        if self._needs_llm():
            llm_cfg = config['llm']
            self.llm_handler = GeminiHandler(
                api_key=llm_cfg['api_key'],
                model=llm_cfg['model'],
                temperature=llm_cfg['temperature'],
                top_p=llm_cfg['top_p']
            )
            if llm_cfg.get('enable_parser', True):
                self.parser = LLMParser(self.llm_handler)
        
        # Initialize BM25 indexer (needed for BM25 strategies)
        if self._needs_bm25():
            self.bm25_indexer = BM25Indexer()
        
        # Initialize semantic indexer (needed for semantic strategies)
        if self._needs_semantic():
            self.semantic_indexer = SemanticIndexer()
        
        # Initialize fusion (needed for multi-engine strategies)
        if self._needs_fusion():
            fusion_cfg = config['fusion']
            self.fusion = RRFFusion(
                k=fusion_cfg['k'],
                semantic_weight=fusion_cfg.get('semantic_weight', 1.5),
                bm25_weight=fusion_cfg.get('bm25_weight', 1.0)
            )
    
    def _needs_llm(self):
        """Check if strategy requires LLM parsing"""
        return self.strategy in ['llm_bm25', 'llm_semantic', 'llm_bm25_semantic']
    
    def _needs_bm25(self):
        """Check if strategy requires BM25 search"""
        return self.strategy in ['bm25_only', 'llm_bm25', 'llm_bm25_semantic']
    
    def _needs_semantic(self):
        """Check if strategy requires semantic search"""
        return self.strategy in ['semantic_only', 'llm_semantic', 'llm_bm25_semantic']
    
    def _needs_fusion(self):
        """Check if strategy requires fusion"""
        return self.strategy == 'llm_bm25_semantic'
    
    def load_indices(self):
        """Load existing indices based on strategy"""
        idx_cfg = self.config['indexer']
        
        if self._needs_semantic():
            self.semantic_indexer.load(
                idx_cfg['semantic']['index_path'],
                idx_cfg['semantic']['doc_map_path']
            )
        
        if self._needs_bm25():
            self.bm25_indexer.load(idx_cfg['bm25']['index_dir'])
    
    def _parse_query(self, query):
        """Parse query using LLM parser if enabled, otherwise return raw query"""
        if self.parser:
            parsed = self.parser.parse(query)
            return parsed['search_term'], parsed['filters']
        else:
            return query, None
    
    def _search_bm25(self, term, filters):
        """Perform BM25 search"""
        bm25_cfg = self.config['bm25']
        search_cfg = self.config['search']
        
        return self.bm25_indexer.search(
            term,
            filters if bm25_cfg.get('enable_filters', True) else None,
            limit=search_cfg['bm25_limit'],
            enable_fuzzy=bm25_cfg.get('enable_fuzzy', True)
        )
    
    def _search_semantic(self, term, filters):
        """Perform semantic search"""
        search_cfg = self.config['search']
        
        return self.semantic_indexer.search(
            term,
            self.embedder,
            filters,
            k=search_cfg['faiss_k']
        )
    
    def _format_results(self, results, limit=None):
        """Format search results for output"""
        if limit is None:
            limit = self.config['search']['final_limit']
        
        output = []
        for item in results[:limit]:
            if isinstance(item, tuple):
                doc_id, score = item
            else:
                doc_id, score = item, 1.0
            
            # Try to get document from BM25 indexer first (has more fields)
            doc = None
            if self.bm25_indexer:
                doc = self.bm25_indexer.get_document(doc_id)
            
            # Fallback to semantic indexer if BM25 not available
            if not doc and self.semantic_indexer and self.semantic_indexer.doc_map:
                # Search through doc_map to find matching doc_id
                doc_meta = None
                for idx, meta in self.semantic_indexer.doc_map.items():
                    if meta.get('id') == str(doc_id):
                        doc_meta = meta
                        break
                
                if doc_meta:
                    doc = {
                        'title': doc_meta.get('title', 'Unknown'),
                        'year': doc_meta.get('year', 0)
                    }
            
            if doc:
                output.append({
                    "title": doc.get('title', 'Unknown'),
                    "year": doc.get('year', 0),
                    "score": round(score, 3)
                })
        
        return output
    
    def search(self, query):
        """Search and return results with detailed timing"""
        timing = {}
        total_start = time.time()
        
        # Parse query
        parse_start = time.time()
        term, filters = self._parse_query(query)
        timing['parse_time'] = time.time() - parse_start
        
        if self.parser:
            print(f"Parsed: '{term}' | Filters: {filters}")
        else:
            print(f"Query: '{term}'")
        
        # Perform searches based on strategy
        bm25_results = {}
        semantic_results = {}
        
        if self.strategy == 'bm25_only':
            bm25_start = time.time()
            bm25_results = self._search_bm25(term, filters)
            timing['bm25_time'] = time.time() - bm25_start
            results = list(bm25_results.items())
        
        elif self.strategy == 'semantic_only':
            semantic_start = time.time()
            semantic_results = self._search_semantic(term, filters)
            timing['semantic_time'] = time.time() - semantic_start
            results = list(semantic_results.items())
        
        elif self.strategy == 'llm_bm25':
            bm25_start = time.time()
            bm25_results = self._search_bm25(term, filters)
            timing['bm25_time'] = time.time() - bm25_start
            results = list(bm25_results.items())
        
        elif self.strategy == 'llm_semantic':
            semantic_start = time.time()
            semantic_results = self._search_semantic(term, filters)
            timing['semantic_time'] = time.time() - semantic_start
            results = list(semantic_results.items())
        
        elif self.strategy == 'llm_bm25_semantic':
            # Search both indexers
            bm25_start = time.time()
            bm25_results = self._search_bm25(term, filters)
            timing['bm25_time'] = time.time() - bm25_start
            
            semantic_start = time.time()
            semantic_results = self._search_semantic(term, filters)
            timing['semantic_time'] = time.time() - semantic_start
            
            # Fuse results
            fusion_start = time.time()
            fused = self.fusion.fuse(bm25_results, semantic_results)
            timing['fusion_time'] = time.time() - fusion_start
            results = fused
        
        else:
            raise ValueError(f"Unknown search strategy: {self.strategy}")
        
        # Format output
        format_start = time.time()
        output = self._format_results(results)
        timing['format_time'] = time.time() - format_start
        
        timing['total_time'] = time.time() - total_start
        
        # Print timing information
        print("\nTiming Breakdown:")
        for key, value in timing.items():
            print(f"  {key}: {value:.3f}s")
        print()
        
        return output, timing
