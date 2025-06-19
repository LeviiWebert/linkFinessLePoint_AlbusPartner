"""
Script principal pour le matching des établissements de santé avec IA
Version modulaire et optimisée
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'service'))

from hospital_matcher import HospitalMatcher


def main():
    """
    Fonction principale du programme
    """
    print("🏥 === MATCHING D'ÉTABLISSEMENTS DE SANTÉ AVEC IA ===")
    print("Version modulaire - Optimisée pour Gemini 1.5 Flash")
    print("=" * 60)
    
    try:
        # Créer le matcher
        matcher = HospitalMatcher()
        
        # Charger les données
        matcher.load_data()
        
        # Traiter tous les hôpitaux
        matcher.process_all_hospitals()
        
        # Sauvegarder les résultats
        matcher.save_results()
        
        print("\n🎉 Traitement terminé avec succès!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Traitement interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
