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

# Install base requirements
echo ""
echo "Installation des dépendances de base..."
pip install -r requirements.txt

# Try to install Piper separately
echo ""
echo "Installation de Piper TTS..."
echo "(Note: Si l'installation échoue, vous pouvez utiliser Edge-TTS comme alternative)"

# Method 1: Try with pip
pip install piper-tts 2>/dev/null && echo "✓ Piper installé via pip" || {
    echo "⚠️ Installation Piper par pip échouée."
    
    # Method 2: Check if piper is available system-wide
    if command -v piper &> /dev/null; then
        echo "✓ Piper trouvé dans le système"
    else
        echo ""
        echo "Piper n'a pas pu être installé automatiquement."
        echo ""
        echo "Options disponibles:"
        echo "1. Installer Piper manuellement:"
        echo "   - Ubuntu/Debian: sudo apt install piper"
        echo "   - Ou télécharger depuis: https://github.com/rhasspy/piper/releases"
        echo ""
        echo "2. Utiliser Edge-TTS (déjà installé) comme alternative"
        echo "   Edge-TTS est installé et peut être utilisé à la place de Piper"
    fi
}

# Create directories
echo ""
echo "Création des dossiers..."
mkdir -p output/split output/audio samples

# Copy env file
if [ ! -f .env ]; then
    echo "Configuration de l'environnement..."
    cp .env.example .env
fi

# Test available TTS
echo ""
echo "Test des moteurs TTS disponibles..."
echo "-----------------------------------"

if command -v piper &> /dev/null; then
    echo "✅ Piper disponible"
    echo "   Télécharger les modèles français avec:"
    echo "   piper --model fr_FR-upmc-medium --download-only"
else
    echo "❌ Piper non disponible"
fi

if python -c "import edge_tts" 2>/dev/null; then
    echo "✅ Edge-TTS disponible (alternative)"
    echo "   Voix françaises: fr-FR-HenriNeural, fr-FR-DeniseNeural"
else
    echo "❌ Edge-TTS non disponible"
fi

echo ""
echo "✅ Installation de base terminée!"
echo ""
echo "Pour commencer:"
echo "  1. Activez l'environnement: source venv/bin/activate"
echo "  2. Placez un fichier EPUB dans le dossier samples/"
echo "  3. Testez le découpage: python scripts/split_epub.py samples/votre_livre.epub --preview"
echo ""
echo "Si Piper n'est pas disponible:"
echo "  - Installez-le manuellement (voir instructions ci-dessus)"
echo "  - Ou utilisez Edge-TTS avec le script alternatif"
echo ""
echo "Commandes utiles:"
echo "  make help     - Voir toutes les commandes"
echo "  make preview FILE=livre.epub  - Prévisualiser les chapitres"
echo "  make run-split FILE=livre.epub - Découper en chapitres"