#!/usr/bin/env python3
"""
CLI interface for the search engine.
Supports both single query mode and interactive mode.
"""

import argparse
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from config.loader import load_config
from search_engine import SearchEngine

console = Console()

def format_table(results, timing):
    """Format results as a human-readable table with metadata using Rich"""
    console.print()
    console.print(Panel("SEARCH RESULTS", style="bold cyan", border_style="cyan"))
    
    if not results:
        console.print("[dim]No results found.[/dim]")
        return
    
    # Create main results table
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Rank", style="cyan", width=6, justify="right")
    table.add_column("Title", style="yellow", width=45)
    table.add_column("Year", style="blue", width=6, justify="center")
    table.add_column("Score", style="green", width=8, justify="right")
    table.add_column("Source", style="magenta", width=12)
    table.add_column("Genres", style="dim", width=20)
    
    # Add rows to table
    for idx, result in enumerate(results, 1):
        title = result.get('title', 'Unknown')
        if len(title) > 43:
            title = title[:40] + '...'
        
        year = result.get('year', 0)
        score = result.get('score', 0.0)
        source = result.get('source', 'unknown')
        
        # Format source display with colors
        if source == 'both':
            source_display = "[bold cyan]BM25[/bold cyan]+[bold yellow]Semantic[/bold yellow]"
        elif source == 'bm25':
            source_display = "[bold cyan]BM25[/bold cyan]"
        elif source == 'semantic':
            source_display = "[bold yellow]Semantic[/bold yellow]"
        else:
            source_display = source or 'N/A'
        
        # Get genres (truncate if too long)
        genres = result.get('genres', '')
        if isinstance(genres, str):
            if len(genres) > 18:
                genres = genres[:15] + '...'
        else:
            genres = str(genres)[:18]
        
        table.add_row(
            str(idx),
            title,
            str(year),
            f"{score:.3f}",
            source_display,
            genres
        )
    
    console.print(table)
    
    # Print detailed metadata for top 5 results
    console.print()
    console.print(Panel("Top Results Details", style="bold green", border_style="green"))
    
    for idx, result in enumerate(results[:5], 1):
        title = result.get('title', 'Unknown')
        year = result.get('year', 0)
        score = result.get('score', 0.0)
        source = result.get('source', 'unknown')
        
        # Format source
        if source == 'both':
            source_display = "[bold cyan]BM25[/bold cyan]+[bold yellow]Semantic[/bold yellow]"
        elif source == 'bm25':
            source_display = "[bold cyan]BM25[/bold cyan]"
        elif source == 'semantic':
            source_display = "[bold yellow]Semantic[/bold yellow]"
        else:
            source_display = source or 'N/A'
        
        details = []
        details.append(f"[bold]Score:[/bold] {score:.3f} | [bold]Source:[/bold] {source_display}")
        
        if result.get('rating'):
            details.append(f"[bold magenta]Rating:[/bold magenta] {result.get('rating')}")
        
        if result.get('director'):
            details.append(f"[bold cyan]Director:[/bold cyan] {result.get('director')}")
        
        if result.get('actors'):
            details.append(f"[bold white]Actors:[/bold white] {result.get('actors')}")
        
        if result.get('genres'):
            details.append(f"[bold green]Genres:[/bold green] {result.get('genres')}")
        
        if result.get('characters'):
            # Show all characters without truncation
            details.append(f"[dim]Characters:[/dim] {result.get('characters')}")
        
        content = "\n".join(details)
        panel_title = f"[{idx}] {title} ({year})"
        console.print(Panel(content, title=panel_title, border_style="blue"))
    
    # Print timing table
    console.print()
    timing_table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE)
    timing_table.add_column("Metric", style="cyan")
    timing_table.add_column("Time", style="green", justify="right")
    
    for key, value in timing.items():
        if key != 'total_time':
            timing_table.add_row(
                key.replace('_', ' ').title(),
                f"{value:.3f}s"
            )
    
    timing_table.add_row("[bold]Total Time[/bold]", f"[bold]{timing.get('total_time', 0):.3f}s[/bold]")
    
    console.print(Panel(timing_table, title="Timing Breakdown", border_style="yellow"))
    console.print()

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
        
        console.print("[cyan]Loading indices...[/cyan]")
        engine.load_indices()
        console.print("[green]Indices loaded![/green]\n")
        
        strategy = config['search_engine']['strategy']
        console.print(Panel(
            f"[bold]Search Strategy:[/bold] {strategy}\n[bold]Query:[/bold] {query}",
            border_style="cyan"
        ))
        console.print()
        
        results, timing = engine.search(query)
        
        if output_format == 'json':
            format_json(results, timing)
        else:
            format_table(results, timing)
        
        return results, timing
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
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

