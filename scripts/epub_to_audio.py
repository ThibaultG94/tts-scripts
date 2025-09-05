#!/usr/bin/env python3
"""Script to convert EPUB files to audio using TTS."""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

from lib.epub_utils import EPUBProcessor
from lib.tts_engine import PiperTTS
from lib.text_cleaner import TextCleaner
from config.settings import settings

console = Console()


def split_text_into_chunks(text: str, chunk_size: int) -> list[str]:
    """
    Split text into manageable chunks for TTS.
    
    Args:
        text: Text to split
        chunk_size: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    cleaner = TextCleaner()
    sentences = cleaner.split_into_sentences(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        if current_size + sentence_size > chunk_size and current_chunk:
            # Save current chunk and start new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence