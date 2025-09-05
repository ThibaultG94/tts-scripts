"""Configuration management for TTS scripts."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    OUTPUT_DIR = BASE_DIR / "output"
    SPLIT_OUTPUT_DIR = OUTPUT_DIR / "split"
    AUDIO_OUTPUT_DIR = OUTPUT_DIR / "audio"
    
    # EPUB processing
    MIN_CHAPTER_LENGTH = int(os.getenv("MIN_CHAPTER_LENGTH", "100"))  # Minimum words per chapter
    PRESERVE_IMAGES = os.getenv("PRESERVE_IMAGES", "false").lower() == "true"
    
    # TTS settings
    TTS_MODEL = os.getenv("TTS_MODEL", "fr_FR-upmc-medium")  # Piper model name
    TTS_VOICE_SPEED = float(os.getenv("TTS_VOICE_SPEED", "1.0"))  # Speed multiplier
    TTS_SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", "22050"))  # Audio sample rate
    
    # Audio settings
    AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")  # wav or mp3
    AUDIO_BITRATE = os.getenv("AUDIO_BITRATE", "192k")  # For MP3
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))  # Characters per TTS chunk
    
    # Processing
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))  # For parallel processing
    DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def ensure_directories(cls):
        """Create output directories if they don't exist."""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.SPLIT_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        cls.AUDIO_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


settings = Settings()