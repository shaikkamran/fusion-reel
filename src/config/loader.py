import os
import yaml
from dotenv import load_dotenv

load_dotenv()

def load_config(config_path=None):
    """Load YAML config and merge with environment variables"""
    if config_path is None:
        # Default to config.yaml in src directory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set defaults for search_engine section
    if 'search_engine' not in config:
        config['search_engine'] = {}
    config['search_engine'].setdefault('strategy', 'llm_bm25_semantic')
    
    # Validate search_engine strategy
    valid_strategies = ['bm25_only', 'semantic_only', 'llm_bm25', 'llm_semantic', 'llm_bm25_semantic']
    if config['search_engine']['strategy'] not in valid_strategies:
        raise ValueError(f"Invalid search_engine.strategy: {config['search_engine']['strategy']}. "
                        f"Must be one of: {valid_strategies}")
    
    # Set defaults for bm25 section
    if 'bm25' not in config:
        config['bm25'] = {}
    config['bm25'].setdefault('enable_fuzzy', True)
    config['bm25'].setdefault('enable_filters', True)
    
    # Set defaults for llm section
    if 'llm' not in config:
        config['llm'] = {}
    config['llm'].setdefault('enable_parser', True)
    
    # Merge API keys from .env
    if 'llm' in config:
        provider = config['llm'].get('provider', 'gemini')
        if provider == 'gemini':
            config['llm']['api_key'] = os.getenv("GEMINI_API_KEY")
        elif provider == 'openai':
            config['llm']['api_key'] = os.getenv("OPENAI_API_KEY")
        elif provider == 'ollama':
            config['llm']['api_key'] = None  # Ollama doesn't need API key
    
    # Set defaults for fusion section
    if 'fusion' not in config:
        config['fusion'] = {}
    config['fusion'].setdefault('strategy', 'rrf')
    config['fusion'].setdefault('k', 60)
    config['fusion'].setdefault('semantic_weight', 1.5)
    config['fusion'].setdefault('bm25_weight', 1.0)
    
    # Set defaults for search section
    if 'search' not in config:
        config['search'] = {}
    config['search'].setdefault('bm25_limit', 20)
    config['search'].setdefault('faiss_k', 100)
    config['search'].setdefault('final_limit', 50)
    
    return config

