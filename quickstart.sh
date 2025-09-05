#!/bin/bash
# Quick start script for TTS EPUB converter

set -e

echo "🚀 TTS EPUB Converter - Installation rapide"
echo "==========================================="

# Check Python version
echo "Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé!"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $python_version trouvé"

# Create virtual environment
echo ""
echo "Création de l'environnement virtuel..."
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
echo ""
echo "Mise à jour de pip..."
pip install --upgrade pip --quiet

# Install requirements
echo ""
echo "Installation des dépendances..."
pip install -r requirements.txt

# Create directories
echo ""
echo "Création des dossiers..."
mkdir -p output/split output/audio samples

# Copy env file
if [ ! -f .env ]; then
    echo "Configuration de l'environnement..."
    cp .env.example .env
fi

# Try to install Piper models
echo ""
echo "Téléchargement des modèles TTS français..."
piper --model fr_FR-upmc-medium --download-only 2>/dev/null || {
    echo "⚠️  Impossible de télécharger les modèles automatiquement."
    echo "   Vous devrez les installer manuellement avec:"
    echo "   piper --model fr_FR-upmc-medium --download-only"
}

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Pour commencer:"
echo "  1. Activez l'environnement: source venv/bin/activate"
echo "  2. Placez un fichier EPUB dans le dossier samples/"
echo "  3. Testez le découpage: python scripts/split_epub.py samples/votre_livre.epub --preview"
echo "  4. Convertissez en audio: python scripts/epub_to_audio.py samples/votre_livre.epub"
echo ""
echo "Commandes utiles:"
echo "  make help     - Voir toutes les commandes"
echo "  make preview FILE=livre.epub  - Prévisualiser les chapitres"
echo "  make run-split FILE=livre.epub - Découper en chapitres"
echo "  make run-audio FILE=livre.epub - Convertir en audio"