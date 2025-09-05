#!/usr/bin/env python3
"""Convert EPUB chapters to audio using Piper (working version)."""

import sys
import subprocess
from pathlib import Path
import click
from rich.console import Console
from rich.progress import track

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.epub_utils import EPUBProcessor
from lib.text_cleaner import TextCleaner

console = Console()


def find_piper():
    """Find the best Piper executable."""
    # Try different piper locations
    candidates = [
        '/usr/local/bin/piper-bin',  # Our binary install
        '/usr/local/bin/piper',       # Standard binary
        'piper',                      # In PATH
    ]
    
    for cmd in candidates:
        try:
            result = subprocess.run([cmd, '--help'], capture_output=True)
            if result.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue
    
    console.print("[red]❌ Piper not found![/red]")
    console.print("Install with:")
    console.print("  wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz")
    console.print("  tar -xzf piper_linux_x86_64.tar.gz")
    console.print("  sudo mv piper/piper /usr/local/bin/piper-bin")
    sys.exit(1)


def find_voice(voice_name):
    """Find voice model path."""
    base_dir = Path.home() / "work/tts-scripts/voices/fr_FR"
    
    # Map of short names to paths
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
        model_path = Path(voice_name)  # Try as full path
    
    if not model_path.exists():
        console.print(f"[red]❌ Voice model not found: {model_path}[/red]")
        console.print("\nAvailable voices:")
        for name, path in voice_map.items():
            status = "✅" if path.exists() else "❌"
            console.print(f"  {status} {name}: {path}")
        sys.exit(1)
    
    # Check for config file
    config_path = model_path.with_suffix('.onnx.json')
    if not config_path.exists():
        console.print(f"[yellow]⚠️  Config file not found: {config_path}[/yellow]")
        config_path = None
    
    return model_path, config_path


@click.command()
@click.argument('epub_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--voice', '-v', default='upmc', 
              help='Voice: upmc, siwis, tom, gilles, mls (default: upmc)')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory (default: output/audio)')
@click.option('--format', '-f', type=click.Choice(['wav', 'mp3']), default='wav',
              help='Output format (default: wav)')
@click.option('--speed', '-s', type=float, default=1.0,
              help='Speech speed (0.5-2.0, default: 1.0)')
def convert_epub_to_audio(epub_files, voice, output_dir, format, speed):
    """Convert EPUB files to audio using Piper TTS."""
    
    # Find Piper
    piper_cmd = find_piper()
    console.print(f"[green]✅ Using Piper: {piper_cmd}[/green]")
    
    # Find voice model
    model_path, config_path = find_voice(voice)
    console.print(f"[green]✅ Using voice: {model_path.stem}[/green]")
    
    # Setup output directory
    output_path = Path(output_dir) if output_dir else Path("output/audio")
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n[bold blue]Converting {len(epub_files)} EPUB files[/bold blue]")
    console.print(f"Output: {output_path}\n")
    
    successful = []
    failed = []
    
    for epub_file in track(epub_files, description="Converting..."):
        epub_path = Path(epub_file)
        
        try:
            # Extract text from EPUB
            processor = EPUBProcessor(epub_path)
            text = processor.extract_full_text(skip_metadata=True)
            
            if not text.strip():
                console.print(f"[yellow]⚠️  No text in {epub_path.name}[/yellow]")
                continue
            
            # Clean text for TTS
            cleaner = TextCleaner()
            text = cleaner.clean_text_for_tts(text)
            
            # Prepare output filename
            output_file = output_path / f"{epub_path.stem}.{format}"
            
            # Create temp text file
            temp_text = Path(f"/tmp/{epub_path.stem}.txt")
            temp_text.write_text(text, encoding='utf-8')
            
            # Prepare Piper command
            cmd = [piper_cmd, '--model', str(model_path)]
            
            if config_path:
                cmd.extend(['--config', str(config_path)])
            
            if speed != 1.0:
                # Piper uses length_scale (inverse of speed)
                length_scale = 1.0 / speed
                cmd.extend(['--length-scale', str(length_scale)])
            
            # Output format
            if format == 'wav':
                cmd.extend(['--output_file', str(output_file)])
            else:
                # Output to WAV first, then convert
                temp_wav = Path(f"/tmp/{epub_path.stem}.wav")
                cmd.extend(['--output_file', str(temp_wav)])
            
            # Run Piper
            with open(temp_text, 'r') as stdin:
                result = subprocess.run(cmd, stdin=stdin, capture_output=True, text=True)
            
            if result.returncode != 0:
                console.print(f"[red]❌ Failed: {epub_path.name}[/red]")
                console.print(f"   Error: {result.stderr[:200]}")
                failed.append(epub_path.name)
                continue
            
            # Convert to MP3 if needed
            if format == 'mp3':
                temp_wav = Path(f"/tmp/{epub_path.stem}.wav")
                subprocess.run([
                    'ffmpeg', '-y', '-i', str(temp_wav),
                    '-codec:a', 'libmp3lame', '-qscale:a', '2',
                    str(output_file)
                ], capture_output=True)
                temp_wav.unlink()
            
            # Clean up temp file
            temp_text.unlink(missing_ok=True)
            
            # Get file size
            size_mb = output_file.stat().st_size / (1024 * 1024)
            console.print(f"[green]✅ {output_file.name} ({size_mb:.1f} MB)[/green]")
            successful.append(output_file.name)
            
        except Exception as e:
            console.print(f"[red]❌ Error with {epub_path.name}: {e}[/red]")
            failed.append(epub_path.name)
    
    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"✅ Successful: {len(successful)}")
    console.print(f"❌ Failed: {len(failed)}")
    
    if successful:
        console.print(f"\n[green]Audio files in {output_path}:[/green]")
        for name in successful[:5]:
            console.print(f"  • {name}")
        if len(successful) > 5:
            console.print(f"  ... and {len(successful) - 5} more")


if __name__ == "__main__":
    convert_epub_to_audio()