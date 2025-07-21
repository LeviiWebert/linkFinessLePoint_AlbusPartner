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
    print("4. Changer le niveau de matching fuzzy")
    print("5. Quitter")
    
    while True:
        try:
            choice = input("\nVotre choix (1/2/3/4/5): ").strip()
            
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
                choose_fuzzy_level()
                continue
            elif choice == "5":
                print("👋 Au revoir!")
                sys.exit(0)
            else:
                print("❌ Choix invalide. Veuillez entrer 1, 2, 3, 4 ou 5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            sys.exit(0)


def choose_fuzzy_level():
    """
    Permet de choisir le niveau de matching fuzzy
    """
    from config import FUZZY_LEVELS, FUZZY_LEVEL
    
    print("\n🎯 === NIVEAU DE MATCHING FUZZY ===")
    print("Choisissez le niveau de strictness pour le matching des noms :")
    print()
    
    # Afficher les options disponibles
    options = list(FUZZY_LEVELS.keys())
    for i, level in enumerate(options, 1):
        info = FUZZY_LEVELS[level]
        current = " (ACTUEL)" if level == FUZZY_LEVEL else ""
        print(f"{i}. {info['description']} - Seuil: {info['threshold']}%{current}")
    
    print()
    print("💡 Plus le seuil est élevé, plus le matching est strict")
    print("   - Seuil élevé = moins de matches, mais plus précis")
    print("   - Seuil bas = plus de matches, mais plus de faux positifs")
    
    while True:
        try:
            choice = input(f"\nVotre choix (1-{len(options)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(options):
                selected_level = options[choice_num - 1]
                selected_info = FUZZY_LEVELS[selected_level]
                
                print(f"✅ Niveau sélectionné: {selected_info['description']}")
                print(f"   Seuil: {selected_info['threshold']}%")
                
                # Mettre à jour la configuration
                update_config_file("FUZZY_LEVEL", f'"{selected_level}"')
                print("ℹ️  Redémarrez le script pour appliquer les changements")
                break
            else:
                print(f"❌ Choix invalide. Entrez un nombre entre 1 et {len(options)}.")
                
        except ValueError:
            print("❌ Veuillez entrer un nombre valide.")
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            sys.exit(0)


def update_config_file(param_name, value):
    """
    Met à jour un paramètre dans le fichier config.py
    """
    try:
        import os
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
        
        # Lire le fichier
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Chercher et modifier la ligne
        for i, line in enumerate(lines):
            if line.startswith(f"{param_name} ="):
                lines[i] = f"{param_name} = {value}  # Modifié automatiquement\n"
                break
        
        # Réécrire le fichier
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        print(f"✅ Paramètre {param_name} mis à jour: {value}")
        
    except Exception as e:
        print(f"❌ Erreur mise à jour config: {e}")
        print(f"📝 Modifiez manuellement {param_name} = {value} dans config.py")


def verify_file_configuration():
    """
    Vérifie et confirme la configuration des fichiers avec l'utilisateur
    """
    import pandas as pd
    from config import PATH_TABLE_A, PATH_TABLE_B, OUTPUT_PATH, COLA_NOM_HOPITAL, COLB_NOM, COLA_FINESS, COLB_FIN_SCS
    
    print("\n🔍 === VÉRIFICATION DE LA CONFIGURATION ===")
    print(f"📁 Fichier SOURCE (établissements à traiter): {PATH_TABLE_A}")
    print(f"📁 Fichier RÉFÉRENCE (contient les FINESS): {PATH_TABLE_B}")
    print(f"📁 Fichier RÉSULTAT: {OUTPUT_PATH}")
    
    # Vérifier les colonnes réelles des fichiers
    try:
        df_source = pd.read_excel(PATH_TABLE_A, nrows=1)
        df_reference = pd.read_excel(PATH_TABLE_B, nrows=1)
        
        print(f"\n� COLONNES DISPONIBLES:")
        print(f"   SOURCE: {list(df_source.columns)}")
        print(f"   RÉFÉRENCE: {list(df_reference.columns)}")
        
        print(f"\n📊 CONFIGURATION ACTUELLE:")
        print(f"   SOURCE: Colonne '{COLA_NOM_HOPITAL}' → Recherche des FINESS")
        print(f"   RÉFÉRENCE: Colonnes '{COLB_NOM}' et '{COLB_FIN_SCS}' → Fournit les FINESS")
        print(f"   RÉSULTAT: Ajoute colonne '{COLA_FINESS}' au fichier source")
        
        # Vérifier si les colonnes configurées existent
        if COLA_NOM_HOPITAL not in df_source.columns:
            print(f"⚠️  ATTENTION: Colonne '{COLA_NOM_HOPITAL}' introuvable dans le fichier source!")
            print(f"   Colonnes disponibles: {list(df_source.columns)}")
        
        if COLB_NOM not in df_reference.columns:
            print(f"⚠️  ATTENTION: Colonne '{COLB_NOM}' introuvable dans le fichier référence!")
            
    except Exception as e:
        print(f"❌ Erreur lecture fichiers: {e}")
    
    print(f"\n💡 LOGIQUE:")
    print(f"   Pour chaque établissement du fichier SOURCE,")
    print(f"   on cherche dans le fichier RÉFÉRENCE l'établissement correspondant")
    print(f"   et on récupère son numéro FINESS.")
    
    while True:
        confirm = input("\n❓ Cette configuration est-elle correcte? (oui/non/inverser/corriger): ").strip().lower()
        
        if confirm in ['oui', 'o', 'yes', 'y']:
            print("✅ Configuration confirmée")
            break
        elif confirm in ['corriger', 'c', 'fix']:
            print("\n🔧 CORRECTION DE LA CONFIGURATION:")
            print("Pour corriger, modifiez le fichier config.py")
            print("Section STATIC_CONFIG:")
            print("- COLA_NOM_HOPITAL: nom de la colonne dans le fichier source")
            print("- COLB_NOM: nom de la colonne dans le fichier référence")
            input("Appuyez sur Entrée après correction...")
            break
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


def choose_establishment_type_handling():
    """
    Demande à l'utilisateur comment il veut gérer les types d'établissements
    """
    print("\n🏥 === GESTION DES TYPES D'ÉTABLISSEMENTS ===")
    print("Comment voulez-vous traiter les types d'établissements dans le matching ?")
    print()
    print("1. Ignorer les types (traiter tous les établissements de la même façon)")
    print("2. Différencier hôpitaux et cliniques (matching plus précis)")
    print("3. Forcer un type spécifique (tous considérés comme hôpitaux)")
    print("4. Forcer un type spécifique (tous considérés comme cliniques)")
    
    while True:
        try:
            choice = input("\nVotre choix (1/2/3/4): ").strip()
            
            if choice == "1":
                print("✅ Types d'établissements ignorés - matching universel")
                return False, None
            elif choice == "2":
                print("✅ Différenciation hôpitaux/cliniques activée")
                return True, None
            elif choice == "3":
                print("✅ Tous les établissements traités comme des hôpitaux")
                return True, "hopital"
            elif choice == "4":
                print("✅ Tous les établissements traités comme des cliniques")
                return True, "clinique"
            else:
                print("❌ Choix invalide. Veuillez entrer 1, 2, 3 ou 4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            sys.exit(0)


def main():
    """
    Fonction principale du programme
    """
    print("🏥 === MATCHING D'ÉTABLISSEMENTS DE SANTÉ AVEC IA ===")
    print("Version modulaire - Optimisée pour Gemini 2.5 Flash")
    print("=" * 60)
    
    # Afficher la configuration actuelle
    from config import FUZZY_LEVEL, FUZZY_LEVELS, FUZZY_THRESHOLD
    fuzzy_info = FUZZY_LEVELS[FUZZY_LEVEL]
    print(f"🎯 Niveau de matching fuzzy: {fuzzy_info['description']} (Seuil: {FUZZY_THRESHOLD}%)")
    
    # Demander à l'utilisateur s'il souhaite reprendre l'historique
    use_history = get_user_choice()
    
    # Choix de la gestion des types d'établissements
    differentiate_types, forced_type = choose_establishment_type_handling()
    
    try:
        # Créer le matcher avec le choix de l'utilisateur
        # use_history = True signifie reprendre l'historique
        # use_history = False signifie recommencer à zéro (reset_history = True)
        matcher = HospitalMatcher(reset_history=not use_history, differentiate_types=differentiate_types, forced_type=forced_type)
        
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
