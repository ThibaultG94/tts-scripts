"""Alternative TTS engine using Edge-TTS (Microsoft)."""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional, List
import edge_tts
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pydub import AudioSegment

from config.settings import settings

console = Console()


class EdgeTTS:
    """Wrapper for Edge TTS engine (Microsoft voices)."""
    
    # Available French voices
    FRENCH_VOICES = {
        "henri": "fr-FR-HenriNeural",      # Male voice
        "denise": "fr-FR-DeniseNeural",    # Female voice
        "brigitte": "fr-FR-BrigitteNeural", # Female voice
        "alain": "fr-FR-AlainNeural",      # Male voice
        "claude": "fr-FR-ClaudeNeural",    # Male voice
        "celine": "fr-FR-CelineNeural",    # Female voice
    }
    
    def __init__(self, voice: str = None):
        """
        Initialize Edge TTS.
        
        Args:
            voice: Voice name or key from FRENCH_VOICES
        """
        if voice and voice in self.FRENCH_VOICES:
            self.voice = self.FRENCH_VOICES[voice]
        elif voice and voice.startswith("fr-"):
            self.voice = voice
        else:
            # Default to Henri (male voice)
            self.voice = self.FRENCH_VOICES["henri"]
            
        self.speed = settings.TTS_VOICE_SPEED
        
        console.print(f"[green]✓ Edge-TTS initialized[/green]")
        console.print(f"[blue]Using voice: {self.voice}[/blue]")
        
    async def _text_to_speech_async(self, text: str, output_path: Path) -> Path:
        """
        Async version of text to speech conversion.
        
        Args:
            text: Text to convert
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate rate string for speed adjustment
        # Edge-TTS uses percentage: +0% is normal, +50% is 1.5x speed
        rate_percent = int((self.speed - 1.0) * 100)
        rate_string = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
        
        # Create TTS communicate object
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=rate_string
        )
        
        # Generate audio
        temp_mp3 = output_path.with_suffix('.mp3')
        await communicate.save(str(temp_mp3))
        
        # Convert to desired format if needed
        if settings.AUDIO_FORMAT == "wav":
            audio = AudioSegment.from_mp3(str(temp_mp3))
            wav_path = output_path.with_suffix('.wav')
            audio.export(str(wav_path), format="wav")
            temp_mp3.unlink()  # Remove temp MP3
            return wav_path
        else:
            return temp_mp3
            
    def text_to_speech(self, text: str, output_path: Path) -> Path:
        """
        Convert text to speech using Edge-TTS.
        
        Args:
            text: Text to convert
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        # Run async function in sync context
        return asyncio.run(self._text_to_speech_async(text, output_path))
    
    async def _process_chunks_async(self, text_chunks: List[str], output_base: Path, 
                                  combine: bool = True) -> Path:
        """
        Async version of chunk processing.
        
        Args:
            text_chunks: List of text chunks
            output_base: Base path for output
            combine: Whether to combine chunks
            
        Returns:
            Path to final audio file
        """
        chunk_files = []
        
        # Process chunks sequentially (Edge-TTS free tier has rate limits)
        for i, chunk in enumerate(text_chunks):
            console.print(f"[cyan]Processing chunk {i+1}/{len(text_chunks)}...[/cyan]")
            chunk_path = output_base.parent / f"{output_base.stem}_chunk_{i:03d}.mp3"
            await self._text_to_speech_async(chunk, chunk_path)
            chunk_files.append(chunk_path)
        
        if combine:
            # Combine all chunks
            combined = AudioSegment.empty()
            
            for chunk_file in chunk_files:
                audio = AudioSegment.from_mp3(str(chunk_file))
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
            return output_base.parent
            
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
        return asyncio.run(self._process_chunks_async(text_chunks, output_base, combine))
    
    @classmethod
    async def list_voices_async(cls) -> List[str]:
        """
        List all available voices.
        
        Returns:
            List of voice names
        """
        voices = await edge_tts.list_voices()
        french_voices = [v['Name'] for v in voices if v['Locale'].startswith('fr-')]
        return french_voices
    
    @classmethod
    def list_voices(cls) -> List[str]:
        """
        List all available French voices.
        
        Returns:
            List of voice names
        """
        return asyncio.run(cls.list_voices_async())
    
    @classmethod
    def print_available_voices(cls):
        """Print all available French voices with descriptions."""
        console.print("\n[bold]Available French voices for Edge-TTS:[/bold]")
        for key, voice_id in cls.FRENCH_VOICES.items():
            console.print(f"  • {key:10} → {voice_id}")
        
        console.print("\n[dim]Getting full list from Edge-TTS...[/dim]")
        try:
            all_voices = cls.list_voices()
            if all_voices:
                console.print("\n[bold]All French voices from Edge:[/bold]")
                for voice in all_voices:
                    console.print(f"  • {voice}")
        except Exception as e:
            console.print(f"[yellow]Could not fetch voice list: {e}[/yellow]")