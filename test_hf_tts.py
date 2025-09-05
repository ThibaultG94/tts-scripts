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
