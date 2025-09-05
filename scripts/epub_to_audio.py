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
            current_chunk.append(sentence)
            current_size += sentence_size
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


@click.command()
@click.argument('epub_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for audio files')
@click.option('--model', '-m', type=str, default='fr_FR-upmc-medium',
              help='TTS model to use (default: fr_FR-upmc-medium)')
@click.option('--format', '-f', type=click.Choice(['wav', 'mp3']), default='wav',
              help='Output audio format (default: wav)')
@click.option('--speed', '-s', type=float, default=1.0,
              help='Speech speed multiplier (default: 1.0)')
@click.option('--chunk-size', '-c', type=int, default=5000,
              help='Characters per TTS chunk (default: 5000)')
@click.option('--combine-chapters', is_flag=True,
              help='Combine all chapters into a single audio file')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without actually converting')
def epub_to_audio(epub_files, output_dir, model, format, speed, chunk_size, combine_chapters, dry_run):
    """
    Convert EPUB file(s) to audio using TTS.
    
    EPUB_FILES: Path(s) to EPUB file(s) to convert
    """
    # Update settings
    settings.TTS_MODEL = model
    settings.AUDIO_FORMAT = format
    settings.TTS_VOICE_SPEED = speed
    settings.CHUNK_SIZE = chunk_size
    settings.ensure_directories()
    
    output_path = Path(output_dir) if output_dir else settings.AUDIO_OUTPUT_DIR
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold blue]Converting {len(epub_files)} EPUB file(s) to audio[/bold blue]")
    console.print(f"Model: {model}")
    console.print(f"Format: {format}")
    console.print(f"Speed: {speed}x")
    console.print(f"Output: {output_path}\n")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be created[/yellow]\n")
    
    # Initialize TTS engine
    if not dry_run:
        try:
            tts = PiperTTS(model=model)
        except RuntimeError as e:
            console.print(f"[red]Failed to initialize TTS: {e}[/red]")
            return 1
    
    cleaner = TextCleaner()
    all_audio_files = []
    
    for epub_file in epub_files:
        epub_path = Path(epub_file)
        console.print(f"\n[cyan]Processing: {epub_path.name}[/cyan]")
        
        try:
            processor = EPUBProcessor(epub_path)
            
            # Get chapters or full text
            if combine_chapters:
                # Get all text as one
                console.print("Extracting full text...")
                full_text = processor.extract_full_text()
                
                if dry_run:
                    word_count = len(full_text.split())
                    reading_time = cleaner.estimate_reading_time(full_text)
                    console.print(f"  • Would process {word_count:,} words")
                    console.print(f"  • Estimated audio: {reading_time:.1f} minutes")
                    continue
                
                # Split into chunks
                chunks = split_text_into_chunks(full_text, chunk_size)
                console.print(f"  • Split into {len(chunks)} chunks")
                
                # Generate audio
                output_file = output_path / f"{epub_path.stem}_full.{format}"
                final_audio = tts.process_chunks(chunks, output_file.with_suffix(''), combine=True)
                
                console.print(f"[green]✓ Created: {final_audio.name}[/green]")
                all_audio_files.append(final_audio)
                
            else:
                # Process each chapter separately
                chapters = processor.get_chapters()
                
                for idx, (chapter_id, title, content) in enumerate(chapters):
                    # Extract text
                    text = cleaner.extract_text_from_html(content)
                    word_count = len(text.split())
                    
                    console.print(f"  Chapter {idx+1}: {title} ({word_count} words)")
                    
                    if dry_run:
                        reading_time = cleaner.estimate_reading_time(text)
                        console.print(f"    • Estimated audio: {reading_time:.1f} minutes")
                        continue
                    
                    # Generate safe filename
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                    output_file = output_path / f"{epub_path.stem}_{chapter_id}_{safe_title}.{format}"
                    
                    # Split into chunks if needed
                    if len(text) > chunk_size:
                        chunks = split_text_into_chunks(text, chunk_size)
                        console.print(f"    • Processing {len(chunks)} chunks...")
                        final_audio = tts.process_chunks(chunks, output_file.with_suffix(''), combine=True)
                    else:
                        # Process as single chunk
                        final_audio = tts.text_to_speech(text, output_file)
                    
                    console.print(f"    [green]✓ Created: {final_audio.name}[/green]")
                    all_audio_files.append(final_audio)
                    
        except Exception as e:
            console.print(f"[red]Error processing {epub_path.name}: {e}[/red]")
            if settings.DEBUG_MODE:
                console.print_exception()
            continue
    
    # Summary
    if not dry_run and all_audio_files:
        console.print(f"\n[bold green]Conversion complete![/bold green]")
        console.print(f"Created {len(all_audio_files)} audio file(s):")
        
        total_size = 0
        for audio_file in all_audio_files:
            size_mb = audio_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            console.print(f"  • {audio_file.name} ({size_mb:.1f} MB)")
        
        console.print(f"\nTotal size: {total_size:.1f} MB")
    
    return 0


if __name__ == "__main__":
    epub_to_audio()