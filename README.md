# TTS Scripts - EPUB to Audio Converter

Scripts Python pour découper des fichiers EPUB en chapitres et les convertir en audio avec TTS.

## 🚀 Installation rapide

```bash
# Cloner le repo et installer
git clone <your-repo>
cd tts-scripts
make install

# Installer les modèles Piper
make install-piper
```

## 📖 Usage

### 1. Découper un EPUB en chapitres

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Prévisualiser les chapitres
python scripts/split_epub.py mon_livre.epub --preview

# Découper en fichiers séparés
python scripts/split_epub.py mon_livre.epub

# Avec options
python scripts/split_epub.py mon_livre.epub \
    --output-dir ./chapitres \
    --min-words 200
```

### 2. Convertir EPUB en audio

```bash
# Convertir un seul fichier
python scripts/epub_to_audio.py mon_livre.epub

# Convertir plusieurs fichiers
python scripts/epub_to_audio.py chapitre1.epub chapitre2.epub

# Avec options personnalisées
python scripts/epub_to_audio.py mon_livre.epub \
    --model fr_FR-upmc-medium \
    --format mp3 \
    --speed 1.2 \
    --combine-chapters
```

### 3. Pipeline complet

```bash
# 1. Découper le livre
python scripts/split_epub.py livre.epub

# 2. Convertir tous les chapitres
python scripts/epub_to_audio.py output/split/*.epub
```

## 🎯 Commandes Make

```bash
make help           # Afficher l'aide
make install        # Installer les dépendances
make install-piper  # Télécharger les modèles TTS
make test          # Lancer les tests
make lint          # Vérifier le code
make format        # Formater le code
make clean         # Nettoyer les fichiers générés

# Avec fichier
make run-split FILE=livre.epub
make run-audio FILE=livre.epub
make preview FILE=livre.epub
```

## ⚙️ Configuration

Créer un fichier `.env` depuis le template :

```bash
cp .env.example .env
```

Variables disponibles :

- `TTS_MODEL` : Modèle Piper à utiliser (fr_FR-upmc-medium)
- `TTS_VOICE_SPEED` : Vitesse de la voix (1.0 = normale)
- `AUDIO_FORMAT` : Format de sortie (wav/mp3)
- `CHUNK_SIZE` : Taille des blocs de texte pour TTS
- `MIN_CHAPTER_LENGTH` : Nombre minimum de mots par chapitre

## 📁 Structure des sorties

```
output/
├── split/          # EPUBs découpés
│   ├── livre_chapter_001_Introduction.epub
│   ├── livre_chapter_002_Chapitre1.epub
│   └── ...
└── audio/          # Fichiers audio générés
    ├── livre_chapter_001_Introduction.wav
    ├── livre_chapter_002_Chapitre1.wav
    └── ...
```

## 🔊 Modèles TTS disponibles

### Français

- `fr_FR-upmc-medium` : Voix masculine, qualité moyenne (recommandé)
- `fr_FR-siwis-medium` : Voix alternative
- `fr_FR-tom-medium` : Voix Tom
- `fr_FR-gilles-low` : Voix Gilles, qualité basse mais rapide

### Installation d'autres modèles

```bash
# Lister les modèles disponibles
piper --list-models | grep fr_FR

# Télécharger un modèle
piper --model fr_FR-tom-medium --download-only
```

## 🐛 Dépannage

### Piper non trouvé

```bash
pip install piper-tts
# ou
pip install piper-tts[gpu]  # Pour support GPU
```

### Erreur de modèle

```bash
# Réinstaller le modèle
rm -rf ~/.local/share/piper/
make install-piper
```

### Mémoire insuffisante

Réduire `CHUNK_SIZE` dans `.env` :

```env
CHUNK_SIZE=2000  # Au lieu de 5000
```

## 📝 Exemples de scripts personnalisés

### Convertir un dossier entier

```bash
#!/bin/bash
for epub in ~/Books/*.epub; do
    echo "Processing: $epub"
    python scripts/split_epub.py "$epub"
    python scripts/epub_to_audio.py output/split/*.epub \
        --format mp3 \
        --speed 1.1
    # Nettoyer les splits
    rm output/split/*.epub
done
```

### Conversion batch avec voix différentes

```python
#!/usr/bin/env python3
import subprocess
from pathlib import Path

models = {
    "narrator": "fr_FR-upmc-medium",
    "character": "fr_FR-siwis-medium"
}

for chapter in Path("output/split").glob("*.epub"):
    model = models["narrator"] if "narration" in chapter.name else models["character"]
    subprocess.run([
        "python", "scripts/epub_to_audio.py",
        str(chapter),
        "--model", model
    ])
```

## 🚧 Roadmap

- [ ] Support multi-threading pour conversion batch
- [ ] Interface web simple
- [ ] Support d'autres formats (PDF, DOCX)
- [ ] Post-processing audio (normalisation, compression)
- [ ] Détection automatique de la langue
- [ ] Voix multiples par personnage

## 📄 Licence

MIT
