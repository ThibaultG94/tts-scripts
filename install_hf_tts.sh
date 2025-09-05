#!/bin/bash
# Script to install HuggingFace TTS dependencies

echo "📦 Installation des dépendances HuggingFace TTS"
echo "=============================================="

# Activate venv if not already
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

echo ""
echo "Installation des packages nécessaires..."
echo "Cela peut prendre quelques minutes..."

# Install PyTorch (CPU version, lighter)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install transformers and scipy
pip install transformers scipy

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Test rapide avec le modèle Facebook MMS French:"
echo "------------------------------------------------"

# Create a test script
cat > test_hf_tts.py << 'EOF'
from transformers import VitsModel, VitsTokenizer
import torch

print("Chargement du modèle...")
try:
    tokenizer = VitsTokenizer.from_pretrained("facebook/mms-tts-fra")
    model = VitsModel.from_pretrained("facebook/mms-tts-fra")
    print("✅ Modèle chargé avec succès!")
    print("Le modèle est prêt à être utilisé.")
except Exception as e:
    print(f"❌ Erreur: {e}")
EOF

python test_hf_tts.py

echo ""
echo "Commandes disponibles:"
echo "----------------------"
echo ""
echo "1. Tester avec un chapitre court:"
echo "   python scripts/epub_to_audio_hf.py output/split/*chapter_000_Sommaire.epub"
echo ""
echo "2. Convertir plusieurs chapitres:"
echo "   python scripts/epub_to_audio_hf.py output/split/*.epub"
echo ""
echo "3. Mode dry-run (test sans créer de fichiers):"
echo "   python scripts/epub_to_audio_hf.py output/split/*chapter_000_Sommaire.epub --dry-run"
echo ""
echo "Note: Le premier lancement téléchargera le modèle (~500MB), soyez patient!"