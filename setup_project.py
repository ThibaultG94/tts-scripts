#!/usr/bin/env python3
"""Setup script to create project structure and __init__ files."""

from pathlib import Path

# Create necessary directories and __init__.py files
directories = [
    "lib",
    "config", 
    "scripts",
    "tests",
    "output",
    "output/split",
    "output/audio",
    "samples"
]

for dir_path in directories:
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py for Python packages
    if dir_path in ["lib", "config", "scripts", "tests"]:
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Package initialization."""\n')
            print(f"✓ Created {init_file}")

# Create .gitkeep files for empty directories
for dir_path in ["output", "output/split", "output/audio", "samples"]:
    gitkeep = Path(dir_path) / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("")
        print(f"✓ Created {gitkeep}")

print("\n✅ Project structure setup complete!")
print("\nNow you can run:")
print("  python scripts/split_epub.py <your_epub_file> --preview")
print("  python scripts/epub_to_audio_edge.py <your_epub_file>")
