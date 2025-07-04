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


def get_user_choice():
    """
    Demande à l'utilisateur s'il souhaite reprendre l'historique ou recommencer
    """
    print("\n📋 OPTIONS DE TRAITEMENT:")
    print("1. Reprendre l'historique existant (recommandé)")
    print("2. Recommencer à zéro (efface l'historique)")
    print("3. Vérifier la configuration des fichiers")
    print("4. Quitter")
    
    while True:
        try:
            choice = input("\nVotre choix (1/2/3/4): ").strip()
            
            if choice == "1":
                print("✅ Reprise de l'historique existant...")
                return True
            elif choice == "2":
                confirm = input("⚠️  Êtes-vous sûr de vouloir recommencer à zéro? (oui/non): ").strip().lower()
                if confirm in ['oui', 'o', 'yes', 'y']:
                    print("🔄 Recommencement à zéro...")
                    return False
                else:
                    print("Annulé, retour au menu...")
                    continue
            elif choice == "3":
                verify_file_configuration()
                continue
            elif choice == "4":
                print("👋 Au revoir!")
                sys.exit(0)
            else:
                print("❌ Choix invalide. Veuillez entrer 1, 2, 3 ou 4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            sys.exit(0)


def verify_file_configuration():
    """
    Vérifie et confirme la configuration des fichiers avec l'utilisateur
    """
    from config import PATH_TABLE_A, PATH_TABLE_B, OUTPUT_PATH, COLA_NOM_HOPITAL, COLB_NOM, COLA_FINESS, COLB_FIN_SCS
    
    print("\n🔍 === VÉRIFICATION DE LA CONFIGURATION ===")
    print(f"📁 Fichier SOURCE (établissements à traiter): {PATH_TABLE_A}")
    print(f"📁 Fichier RÉFÉRENCE (contient les FINESS): {PATH_TABLE_B}")
    print(f"📁 Fichier RÉSULTAT: {OUTPUT_PATH}")
    
    print(f"\n📊 FLUX DE DONNÉES:")
    print(f"   SOURCE: Colonne '{COLA_NOM_HOPITAL}' → Recherche des FINESS")
    print(f"   RÉFÉRENCE: Colonnes '{COLB_NOM}' et '{COLB_FIN_SCS}' → Fournit les FINESS")
    print(f"   RÉSULTAT: Ajoute colonne '{COLA_FINESS}' au fichier source")
    
    print(f"\n💡 LOGIQUE:")
    print(f"   Pour chaque établissement du fichier SOURCE,")
    print(f"   on cherche dans le fichier RÉFÉRENCE l'établissement correspondant")
    print(f"   et on récupère son numéro FINESS.")
    
    while True:
        confirm = input("\n❓ Cette configuration est-elle correcte? (oui/non/inverser): ").strip().lower()
        
        if confirm in ['oui', 'o', 'yes', 'y']:
            print("✅ Configuration confirmée")
            break
        elif confirm in ['non', 'n', 'no']:
            print("❌ Veuillez modifier le fichier config.py selon vos besoins")
            sys.exit(0)
        elif confirm in ['inverser', 'inv', 'i']:
            suggest_file_inversion()
            break
        else:
            print("Répondez par 'oui', 'non' ou 'inverser'")


def suggest_file_inversion():
    """
    Propose d'inverser les fichiers si l'utilisateur le souhaite
    """
    print("\n🔄 INVERSION DES FICHIERS:")
    print("Pour inverser les rôles des fichiers, modifiez dans config.py:")
    print("PATH_TABLE_A = votre fichier de référence (qui contient les FINESS)")
    print("PATH_TABLE_B = votre fichier à traiter (où ajouter les FINESS)")
    print("\nEt ajustez les noms de colonnes en conséquence.")
    
    input("\nAppuyez sur Entrée pour continuer...")
    sys.exit(0)


def main():
    """
    Fonction principale du programme
    """
    print("🏥 === MATCHING D'ÉTABLISSEMENTS DE SANTÉ AVEC IA ===")
    print("Version modulaire - Optimisée pour Gemini 1.5 Flash")
    print("=" * 60)
    
    # Demander à l'utilisateur s'il souhaite reprendre l'historique
    use_history = get_user_choice()
    
    try:
        # Créer le matcher avec le choix de l'utilisateur
        # use_history = True signifie reprendre l'historique
        # use_history = False signifie recommencer à zéro (reset_history = True)
        matcher = HospitalMatcher(reset_history=not use_history)
        
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
