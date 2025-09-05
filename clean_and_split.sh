#!/bin/bash
# Script to clean old files and re-split EPUB with better logic

echo "🧹 Nettoyage et re-découpage intelligent"
echo "========================================="

# Check if EPUB file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <fichier.epub>"
    echo "Exemple: $0 'La Cite des Dames - Christine de Pizan.epub'"
    exit 1
fi

EPUB_FILE="$1"

# Check if file exists
if [ ! -f "$EPUB_FILE" ]; then
    echo "❌ Fichier non trouvé: $EPUB_FILE"
    exit 1
fi

echo ""
echo "📚 Fichier: $EPUB_FILE"
echo ""

# Clean old split files
echo "🗑️  Suppression des anciens fichiers..."
rm -f output/split/*.epub
echo "✓ Dossier split nettoyé"

echo ""
echo "✂️  Découpage intelligent en cours..."
echo "------------------------------------"

# Run the split with the improved script
python scripts/split_epub.py "$EPUB_FILE"

echo ""
echo "📊 Résultat du découpage:"
echo "------------------------"

# Count and list files
if [ -d "output/split" ]; then
    FILE_COUNT=$(ls -1 output/split/*.epub 2>/dev/null | wc -l)
    
    if [ "$FILE_COUNT" -gt 0 ]; then
        echo "✅ $FILE_COUNT fichiers créés:"
        echo ""
        ls -lh output/split/*.epub | awk '{print "  • " $9 " (" $5 ")"}'
        
        echo ""
        echo "Les fichiers sont maintenant numérotés de façon cohérente:"
        echo "  - ch001, ch002, ch003... pour une lecture séquentielle"
        echo "  - Les sections non-textuelles ont été ignorées"
        echo ""
        echo "Prochaine étape:"
        echo "  python scripts/epub_to_audio_edge.py output/split/ch001*.epub --voice henri"
    else
        echo "⚠️  Aucun fichier créé. Vérifiez les erreurs ci-dessus."
    fi
else
    echo "❌ Le dossier output/split n'existe pas!"
fi