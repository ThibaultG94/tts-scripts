"""TTS engine using HuggingFace models (VITS)."""

import os
import tempfile
from pathlib import Path
from typing import Optional, List
import torch
from transformers import VitsModel, VitsTokenizer
import scipy.io.wavfile
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pydub import AudioSegment
import numpy as np

from config.settings import settings

console = Console()


class HuggingFaceTTS:
    """Wrapper for HuggingFace TTS models (VITS)."""
    
    # Available French models on HuggingFace
    MODELS = {
        "vits-fr": "facebook/mms-tts-fra",  # Facebook MMS French
        "upmc": "Pendrokar/xvapitch_vits",  # Alternative VITS model
        "mms-fra": "facebook/mms-tts-fra",  # Best quality French
    }
    
    def __init__(self, model_name: str = "mms-fra"):
        """
        Initialize HuggingFace TTS.
        
        Args:
            model_name: Model key or HuggingFace model path
        """
        # Select model
        if model_name in self.MODELS:
            self.model_path = self.MODELS[model_name]
        else:
            self.model_path = model_name
            
        console.print(f"[yellow]Loading model {self.model_path}...[/yellow]")
        
        try:
            # Load model and tokenizer
            self.tokenizer = VitsTokenizer.from_pretrained(self.model_path)
            self.model = VitsModel.from_pretrained(self.model_path)
            
            # Check for GPU
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = self.model.to(self.device)
            
            console.print(f"[green]✓ Model loaded successfully[/green]")
            console.print(f"[blue]Using device: {self.device}[/blue]")
            
        except Exception as e:
            console.print(f"[red]Failed to load model: {e}[/red]")
            console.print("[yellow]Installing required packages...[/yellow]")
            raise RuntimeError(f"Please install transformers and torch: pip install transformers torch")
        
        self.sample_rate = 16000  # VITS models typically use 16kHz
        
    def text_to_speech(self, text: str, output_path: Path) -> Path:
        """
        Convert text to speech using HuggingFace model.
        
        Args:
            text: Text to convert
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate speech
            with torch.no_grad():
                output = self.model(**inputs).waveform
            
            # Convert to numpy array
            waveform = output.squeeze().cpu().numpy()
            
            # Save as WAV first
            temp_wav = output_path.with_suffix('.wav')
            scipy.io.wavfile.write(str(temp_wav), rate=self.sample_rate, data=waveform)
            
            # Convert to desired format if needed
            if settings.AUDIO_FORMAT == "mp3":
                audio = AudioSegment.from_wav(str(temp_wav))
                mp3_path = output_path.with_suffix('.mp3')
                audio.export(str(mp3_path), format="mp3", bitrate=settings.AUDIO_BITRATE)
                temp_wav.unlink()  # Remove temp WAV
                return mp3_path
            else:
                return temp_wav
                
        except Exception as e:
            console.print(f"[red]Error generating speech: {e}[/red]")
            raise
            
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