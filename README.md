# TTS Scripts - Convertisseur EPUB vers Audio

Convertit des livres EPUB en livres audio avec la synthèse vocale Piper TTS.

## 🚀 Installation rapide

```bash
# 1. Installer les dépendances
chmod +x quickstart.sh
./quickstart.sh

# 2. Installer Piper (binaire)
chmod +x install_hf_tts.sh
./install_hf_tts.sh

# 3. Activer l'environnement
source venv/bin/activate
```

## 📖 Usage

### Workflow complet

```bash
# 1. Découper un EPUB en chapitres
python scripts/split_epub.py "mon_livre.epub"

# 2. Convertir en audio (WAV)
python scripts/epub_to_audio.py output/split/*.epub --voice upmc

# 3. (Optionnel) Voir les chapitres avant conversion
python scripts/split_epub.py "mon_livre.epub" --preview
```

### Scripts disponibles

- `scripts/split_epub.py` : Découpe un EPUB en chapitres
- `scripts/epub_to_audio.py` : Convertit des EPUB en audio WAV
- `clean_and_split.sh` : Nettoie et re-découpe un EPUB

## 📁 Structure du projet

```
tts-scripts/
├── scripts/          # Scripts principaux
├── lib/              # Bibliothèques
│   ├── epub_utils.py     # Manipulation EPUB
│   ├── text_cleaner.py   # Nettoyage texte
│   └── piper_tts.py      # Moteur TTS
├── config/           # Configuration
├── voices/           # Modèles de voix
├── output/           # Fichiers générés
│   ├── split/       # EPUB découpés
│   └── audio/       # Fichiers audio
└── samples/         # Fichiers test

```

## 🎤 Voix disponibles

- **upmc** : Voix française masculine (recommandée)
- **siwis** : Voix alternative
- **tom** : Voix Tom
- **gilles** : Voix Gilles (rapide)
- **mls** : Voix MLS

## ⚙️ Configuration

Modifiez `.env` pour ajuster :
- `MIN_CHAPTER_LENGTH` : Mots minimum par chapitre (défaut: 100)
- `AUDIO_FORMAT` : Format de sortie (wav/mp3)

## 🐛 Résolution de problèmes

### Chapitres manquants
Réduisez `MIN_CHAPTER_LENGTH` ou utilisez `--min-words 50`

### Fichiers audio trop gros
Les WAV sont volumineux (~500MB/heure). Pour réduire :
```bash
# Convertir en MP3 après coup
for f in output/audio/*.wav; do
    ffmpeg -i "$f" -b:a 128k "${f%.wav}.mp3"
done
```

## 📄 Licence

MIT
