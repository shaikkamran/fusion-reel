from config.loader import load_config
from search_engine import SearchEngine
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def main():
    """Server-like interface for interactive search"""
    # Load configuration
    config = load_config()
    
    # Initialize search engine
    engine = SearchEngine(config)
    
    # Load indices
    console.print("[cyan]Loading indices...[/cyan]")
    engine.load_indices()
    console.print("[green]Indices loaded![/green]\n")
    
    strategy = config['search_engine']['strategy']
    console.print(Panel(
        f"[bold cyan]Movie Search Engine - Interactive Mode[/bold cyan]\n\n"
        f"[bold]Search Strategy:[/bold] {strategy}\n"
        f"[dim]Type 'exit' or 'bye' to quit[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    # Server loop
    while True:
        try:
            # Get user input
            query = input("Enter search query: ").strip()
            
            # Check for exit commands
            if query.lower() in ['exit', 'bye']:
                console.print("\n[bold green]Goodbye![/bold green]")
                break
            
            # Skip empty queries
            if not query:
                continue
            
            # Perform search
            print()
            results, timing = engine.search(query)
            
            # Display results with Rich formatting
            if results:
                # Create results table
                table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                table.add_column("Rank", style="cyan", width=6, justify="right")
                table.add_column("Title", style="yellow", width=40)
                table.add_column("Year", style="blue", width=6, justify="center")
                table.add_column("Score", style="green", width=8, justify="right")
                table.add_column("Source", style="magenta", width=12)
                table.add_column("Genres", style="dim", width=20)
                
                # Add rows to table
                for idx, result in enumerate(results[:10], 1):  # Show top 10
                    title = result.get('title', 'Unknown')
                    if len(title) > 38:
                        title = title[:35] + '...'
                    
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
                
                console.print()
                console.print(Panel(table, title="Top Results", style="bold green", border_style="green"))
                
                # Show detailed metadata for top 5 results
                if len(results) >= 5:
                    console.print()
                    console.print(Panel("Top Results Details", style="bold cyan", border_style="cyan"))
                    
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
                            actors = result.get('actors')
                            if isinstance(actors, str) and len(actors) > 60:
                                actors = actors[:57] + '...'
                            details.append(f"[bold white]Actors:[/bold white] {actors}")
                        
                        if result.get('genres'):
                            details.append(f"[bold green]Genres:[/bold green] {result.get('genres')}")
                        
                        content = "\n".join(details)
                        panel_title = f"[{idx}] {title} ({year})"
                        console.print(Panel(content, title=panel_title, border_style="blue"))
                
                if len(results) > 10:
                    console.print(f"\n[dim]... and {len(results) - 10} more results[/dim]")
            else:
                console.print("[dim]No results found.[/dim]")
            
            console.print()
            console.print(Panel("", border_style="dim"))
            console.print()
        
        except KeyboardInterrupt:
            console.print("\n\n[bold green]Goodbye![/bold green]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")
            continue

if __name__ == "__main__":
    main()

