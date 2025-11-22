"""Formatter functions for displaying search results with metadata."""

from typing import Dict, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_search_results(
    results: Dict[str, float],
    indexer: Optional[Any] = None,
    result_type: str = "Results",
    max_display: int = 10
) -> None:
    """
    Format and print search results with full metadata.
    
    Args:
        results: Dictionary mapping document IDs to scores
        indexer: BM25Indexer or SemanticIndexer instance to retrieve document metadata
        result_type: Label for the result type (e.g., "BM25 Results", "Semantic Results")
        max_display: Maximum number of results to display
    """
    if not results:
        console.print(f"\n[dim]{result_type}: No results found[/dim]")
        return
    
    # Create header panel
    header_text = f"{result_type} ({len(results)} total, showing top {min(max_display, len(results))})"
    console.print(Panel(header_text, style="bold cyan", border_style="cyan"))
    
    # Sort results by score (descending)
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    
    for rank, (doc_id, score) in enumerate(sorted_results[:max_display], 1):
        # Try to get document metadata
        doc = None
        
        # Try BM25 indexer first (has more fields)
        if indexer and hasattr(indexer, 'get_document'):
            try:
                doc = indexer.get_document(doc_id)
            except Exception:
                pass
        
        # Fallback to semantic indexer doc_map
        if not doc and indexer and hasattr(indexer, 'doc_map') and indexer.doc_map:
            for idx, meta in indexer.doc_map.items():
                if meta.get('id') == str(doc_id):
                    doc = meta
                    break
        
        # Create result panel
        if doc:
            content_lines = []
            
            if 'title' in doc:
                content_lines.append(f"[bold yellow]Title:[/bold yellow] {doc['title']}")
            
            if 'year' in doc:
                content_lines.append(f"[bold blue]Year:[/bold blue] {doc['year']}")
            
            if 'genres' in doc:
                genres = doc['genres']
                if isinstance(genres, str):
                    content_lines.append(f"[bold green]Genres:[/bold green] {genres}")
                else:
                    content_lines.append(f"[bold green]Genres:[/bold green] {', '.join(genres) if isinstance(genres, list) else genres}")
            
            if 'rating' in doc and doc['rating']:
                content_lines.append(f"[bold magenta]Rating:[/bold magenta] {doc['rating']}")
            
            if 'director' in doc and doc['director']:
                content_lines.append(f"[bold cyan]Director:[/bold cyan] {doc['director']}")
            
            if 'actors' in doc and doc['actors']:
                actors = doc['actors']
                if isinstance(actors, str):
                    actor_list = actors.split(',')[:5]
                    actors_display = ', '.join(actor_list)
                    if len(actors.split(',')) > 5:
                        actors_display += f" ... (+{len(actors.split(',')) - 5} more)"
                    content_lines.append(f"[bold white]Actors:[/bold white] {actors_display}")
                else:
                    content_lines.append(f"[bold white]Actors:[/bold white] {actors}")
            
            if 'characters' in doc and doc['characters']:
                characters = doc['characters']
                # Show all characters without truncation
                if isinstance(characters, str):
                    content_lines.append(f"[dim]Characters:[/dim] {characters}")
                else:
                    content_lines.append(f"[dim]Characters:[/dim] {characters}")
            
            if 'overview' in doc and doc['overview']:
                overview = doc['overview']
                if len(overview) > 200:
                    overview = overview[:200] + "..."
                content_lines.append(f"[dim]Overview:[/dim] {overview}")
            
            content = "\n".join(content_lines)
            title = f"[{rank}] Doc ID: {doc_id} | Score: {score:.4f}"
            console.print(Panel(content, title=title, border_style="blue"))
        else:
            title = f"[{rank}] Doc ID: {doc_id} | Score: {score:.4f}"
            console.print(Panel("[dim](Metadata not available)[/dim]", title=title, border_style="dim"))
    
    if len(results) > max_display:
        console.print(f"\n[dim]... and {len(results) - max_display} more results[/dim]\n")

