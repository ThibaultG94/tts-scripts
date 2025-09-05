"""TTS engine wrapper for Piper."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List
import wave
import struct
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pydub import AudioSegment

from config.settings import settings

console = Console()


class PiperTTS:
    """Wrapper for Piper TTS engine."""
    
    def __init__(self, model: str = None):
        """
        Initialize Piper TTS.
        
        Args:
            model: Model name to use
        """
        self.model = model or settings.TTS_MODEL
        self.sample_rate = settings.TTS_SAMPLE_RATE
        self.speed = settings.TTS_VOICE_SPEED
        
        # Check if piper is available
        self._check_piper()
        
    def _check_piper(self):
        """Check if Piper is installed and download model if needed."""
        try:
            result = subprocess.run(['piper', '--version'], 
                                  capture_output=True, text=True)
            console.print(f"[green]✓ Piper TTS found[/green]")
        except FileNotFoundError:
            console.print("[red]✗ Piper not found![/red]")
            console.print("Install with: pip install piper-tts")
            raise RuntimeError("Piper TTS not installed")
            
        # Check/download model
        self._ensure_model()
        
    def _ensure_model(self):
        """Ensure the TTS model is downloaded."""
        # For Piper, models are usually downloaded automatically
        # This is a placeholder for model management
        console.print(f"[blue]Using model: {self.model}[/blue]")
        
    def text_to_speech(self, text: str, output_path: Path) -> Path:
        """
        Convert text to speech using Piper.
        
        Args:
            text: Text to convert
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(text)
            tmp_text_path = tmp_file.name
            
        try:
            # Run Piper
            cmd = [
                'piper',
                '--model', self.model,
                '--output_file', str(output_path),
            ]
            
            if self.speed != 1.0:
                cmd.extend(['--length-scale', str(1.0 / self.speed)])
                
            # Run with input from file
            with open(tmp_text_path, 'r') as input_file:
                result = subprocess.run(
                    cmd,
                    stdin=input_file,
                    capture_output=True,
                    text=True
                )
                
            if result.returncode != 0:
                console.print(f"[red]Piper error: {result.stderr}[/red]")
                raise RuntimeError(f"Piper TTS failed: {result.stderr}")
                
            # Convert to desired format if needed
            if settings.AUDIO_FORMAT == "mp3" and output_path.suffix == ".wav":
                mp3_path = output_path.with_suffix(".mp3")
                self._convert_to_mp3(output_path, mp3_path)
                output_path.unlink()  # Remove WAV file
                return mp3_path
                
            return output_path
            
        finally:
            # Clean up temp file
            Path(tmp_text_path).unlink(missing_ok=True)
            
    def _convert_to_mp3(self, wav_path: Path, mp3_path: Path):
        """
        Convert WAV to MP3 using pydub.
        
        Args:
            wav_path: Source WAV file
            mp3_path: Destination MP3 file
        """
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3", bitrate=settings.AUDIO_BITRATE)
        
    def process_chunks(self, text_chunks: List[str], output_base: Path, 
                      combine: bool = True) -> Path:
        """
        Process multiple text chunks and optionally combine.
        
        Args:
            text_chunks: List of text chunks
            output_base: Base path for output
            combine: Whether to combine chunks into single file
            
        Returns:
            Path to final audio file
        """
        chunk_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Processing chunks...", 
                total=len(text_chunks)
            )
            
            for i, chunk in enumerate(text_chunks):
                chunk_path = output_base.parent / f"{output_base.stem}_chunk_{i:03d}.wav"
                self.text_to_speech(chunk, chunk_path)
                chunk_files.append(chunk_path)
                progress.update(task, advance=1)
        
        if combine:
            # Combine all chunks
            combined = AudioSegment.empty()
            
            for chunk_file in chunk_files:
                audio = AudioSegment.from_wav(str(chunk_file))
                combined += audio
                # Add small pause between chunks
                combined += AudioSegment.silent(duration=500)  # 0.5 second pause
                
            # Save combined file
            final_path = output_base.with_suffix(f".{settings.AUDIO_FORMAT}")
            if settings.AUDIO_FORMAT == "mp3":
                combined.export(str(final_path), format="mp3", bitrate=settings.AUDIO_BITRATE)
            else:
                combined.export(str(final_path), format="wav")
                
            # Clean up chunk files
            for chunk_file in chunk_files:
                chunk_file.unlink()
                
            return final_path
        else:
            return output_base.parent  # Return directory with chunks