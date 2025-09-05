"""EPUB file manipulation utilities."""

import os
from pathlib import Path
from typing import List, Tuple, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

from lib.text_cleaner import TextCleaner
from config.settings import settings

console = Console()


class EPUBProcessor:
    """Handle EPUB file operations."""
    
    def __init__(self, epub_path: Path):
        """
        Initialize EPUB processor.
        
        Args:
            epub_path: Path to the EPUB file
        """
        self.epub_path = Path(epub_path)
        self.book = epub.read_epub(str(epub_path))
        self.cleaner = TextCleaner()
        
    def get_chapters(self) -> List[Tuple[str, str, str]]:
        """
        Extract chapters from EPUB.
        
        Returns:
            List of tuples (chapter_id, title, content_html)
        """
        chapters = []
        
        # Get all items of type DOCUMENT
        items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        for idx, item in enumerate(items):
            # Get content
            content = item.get_content().decode('utf-8', errors='ignore')
            
            # Parse to get title
            soup = BeautifulSoup(content, 'html.parser')
            title = self._extract_title(soup, idx)
            
            # Check if content is substantial
            text = self.cleaner.extract_text_from_html(content)
            word_count = len(text.split())
            
            if word_count >= settings.MIN_CHAPTER_LENGTH:
                chapter_id = f"chapter_{idx:03d}"
                chapters.append((chapter_id, title, content))
                console.print(f"[green]Found chapter:[/green] {title} ({word_count} words)")
            else:
                console.print(f"[yellow]Skipped short section:[/yellow] {title} ({word_count} words)")
                
        return chapters
    
    def _extract_title(self, soup: BeautifulSoup, index: int) -> str:
        """
        Extract chapter title from HTML.
        
        Args:
            soup: BeautifulSoup object
            index: Chapter index
            
        Returns:
            Chapter title
        """
        # Try to find title in order of preference
        for tag in ['h1', 'h2', 'h3', 'title']:
            title_elem = soup.find(tag)
            if title_elem and title_elem.string:
                return title_elem.string.strip()
                
        # Fallback to generic title
        return f"Chapter {index + 1}"
    
    def split_into_chapters(self, output_dir: Optional[Path] = None) -> List[Path]:
        """
        Split EPUB into individual chapter files.
        
        Args:
            output_dir: Directory to save split files
            
        Returns:
            List of paths to created EPUB files
        """
        if output_dir is None:
            output_dir = settings.SPLIT_OUTPUT_DIR
            
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get base name without extension
        base_name = self.epub_path.stem
        
        chapters = self.get_chapters()
        created_files = []
        
        console.print(f"\n[bold blue]Splitting {len(chapters)} chapters from {self.epub_path.name}[/bold blue]")
        
        for chapter_id, title, content in track(chapters, description="Creating EPUB files"):
            # Create new EPUB for this chapter
            chapter_book = epub.EpubBook()
            
            # Copy metadata from original
            chapter_book.set_title(f"{self.book.get_metadata('DC', 'title')[0][0]} - {title}")
            
            # Copy other metadata if exists
            for author in self.book.get_metadata('DC', 'creator'):
                chapter_book.add_author(author[0])
            
            chapter_book.set_language(self.book.get_metadata('DC', 'language')[0][0] 
                                     if self.book.get_metadata('DC', 'language') else 'fr')
            
            # Create chapter item
            chapter_item = epub.EpubHtml(
                title=title,
                file_name=f'{chapter_id}.xhtml',
                lang='fr'
            )
            chapter_item.content = content.encode('utf-8')
            
            # Add chapter to book
            chapter_book.add_item(chapter_item)
            
            # Create TOC and spine
            chapter_book.toc = (epub.Link(f'{chapter_id}.xhtml', title, chapter_id),)
            chapter_book.spine = ['nav', chapter_item]
            
            # Add navigation files
            chapter_book.add_item(epub.EpubNcx())
            chapter_book.add_item(epub.EpubNav())
            
            # Generate filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = output_dir / f"{base_name}_{chapter_id}_{safe_title}.epub"
            
            # Write EPUB
            epub.write_epub(str(filename), chapter_book, {})
            created_files.append(filename)
            
        console.print(f"[bold green]✓ Created {len(created_files)} EPUB files in {output_dir}[/bold green]")
        return created_files
    
    def extract_full_text(self) -> str:
        """
        Extract all text from EPUB.
        
        Returns:
            Full text content
        """
        full_text = []
        
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content().decode('utf-8', errors='ignore')
            text = self.cleaner.extract_text_from_html(content)
            if text:
                full_text.append(text)
                
        return "\n\n".join(full_text)