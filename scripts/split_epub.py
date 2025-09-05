#!/usr/bin/env python3
"""Script to split EPUB files into individual chapters."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table

from lib.epub_utils import EPUBProcessor
from config.settings import settings

console = Console()


@click.command()
@click.argument('epub_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), 
              help='Output directory for split files')
@click.option('--min-words', '-m', type=int, default=100,
              help='Minimum words per chapter (default: 100)')
@click.option('--preview', '-p', is_flag=True,
              help='Preview chapters without creating files')
def split_epub(epub_file, output_dir, min_words, preview):
    """
    Split an EPUB file into individual chapter files.
    
    EPUB_FILE: Path to the EPUB file to split
    """
    # Update settings
    settings.MIN_CHAPTER_LENGTH = min_words
    settings.ensure_directories()
    
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        console.print(f"[red]Error: File {epub_path} not found![/red]")
        return
        
    if not epub_path.suffix.lower() == '.epub':
        console.print(f"[red]Error: File must be an EPUB![/red]")
        return
        
    console.print(f"[bold blue]Processing: {epub_path.name}[/bold blue]\n")
    
    try:
        processor = EPUBProcessor(epub_path)
        
        if preview:
            # Just show chapter information
            chapters = processor.get_chapters()
            
            # Create table
            table = Table(title="Chapter Preview")
            table.add_column("Index", justify="right", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Words", justify="right", style="green")
            table.add_column("Est. Reading (min)", justify="right", style="yellow")
            
            from lib.text_cleaner import TextCleaner
            cleaner = TextCleaner()
            
            total_words = 0
            for idx, (chapter_id, title, content) in enumerate(chapters):
                text = cleaner.extract_text_from_html(content)
                word_count = len(text.split())
                reading_time = cleaner.estimate_reading_time(text)
                total_words += word_count
                
                table.add_row(
                    str(idx + 1),
                    title[:50] + "..." if len(title) > 50 else title,
                    str(word_count),
                    f"{reading_time:.1f}"
                )
                
            console.print(table)
            console.print(f"\n[bold]Total:[/bold] {len(chapters)} chapters, {total_words:,} words")
            
        else:
            # Actually split the file
            output_path = Path(output_dir) if output_dir else None
            created_files = processor.split_into_chapters(output_path)
            
            # Show summary
            console.print("\n[bold green]Summary:[/bold green]")
            for file_path in created_files:
                size_kb = file_path.stat().st_size / 1024
                console.print(f"  • {file_path.name} ({size_kb:.1f} KB)")
                
    except Exception as e:
        console.print(f"[red]Error processing EPUB: {e}[/red]")
        if settings.DEBUG_MODE:
            console.print_exception()
        return 1
        
    return 0


if __name__ == "__main__":
    split_epub()