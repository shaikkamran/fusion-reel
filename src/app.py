from config.loader import load_config
from search_engine import SearchEngine

def main():
    # Load configuration
    config = load_config()
    
    # Initialize search engine
    engine = SearchEngine(config)
    
    # Load indices
    print("Loading indices...")
    engine.load_indices()
    print("Indices loaded!\n")
    
    # Example search
    query = "Indian Romantic movies"
    print(f"Searching for: {query}\n")
    results = engine.search(query)
    
    print("Results:")
    for r in results:
        print(r)

if __name__ == "__main__":
    main()

