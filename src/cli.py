#!/usr/bin/env python3
"""
CLI interface for the search engine.
Supports both single query mode and interactive mode.
"""

import argparse
import json
import sys
from config.loader import load_config
from search_engine import SearchEngine

def format_table(results, timing):
    """Format results as a human-readable table"""
    print("\n" + "="*80)
    print("SEARCH RESULTS")
    print("="*80)
    
    if not results:
        print("No results found.")
        return
    
    # Print header
    print(f"{'Rank':<6} {'Title':<50} {'Year':<8} {'Score':<10}")
    print("-" * 80)
    
    # Print results
    for idx, result in enumerate(results, 1):
        title = result.get('title', 'Unknown')[:47] + '...' if len(result.get('title', '')) > 50 else result.get('title', 'Unknown')
        year = result.get('year', 0)
        score = result.get('score', 0.0)
        print(f"{idx:<6} {title:<50} {year:<8} {score:<10.3f}")
    
    print("="*80)
    
    # Print timing
    print("\nTiming Breakdown:")
    print("-" * 40)
    for key, value in timing.items():
        print(f"  {key.replace('_', ' ').title()}: {value:.3f}s")
    print("-" * 40)
    print(f"  Total Time: {timing.get('total_time', 0):.3f}s")
    print()

def format_json(results, timing):
    """Format results as JSON"""
    output = {
        "results": results,
        "timing": timing,
        "count": len(results)
    }
    print(json.dumps(output, indent=2))

def search_single_query(query, config_path=None, output_format='table'):
    """Perform a single search query"""
    try:
        config = load_config(config_path)
        engine = SearchEngine(config)
        
        print("Loading indices...")
        engine.load_indices()
        print("Indices loaded!\n")
        
        print(f"Search Strategy: {config['search_engine']['strategy']}")
        print(f"Query: {query}\n")
        
        results, timing = engine.search(query)
        
        if output_format == 'json':
            format_json(results, timing)
        else:
            format_table(results, timing)
        
        return results, timing
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Movie Search Engine CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single query with table output
  python -m src.cli search "romantic movies from 2000"
  
  # Single query with JSON output
  python -m src.cli search "action movies" --format json
  
  # Use custom config file
  python -m src.cli search "comedy movies" --config custom_config.yaml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Perform a search query')
    search_parser.add_argument('query', help='Search query string')
    search_parser.add_argument('--config', '-c', help='Path to config file (default: config.yaml)')
    search_parser.add_argument(
        '--format', '-f',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'search':
        search_single_query(args.query, args.config, args.format)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

