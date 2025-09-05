tts-scripts/
├── requirements.txt # Dependencies
├── .env.example # Environment variables template
├── .gitignore # Git ignore file
├── README.md # Project documentation
│
├── scripts/
│ ├── **init**.py
│ ├── split_epub.py # Script to split EPUB by chapters
│ └── epub_to_audio.py # Script to convert EPUB to audio
│
├── lib/
│ ├── **init**.py
│ ├── epub_utils.py # EPUB manipulation utilities
│ ├── text_cleaner.py # Text extraction and cleaning
│ └── tts_engine.py # TTS wrapper (Piper)
│
├── config/
│ ├── **init**.py
│ └── settings.py # Configuration management
│
├── tests/
│ ├── **init**.py
│ ├── test_epub_utils.py
│ └── test_text_cleaner.py
│
├── output/ # Generated files (gitignored)
│ ├── split/ # Split EPUB files
│ └── audio/ # Generated audio files
│
└── samples/ # Sample EPUB files for testing
└── .gitkeep
