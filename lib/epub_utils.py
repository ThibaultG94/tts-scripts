"""EPUB file manipulation utilities."""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
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
    
    # Keywords to identify non-content sections
    SKIP_KEYWORDS = [
        'sommaire', 'table des matières', 'table des noms', 'index',
        'bibliographie', 'références', 'notes', 'glossaire', 'lexique',
        'copyright', 'page de titre', 'couverture', 'colophon',
        'table of contents', 'bibliography', 'references', 'glossary'
    ]
    
    # Keywords to identify real content start
    CONTENT_START_KEYWORDS = [
        'introduction', 'préface', 'avant-propos', 'prologue',
        'chapitre', 'chapter', 'partie', 'part', 'livre', 'book'
    ]
    
    def __init__(self, epub_path: Path):
        """
        Initialize EPUB processor.
        
        Args:
            epub_path: Path to the EPUB file
        """
        self.epub_path = Path(epub_path)
        self.book = epub.read_epub(str(epub_path))
        self.cleaner = TextCleaner()
        
    def _should_skip_section(self, title: str, text: str) -> bool:
        """
        Determine if a section should be skipped.
        
        Args:
            title: Section title
            text: Section text content
            
        Returns:
            True if section should be skipped
        """
        title_lower = title.lower()
        
        # Check if it's a known skip section (but be less aggressive)
        skip_count = 0
        for keyword in self.SKIP_KEYWORDS:
            if keyword in title_lower:
                skip_count += 1
        
        # Only skip if title strongly suggests metadata (multiple keywords)
        if skip_count >= 2:
            return True
        
        # For single keyword matches, check content length
        if skip_count == 1:
            word_count = len(text.split())
            # Only skip if REALLY short (less than 50 words for metadata sections)
            if word_count < 50:
                return True
                
        # For normal chapters, use the configured minimum
        word_count = len(text.split())
        if word_count < settings.MIN_CHAPTER_LENGTH and not self._is_content_start(title):
            return True
            
        return False
    
    def _is_content_start(self, title: str) -> bool:
        """
        Check if this marks the start of actual content.
        
        Args:
            title: Section title
            
        Returns:
            True if this is where content starts
        """
        title_lower = title.lower()
        
        for keyword in self.CONTENT_START_KEYWORDS:
            if keyword in title_lower:
                return True
        
        return False
    
    def _extract_chapter_number(self, title: str) -> Optional[int]:
        """
        Extract chapter number from title if present.
        
        Args:
            title: Chapter title
            
        Returns:
            Chapter number or None
        """
        # Look for patterns like "Chapitre 1", "Chapter I", "Partie 2", etc.
        patterns = [
            r'chapitre\s+(\d+)',
            r'chapter\s+(\d+)',
            r'partie\s+(\d+)',
            r'part\s+(\d+)',
            r'livre\s+(\d+)',
            r'book\s+(\d+)',
        ]
        
        title_lower = title.lower()
        for pattern in patterns:
            match = re.search(pattern, title_lower)
            if match:
                return int(match.group(1))
                
        # Try Roman numerals
        roman_pattern = r'(?:chapitre|chapter|partie|part)\s+([IVXLCDM]+)'
        match = re.search(roman_pattern, title_lower)
        if match:
            return self._roman_to_int(match.group(1))
            
        return None
    
    def _roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer."""
        roman_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        prev = 0
        
        for char in roman.upper()[::-1]:
            value = roman_dict.get(char, 0)
            if value < prev:
                total -= value
            else:
                total += value
            prev = value
            
        return total
    
    def get_chapters(self, skip_metadata: bool = True) -> List[Tuple[str, str, str]]:
        """
        Extract chapters from EPUB intelligently.
        
        Args:
            skip_metadata: Skip non-content sections
            
        Returns:
            List of tuples (chapter_id, title, content_html)
        """
        chapters = []
        content_started = False
        chapter_counter = 0
        
        # Get all items of type DOCUMENT
        items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        for idx, item in enumerate(items):
            # Get content
            content = item.get_content().decode('utf-8', errors='ignore')
            
            # Parse to get title and text
            soup = BeautifulSoup(content, 'html.parser')
            title = self._extract_title(soup, idx)
            text = self.cleaner.extract_text_from_html(content)
            word_count = len(text.split())
            
            # Check if we should start collecting content
            if not content_started and self._is_content_start(title):
                content_started = True
                console.print(f"[green]Content starts at: {title}[/green]")
            
            # Skip if we haven't reached content yet
            if skip_metadata and not content_started:
                console.print(f"[yellow]Skipped metadata:[/yellow] {title}")
                continue
            
            # Skip non-content sections
            if skip_metadata and self._should_skip_section(title, text):
                console.print(f"[yellow]Skipped section:[/yellow] {title} ({word_count} words)")
                continue
            
            # Extract chapter number if present
            chapter_num = self._extract_chapter_number(title)
            
            # Create a proper chapter ID
            if chapter_num is not None:
                chapter_id = f"ch{chapter_num:03d}"
                display_title = title
            else:
                # Use sequential numbering for unnumbered chapters
                chapter_counter += 1
                chapter_id = f"ch{chapter_counter:03d}"
                display_title = f"Chapter {chapter_counter}: {title}"
            
            chapters.append((chapter_id, display_title, content))
            console.print(f"[green]Found chapter:[/green] {display_title} ({word_count} words)")
                
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
            if title_elem:
                # Get text, removing extra whitespace
                title_text = ' '.join(title_elem.get_text().split())
                if title_text:
                    return title_text
                    
        # Try to find first paragraph that looks like a title
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            if len(text) < 100 and not text.endswith('.'):
                return text
                
        # Fallback to generic title
        return f"Section {index + 1}"
    
    def split_into_chapters(self, output_dir: Optional[Path] = None, 
                           skip_metadata: bool = True) -> List[Path]:
        """
        Split EPUB into individual chapter files with intelligent naming.
        
        Args:
            output_dir: Directory to save split files
            skip_metadata: Skip non-content sections
            
        Returns:
            List of paths to created EPUB files
        """
        if output_dir is None:
            output_dir = settings.SPLIT_OUTPUT_DIR
            
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get base name without extension
        base_name = self.epub_path.stem
        
        chapters = self.get_chapters(skip_metadata=skip_metadata)
        created_files = []
        
        console.print(f"\n[bold blue]Splitting {len(chapters)} chapters from {self.epub_path.name}[/bold blue]")
        
        for chapter_id, title, content in track(chapters, description="Creating EPUB files"):
            # Create new EPUB for this chapter
            chapter_book = epub.EpubBook()
            
            # Set metadata
            original_title = self.book.get_metadata('DC', 'title')
            if original_title:
                chapter_book.set_title(f"{original_title[0][0]} - {title}")
            else:
                chapter_book.set_title(title)
            
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
            
            # Generate filename with clean chapter ID and safe title
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Limit length
            safe_title = re.sub(r'\s+', '_', safe_title)  # Replace spaces with underscores
            
            filename = output_dir / f"{base_name}_{chapter_id}_{safe_title}.epub"
            
            # Write EPUB
            epub.write_epub(str(filename), chapter_book, {})
            created_files.append(filename)
            
        console.print(f"[bold green]✓ Created {len(created_files)} EPUB files in {output_dir}[/bold green]")
        return created_files
    
    def extract_full_text(self, skip_metadata: bool = True) -> str:
        """
        Extract all text from EPUB.
        
        Args:
            skip_metadata: Skip non-content sections
            
        Returns:
            Full text content
        """
        full_text = []
        chapters = self.get_chapters(skip_metadata=skip_metadata)
        
        for chapter_id, title, content in chapters:
            text = self.cleaner.extract_text_from_html(content)
            if text:
                full_text.append(f"# {title}\n\n{text}")
                
        return "\n\n".join(full_text)