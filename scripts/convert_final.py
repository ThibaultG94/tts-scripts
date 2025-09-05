#!/usr/bin/env python3
"""Final conversion script with proper MP3 handling and better chapter detection."""

import sys
import subprocess
import shutil
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import track

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.epub_utils import EPUBProcessor
from lib.text_cleaner import TextCleaner

console = Console()


def find_tools():
    """Find required tools (piper, ffmpeg)."""
    tools = {}
    
    # Find Piper
    for cmd in ['/usr/local/bin/piper-bin', '/usr/local/bin/piper', 'piper']:
        if shutil.which(cmd):
            tools['piper'] = cmd
            break
    else:
        console.print("[red]❌ Piper not found![/red]")
        sys.exit(1)
    
    # Find ffmpeg
    tools['ffmpeg'] = shutil.which('ffmpeg')
    if not tools['ffmpeg']:
        console.print("[yellow]⚠️  ffmpeg not found - MP3 conversion disabled[/yellow]")
    
    return tools


def find_voice(voice_name):
    """Find voice model path."""
    base_dir = Path.home() / "work/tts-scripts/voices/fr_FR"
    
    voice_map = {
        'upmc': base_dir / 'upmc/medium/fr_FR-upmc-medium.onnx',
        'siwis': base_dir / 'siwis/medium/fr_FR-siwis-medium.onnx',
        'tom': base_dir / 'tom/medium/fr_FR-tom-medium.onnx',
        'gilles': base_dir / 'gilles/low/fr_FR-gilles-low.onnx',
        'mls': base_dir / 'mls/medium/fr_FR-mls-medium.onnx',
    }
    
    if voice_name in voice_map:
        model_path = voice_map[voice_name]
    else:
        model_path = Path(voice_name)
    
    if not model_path.exists():
        console.print(f"[red]❌ Voice not found: {model_path}[/red]")
        sys.exit(1)
    
    config_path = model_path.with_suffix('.onnx.json')
    return model_path, config_path if config_path.exists() else None


def convert_to_mp3(wav_file, mp3_file, quality='2'):
    """Convert WAV to MP3 using ffmpeg."""
    try:
        cmd = [
            'ffmpeg', '-y', '-i', str(wav_file),
            '-codec:a', 'libmp3lame',
            '-qscale:a', quality,  # 2 = ~190kbps (good quality)
            str(mp3_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            console.print(f"[red]FFmpeg error: {result.stderr[:200]}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]MP3 conversion error: {e}[/red]")
        return False


@click.command()
@click.option('--split-dir', '-i', default='output/split', 
              help='Input directory with EPUB files')
@click.option('--audio-dir', '-o', default='output/audio',
              help='Output directory for audio files')
@click.option('--voice', '-v', default='upmc',
              help='Voice: upmc, siwis, tom, gilles, mls')
@click.option('--format', '-f', type=click.Choice(['wav', 'mp3', 'both']), default='mp3',
              help='Output format (default: mp3)')
@click.option('--min-words', '-m', type=int, default=20,
              help='Minimum words per chapter (default: 20)')
@click.option('--clean', is_flag=True,
              help='Clean existing audio files first')
@click.option('--resplit', is_flag=True,
              help='Re-split the original EPUB first')
def convert_all(split_dir, audio_dir, voice, format, min_words, clean, resplit):
    """Convert all EPUB chapters to audio with Piper."""
    
    console.print("[bold blue]📚 EPUB to Audio Converter[/bold blue]\n")
    
    # Find tools
    tools = find_tools()
    console.print(f"✅ Piper: {tools['piper']}")
    if tools['ffmpeg']:
        console.print(f"✅ FFmpeg: found")
    
    # Find voice
    model_path, config_path = find_voice(voice)
    console.print(f"✅ Voice: {model_path.stem}\n")
    
    # Setup directories
    split_path = Path(split_dir)
    audio_path = Path(audio_dir)
    audio_path.mkdir(parents=True, exist_ok=True)
    
    # Clean if requested
    if clean:
        console.print("🧹 Cleaning existing audio files...")
        for f in audio_path.glob('*.wav'):
            f.unlink()
        for f in audio_path.glob('*.mp3'):
            f.unlink()
    
    # Find EPUB files
    epub_files = sorted(split_path.glob('*.epub'))
    
    if not epub_files:
        console.print(f"[red]No EPUB files in {split_path}[/red]")
        return
    
    console.print(f"Found {len(epub_files)} EPUB files\n")
    
    # Process each file
    stats = {'converted': 0, 'skipped': 0, 'failed': 0, 'total_words': 0}
    
    for epub_file in track(epub_files, description="Converting..."):
        try:
            # Extract text
            processor = EPUBProcessor(epub_file)
            
            # Get text with less aggressive filtering
            from config.settings import settings
            old_min = settings.MIN_CHAPTER_LENGTH
            settings.MIN_CHAPTER_LENGTH = min_words  # Temporary override
            
            text = processor.extract_full_text(skip_metadata=True)
            
            settings.MIN_CHAPTER_LENGTH = old_min  # Restore
            
            if not text or len(text.split()) < min_words:
                stats['skipped'] += 1
                continue
            
            # Clean text
            cleaner = TextCleaner()
            text = cleaner.clean_text_for_tts(text)
            word_count = len(text.split())
            stats['total_words'] += word_count
            
            # Output filename
            base_name = epub_file.stem
            wav_file = audio_path / f"{base_name}.wav"
            mp3_file = audio_path / f"{base_name}.mp3"
            
            # Write text to temp file
            temp_text = Path(f"/tmp/{base_name}.txt")
            temp_text.write_text(text, encoding='utf-8')
            
            # Run Piper
            cmd = [tools['piper'], '--model', str(model_path)]
            if config_path:
                cmd.extend(['--config', str(config_path)])
            cmd.extend(['--output_file', str(wav_file)])
            
            with open(temp_text, 'r') as stdin:
                result = subprocess.run(cmd, stdin=stdin, capture_output=True)
            
            if result.returncode != 0:
                console.print(f"[red]Failed: {base_name}[/red]")
                stats['failed'] += 1
                continue
            
            # Handle format conversion
            if format == 'mp3' or format == 'both':
                if tools['ffmpeg']:
                    if convert_to_mp3(wav_file, mp3_file):
                        if format == 'mp3':
                            wav_file.unlink()  # Remove WAV if only MP3 wanted
                    else:
                        console.print(f"[yellow]MP3 conversion failed for {base_name}[/yellow]")
            
            stats['converted'] += 1
            temp_text.unlink(missing_ok=True)
            
        except Exception as e:
            console.print(f"[red]Error: {epub_file.name}: {e}[/red]")
            stats['failed'] += 1
    
    # Summary
    console.print("\n" + "="*50)
    console.print("[bold]Conversion Complete![/bold]\n")
    
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("✅ Converted", str(stats['converted']))
    table.add_row("⏭️  Skipped", str(stats['skipped']))
    table.add_row("❌ Failed", str(stats['failed']))
    table.add_row("📝 Total words", f"{stats['total_words']:,}")
    
    # Calculate audio duration estimate
    minutes = stats['total_words'] / 150  # ~150 words per minute
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    table.add_row("⏱️  Est. duration", f"{hours}h {mins}min")
    
    console.print(table)
    
    # List audio files
    audio_files = list(audio_path.glob('*.wav')) + list(audio_path.glob('*.mp3'))
    if audio_files:
        total_size = sum(f.stat().st_size for f in audio_files) / (1024**3)  # GB
        console.print(f"\n📁 {len(audio_files)} audio files")
        console.print(f"💾 Total size: {total_size:.2f} GB")
        
        if format == 'both':
            wav_size = sum(f.stat().st_size for f in audio_path.glob('*.wav')) / (1024**3)
            mp3_size = sum(f.stat().st_size for f in audio_path.glob('*.mp3')) / (1024**3)
            console.print(f"   WAV: {wav_size:.2f} GB")
            console.print(f"   MP3: {mp3_size:.2f} GB")


if __name__ == "__main__":
    convert_all()