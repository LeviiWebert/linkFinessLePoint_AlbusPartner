"""
Script de test pour le prompt interactif
"""

import sys
import os

# Ajouter les chemins pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'main'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from main.main import get_user_choice


def test_interactive_prompt():
    """
    Test du prompt interactif
    """
    print("🧪 TEST DU PROMPT INTERACTIF")
    print("=" * 40)
    
    try:
        # Simuler le choix de l'utilisateur
        choice = get_user_choice()
        
        if choice:
            print("✅ Test réussi: L'utilisateur a choisi de reprendre l'historique")
        else:
            print("✅ Test réussi: L'utilisateur a choisi de recommencer à zéro")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")


if __name__ == "__main__":
    test_interactive_prompt()
