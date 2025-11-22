import time
import os
from sentence_transformers import SentenceTransformer
from config.loader import load_config
from llm.gemini_handler import GeminiHandler
from indexer.semantic_indexer import SemanticIndexer
from indexer.bm25_indexer import BM25Indexer
from query_parser.llm_parser import LLMParser
from query_parser.regex_parser import RegexParser
from fusion.rrf_fusion import RRFFusion
from utils.formatters import format_search_results
from rich.console import Console
from rich.panel import Panel

# Disable multiprocessing to avoid hangs on macOS
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

console = Console()

class SearchEngine:
    def __init__(self, config):
        self.config = config
        self.strategy = config['search_engine']['strategy']
        
        # Initialize components based on strategy
        self.embedder = None
        self.llm_handler = None
        self.bm25_parser = None
        self.semantic_parser = None
        self.semantic_indexer = None
        self.bm25_indexer = None
        self.fusion = None
        
        # Initialize embedder (needed for semantic search)
        if self._needs_semantic():
            self.embedder = SentenceTransformer(config['embedding']['model'], trust_remote_code=True)
        
        # Initialize LLM handler (needed for LLM-based parsing if configured)
        parser_cfg = config.get('parser', {})
        if parser_cfg.get('bm25_strategy') == 'llm' or parser_cfg.get('semantic_strategy') == 'llm':
            llm_cfg = config['llm']
            self.llm_handler = GeminiHandler(
                api_key=llm_cfg['api_key'],
                model=llm_cfg['model'],
                temperature=llm_cfg['temperature'],
                top_p=llm_cfg['top_p']
            )
        
        # Initialize BM25 parser based on config
        if self._needs_bm25():
            bm25_strategy = parser_cfg.get('bm25_strategy', 'regex')
            if bm25_strategy == 'llm' and self.llm_handler:
                self.bm25_parser = LLMParser(self.llm_handler)
            else:
                self.bm25_parser = RegexParser()
        
        # Initialize semantic parser for filter extraction
        if self._needs_semantic():
            semantic_strategy = parser_cfg.get('semantic_strategy', 'regex')
            if semantic_strategy == 'llm' and self.llm_handler:
                self.semantic_parser = LLMParser(self.llm_handler)
            else:
                self.semantic_parser = RegexParser()
        
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
    
    def _needs_bm25(self):
        """Check if strategy requires BM25 search"""
        return self.strategy in ['bm25', 'fusion']
    
    def _needs_semantic(self):
        """Check if strategy requires semantic search"""
        return self.strategy in ['semantic', 'fusion']
    
    def _needs_fusion(self):
        """Check if strategy requires fusion"""
        return self.strategy == 'fusion'
    
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
    
    def _parse_query_for_bm25(self, query):
        """
        Parse query for BM25 search using configured parser strategy.
        Returns cleaned text (stop words removed, filters extracted) and filters.
        """
        if not self.bm25_parser:
            # Fallback: return query as-is with no filters
            return query, None
        
        parsed = self.bm25_parser.parse(query)
        # parsed['search_term'] already has stop words removed and filters extracted
        cleaned_text = parsed['search_term']
        filters = parsed.get('filters', None)
        
        return cleaned_text, filters
    
    def _extract_filters_for_semantic(self, query):
        """
        Extract filters for semantic search using configured parser strategy.
        Returns filters dict without modifying query text.
        """
        if not self.semantic_parser:
            return None
        
        parsed = self.semantic_parser.parse(query)
        # Return only filters, query text is not modified for semantic search
        return parsed.get('filters', None)
    
    def _search_bm25(self, cleaned_text, filters):
        """
        Perform BM25 search with cleaned text and filters.
        
        The search query and filters are combined with AND logic:
        - Results must match the search query terms AND all specified filters
        - This ensures filters are hard constraints
        """
        bm25_cfg = self.config['bm25']
        search_cfg = self.config['search']
        
        # Always pass filters to indexer for building/displaying, even if enable_filters is False
        # The indexer will respect enable_filters setting internally if needed
        applied_filters = filters if bm25_cfg.get('enable_filters', True) else None
        
        return self.bm25_indexer.search(
            cleaned_text,
            filters,  # Always pass filters so they can be built and displayed
            limit=search_cfg['bm25_limit'],
            enable_fuzzy=bm25_cfg.get('enable_fuzzy', True),
            require_all_terms=bm25_cfg.get('require_all_terms', False),
            apply_filters=bm25_cfg.get('enable_filters', True)  # Control whether filters are actually applied
        )
    
    def _search_semantic(self, full_query_text, filters):
        """Perform semantic search with full original query text and optional filters"""
        search_cfg = self.config['search']
        semantic_cfg = self.config.get('semantic', {})
        
        # Apply filters only if configured
        applied_filters = filters if semantic_cfg.get('apply_filters', True) else None
        
        return self.semantic_indexer.search(
            full_query_text,
            self.embedder,
            applied_filters,
            k=search_cfg['faiss_k']
        )
    
    def _format_results(self, results, limit=None, source=None):
        """
        Format search results for output with metadata and source information.
        
        Args:
            results: List of tuples (doc_id, score) or (doc_id, score, source)
            limit: Maximum number of results to return
            source: Default source if not provided in results ('bm25', 'semantic', or None)
        """
        if limit is None:
            limit = self.config['search']['final_limit']
        
        output = []
        for item in results[:limit]:
            # Handle different result formats
            if isinstance(item, tuple):
                if len(item) == 3:
                    doc_id, score, result_source = item
                elif len(item) == 2:
                    doc_id, score = item
                    result_source = source
                else:
                    doc_id, score, result_source = item[0], item[1] if len(item) > 1 else 1.0, source
            else:
                doc_id, score, result_source = item, 1.0, source
            
            # Try to get document from BM25 indexer first (has more fields)
            doc = None
            if self.bm25_indexer:
                try:
                    doc = self.bm25_indexer.get_document(doc_id)
                except Exception:
                    pass
            
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
                        'year': doc_meta.get('year', 0),
                        'genres': doc_meta.get('genres', ''),
                        'rating': doc_meta.get('rating', 0.0),
                        'characters': doc_meta.get('characters', ''),
                        'actors': doc_meta.get('actors', ''),
                        'director': doc_meta.get('director', '')
                    }
            
            if doc:
                result_dict = {
                    "title": doc.get('title', 'Unknown'),
                    "year": doc.get('year', 0),
                    "score": round(score, 3)
                }
                
                # Add source information if available
                if result_source:
                    result_dict["source"] = result_source
                
                # Add additional metadata if available
                if 'genres' in doc and doc['genres']:
                    result_dict["genres"] = doc['genres']
                
                if 'rating' in doc and doc['rating']:
                    result_dict["rating"] = round(doc['rating'], 1)
                
                if 'director' in doc and doc['director']:
                    result_dict["director"] = doc['director']
                
                if 'actors' in doc and doc['actors']:
                    # Truncate actors list for table display (full list available in details)
                    actors = doc['actors']
                    if isinstance(actors, str):
                        actor_list = actors.split(',')[:3]
                        result_dict["actors"] = ', '.join(actor_list)
                    else:
                        result_dict["actors"] = actors
                
                if 'characters' in doc and doc['characters']:
                    # Include all characters without truncation
                    result_dict["characters"] = doc['characters']
                
                output.append(result_dict)
        
        return output
    
    def search(self, query):
        """Search and return results with detailed timing"""
        timing = {}
        total_start = time.time()
        
        # Store original query for semantic search
        original_query = query
        
        # Perform searches based on strategy
        bm25_results = {}
        semantic_results = {}
        
        if self.strategy == 'bm25':
            # Parse query for BM25
            parse_start = time.time()
            cleaned_text, bm25_filters = self._parse_query_for_bm25(query)
            timing['parse_time'] = time.time() - parse_start
            
            console.print(Panel(
                f"[bold cyan]BM25 Query (cleaned):[/bold cyan] '{cleaned_text}'\n[bold]Filters:[/bold] {bm25_filters}",
                border_style="cyan"
            ))
            
            bm25_start = time.time()
            bm25_results = self._search_bm25(cleaned_text, bm25_filters)
            timing['bm25_time'] = time.time() - bm25_start
            
            # Format and display results with metadata
            format_search_results(
                bm25_results,
                indexer=self.bm25_indexer,
                result_type="BM25 Results",
                max_display=10
            )
            
            # Convert to list with source information
            results = [(doc_id, score, 'bm25') for doc_id, score in bm25_results.items()]
        
        elif self.strategy == 'semantic':
            # Extract filters for semantic (query text stays full)
            parse_start = time.time()
            semantic_filters = self._extract_filters_for_semantic(query)
            timing['parse_time'] = time.time() - parse_start
            
            console.print(Panel(
                f"[bold yellow]Semantic Query (full):[/bold yellow] '{original_query}'\n[bold]Filters:[/bold] {semantic_filters}",
                border_style="yellow"
            ))
            
            semantic_start = time.time()
            semantic_results = self._search_semantic(original_query, semantic_filters)
            timing['semantic_time'] = time.time() - semantic_start
            
            # Format and display results with metadata
            format_search_results(
                semantic_results,
                indexer=self.semantic_indexer,
                result_type="Semantic Results",
                max_display=10
            )
            
            # Convert to list with source information
            results = [(doc_id, score, 'semantic') for doc_id, score in semantic_results.items()]
        
        elif self.strategy == 'fusion':
            # Parse query for BM25
            parse_start = time.time()
            cleaned_text, bm25_filters = self._parse_query_for_bm25(query)
            
            # Extract filters for semantic (query text stays full)
            semantic_filters = self._extract_filters_for_semantic(query)
            timing['parse_time'] = time.time() - parse_start
            
            console.print(Panel(
                f"[bold cyan]BM25 Query (cleaned):[/bold cyan] '{cleaned_text}'\n[bold]Filters:[/bold] {bm25_filters}",
                border_style="cyan"
            ))
            console.print(Panel(
                f"[bold yellow]Semantic Query (full):[/bold yellow] '{original_query}'\n[bold]Filters:[/bold] {semantic_filters}",
                border_style="yellow"
            ))
            
            # Search both indexers
            bm25_start = time.time()
            bm25_results = self._search_bm25(cleaned_text, bm25_filters)
            timing['bm25_time'] = time.time() - bm25_start
            
            semantic_start = time.time()
            semantic_results = self._search_semantic(original_query, semantic_filters)
            timing['semantic_time'] = time.time() - semantic_start
            
            # Format and display results with metadata
            format_search_results(
                bm25_results,
                indexer=self.bm25_indexer,
                result_type="BM25 Results",
                max_display=10
            )
            format_search_results(
                semantic_results,
                indexer=self.semantic_indexer,
                result_type="Semantic Results",
                max_display=10
            )
            
            # Fuse results
            fusion_start = time.time()
            fused = self.fusion.fuse(bm25_results, semantic_results)
            timing['fusion_time'] = time.time() - fusion_start
            results = fused
        
        else:
            raise ValueError(f"Unknown search strategy: {self.strategy}")
        
        # Format output (fusion results already include source info)
        format_start = time.time()
        output = self._format_results(results, source=self.strategy)
        timing['format_time'] = time.time() - format_start
        
        timing['total_time'] = time.time() - total_start
        
        # Print timing information
        # Timing is now handled by CLI formatter, but keep this for backward compatibility
        from rich.table import Table
        from rich import box
        
        timing_table = Table(show_header=False, box=box.SIMPLE)
        timing_table.add_column("Metric", style="cyan")
        timing_table.add_column("Time", style="green", justify="right")
        
        for key, value in timing.items():
            timing_table.add_row(key.replace('_', ' ').title(), f"{value:.3f}s")
        
        console.print()
        console.print(Panel(timing_table, title="Timing Breakdown", border_style="yellow"))
        console.print()
        
        return output, timing
