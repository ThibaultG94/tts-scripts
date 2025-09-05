"""Text extraction and cleaning utilities."""

import re
from typing import Optional
from bs4 import BeautifulSoup, NavigableString


class TextCleaner:
    """Clean and prepare text for TTS processing."""
    
    @staticmethod
    def extract_text_from_html(html_content: str) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html_content: HTML string to clean
            
        Returns:
            Cleaned text string
        """
        if not html_content:
            return ""
            
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return TextCleaner.clean_text_for_tts(text)
    
    @staticmethod
    def clean_text_for_tts(text: str) -> str:
        """
        Clean text specifically for TTS processing.
        
        Args:
            text: Raw text to clean
            
        Returns:
            TTS-ready text
        """
        if not text:
            return ""
            
        # Replace special characters
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '…': '...',
            '–': '-',
            '—': '-',
            '\xa0': ' ',  # Non-breaking space
            '\u200b': '',  # Zero-width space
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix common TTS pronunciation issues
        text = TextCleaner.fix_pronunciation(text)
        
        return text
    
    @staticmethod
    def fix_pronunciation(text: str) -> str:
        """
        Fix common pronunciation issues for French TTS.
        
        Args:
            text: Text to fix
            
        Returns:
            Text with improved pronunciation markers
        """
        # Add space after punctuation if missing
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Handle common abbreviations
        abbreviations = {
            'M.': 'Monsieur',
            'Mme': 'Madame',
            'Dr': 'Docteur',
            'etc.': 'et cetera',
            'ex.': 'exemple',
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        return text
    
    @staticmethod
    def split_into_sentences(text: str) -> list[str]:
        """
        Split text into sentences for better TTS processing.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def estimate_reading_time(text: str, words_per_minute: int = 150) -> float:
        """
        Estimate reading time in minutes.
        
        Args:
            text: Text to estimate
            words_per_minute: Reading speed
            
        Returns:
            Estimated time in minutes
        """
        word_count = len(text.split())
        return word_count / words_per_minute