.PHONY: help install test lint format clean run-split run-audio

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	. $(VENV)/bin/activate && $(PIP) install -r requirements.txt
	@echo "✓ Installation complete. Activate venv with: source $(VENV)/bin/activate"

install-piper: ## Install Piper TTS models
	@echo "Downloading French models for Piper..."
	. $(VENV)/bin/activate && piper --model fr_FR-upmc-medium --download-only
	. $(VENV)/bin/activate && piper --model fr_FR-siwis-medium --download-only
	@echo "✓ Piper models downloaded"

test: ## Run tests
	. $(VENV)/bin/activate && pytest tests/ -v --cov=lib --cov-report=term-missing

lint: ## Run code linting
	. $(VENV)/bin/activate && ruff check .
	. $(VENV)/bin/activate && mypy lib/

format: ## Format code
	. $(VENV)/bin/activate && black lib/ scripts/ tests/
	. $(VENV)/bin/activate && ruff check --fix .

clean: ## Clean generated files
	rm -rf output/split/*.epub
	rm -rf output/audio/*.wav
	rm -rf output/audio/*.mp3
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Script runners
run-split: ## Split EPUB (usage: make run-split FILE=book.epub)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=path/to/book.epub"; \
		exit 1; \
	fi
	. $(VENV)/bin/activate && python scripts/split_epub.py "$(FILE)"

run-audio: ## Convert EPUB to audio (usage: make run-audio FILE=book.epub)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=path/to/book.epub"; \
		exit 1; \
	fi
	. $(VENV)/bin/activate && python scripts/epub_to_audio.py "$(FILE)"

run-batch-audio: ## Convert all split EPUBs to audio
	. $(VENV)/bin/activate && python scripts/epub_to_audio.py output/split/*.epub

preview: ## Preview EPUB chapters (usage: make preview FILE=book.epub)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=path/to/book.epub"; \
		exit 1; \
	fi
	. $(VENV)/bin/activate && python scripts/split_epub.py "$(FILE)" --preview

demo: ## Run full demo pipeline
	@echo "Running demo pipeline..."
	@echo "1. Splitting sample EPUB..."
	. $(VENV)/bin/activate && python scripts/split_epub.py samples/*.epub --min-words 50
	@echo "2. Converting first chapter to audio..."
	. $(VENV)/bin/activate && python scripts/epub_to_audio.py output/split/*.epub | head -1
	@echo "✓ Demo complete! Check output/ directory"