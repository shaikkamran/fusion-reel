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
    
    # Merge API keys from .env
    if 'llm' in config:
        provider = config['llm']['provider']
        if provider == 'gemini':
            config['llm']['api_key'] = os.getenv("GEMINI_API_KEY")
        elif provider == 'openai':
            config['llm']['api_key'] = os.getenv("OPENAI_API_KEY")
        elif provider == 'ollama':
            config['llm']['api_key'] = None  # Ollama doesn't need API key
    
    return config

