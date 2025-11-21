from config.loader import load_config
from search_engine import SearchEngine

def main():
    """Server-like interface for interactive search"""
    # Load configuration
    config = load_config()
    
    # Initialize search engine
    engine = SearchEngine(config)
    
    # Load indices
    print("Loading indices...")
    engine.load_indices()
    print("Indices loaded!\n")
    
    print("="*80)
    print("Movie Search Engine - Interactive Mode")
    print("="*80)
    print(f"Search Strategy: {config['search_engine']['strategy']}")
    print("Type 'exit' or 'bye' to quit\n")
    
    # Server loop
    while True:
        try:
            # Get user input
            query = input("Enter search query: ").strip()
            
            # Check for exit commands
            if query.lower() in ['exit', 'bye']:
                print("\nGoodbye!")
                break
            
            # Skip empty queries
            if not query:
                continue
            
            # Perform search
            print()
            results, timing = engine.search(query)
            
            # Display results
            if results:
                print("\nTop Results:")
                print("-" * 80)
                for idx, result in enumerate(results[:10], 1):  # Show top 10
                    title = result.get('title', 'Unknown')
                    year = result.get('year', 0)
                    score = result.get('score', 0.0)
                    print(f"{idx}. {title} ({year}) - Score: {score:.3f}")
                if len(results) > 10:
                    print(f"\n... and {len(results) - 10} more results")
            else:
                print("No results found.")
            
            print("\n" + "="*80 + "\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            continue

if __name__ == "__main__":
    main()

