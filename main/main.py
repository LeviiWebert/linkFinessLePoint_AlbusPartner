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
    print("5. Mode TEST - Échantillon de 25 établissements avec logging détaillé")
    print("6. Quitter")
    
    while True:
        try:
            choice = input("\nVotre choix (1/2/3/4/5/6): ").strip()
            
            if choice == "1":
                print("✅ Reprise de l'historique existant...")
                return True, False
            elif choice == "2":
                confirm = input("⚠️  Êtes-vous sûr de vouloir recommencer à zéro? (oui/non): ").strip().lower()
                if confirm in ['oui', 'o', 'yes', 'y']:
                    print("🔄 Recommencement à zéro...")
                    return False, False
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
                print("🧪 Mode TEST activé - Échantillon aléatoire avec logging détaillé")
                return False, True  # reset=True, test_mode=True
            elif choice == "6":
                print("👋 Au revoir!")
                sys.exit(0)
            else:
                print("❌ Choix invalide. Veuillez entrer 1, 2, 3, 4, 5 ou 6.")
                
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
    from config import (PATH_TABLE_A, PATH_TABLE_B, OUTPUT_PATH, 
                       get_column_mapping, get_geo_comparison_strategy, 
                       get_finess_strategy, validate_configuration)
    
    print("\n🔍 === VÉRIFICATION DE LA CONFIGURATION ===")
    print(f"📁 Fichier SOURCE (établissements à traiter): {PATH_TABLE_A}")
    print(f"📁 Fichier RÉFÉRENCE (contient les FINESS): {PATH_TABLE_B}")
    print(f"📁 Fichier RÉSULTAT: {OUTPUT_PATH}")
    
    # Validation de la configuration
    validation = validate_configuration()
    if not validation["valid"]:
        print("\n❌ ERREURS DE CONFIGURATION:")
        for error in validation["errors"]:
            print(f"   • {error}")
        input("Appuyez sur Entrée pour continuer...")
        return
    
    if validation["warnings"]:
        print("\n⚠️  AVERTISSEMENTS:")
        for warning in validation["warnings"]:
            print(f"   • {warning}")
    
    # Afficher la configuration actuelle
    columns = get_column_mapping()
    geo_strategy = get_geo_comparison_strategy()
    finess_strategy = get_finess_strategy()
    
    print(f"\n📊 CONFIGURATION ACTUELLE:")
    print(f"   SOURCE: '{columns['source']['name']}' (noms) + '{columns['source']['city']}' (villes)")
    if columns['source']['department']:
        print(f"           + '{columns['source']['department']}' (départements)")
    
    print(f"   RÉFÉRENCE: '{columns['reference']['name_primary']}' (noms)")
    if columns['reference']['name_secondary']:
        print(f"              + '{columns['reference']['name_secondary']}' (noms alternatifs)")
    print(f"              + '{columns['reference']['city']}' (villes)")
    if columns['reference']['department']:
        print(f"              + '{columns['reference']['department']}' (départements)")
    
    print(f"\n🗺️  STRATÉGIE GÉOGRAPHIQUE:")
    if geo_strategy["city_only"]:
        print("   • Comparaison par VILLE uniquement")
    elif geo_strategy["department_only"]:
        print("   • Comparaison par DÉPARTEMENT uniquement")
    elif geo_strategy["both"]:
        print("   • Comparaison par VILLE ET DÉPARTEMENT")
    
    print(f"\n🏥 STRATÉGIE FINESS:")
    if finess_strategy["prefer_source"]:
        print("   • Source principale: TABLE SOURCE")
    else:
        print("   • Source principale: TABLE RÉFÉRENCE")
    
    if finess_strategy["has_source_finess"]:
        print(f"   • FINESS source: '{columns['source']['finess']}'")
    if finess_strategy["has_reference_finess"]:
        print(f"   • FINESS référence: '{columns['reference']['finess']}'")
    
    # Vérifier les colonnes réelles des fichiers
    try:
        df_source = pd.read_excel(PATH_TABLE_A, nrows=1)
        df_reference = pd.read_excel(PATH_TABLE_B, nrows=1)
        
        print(f"\n🔍 VÉRIFICATION DES COLONNES:")
        
        # Vérifier colonnes source
        missing_source = []
        for key, col in columns['source'].items():
            if col and col not in df_source.columns:
                missing_source.append(f"{key}: '{col}'")
        
        # Vérifier colonnes référence
        missing_ref = []
        for key, col in columns['reference'].items():
            if col and col not in df_reference.columns:
                missing_ref.append(f"{key}: '{col}'")
        
        if missing_source:
            print("   ❌ Colonnes manquantes dans SOURCE:")
            for missing in missing_source:
                print(f"      • {missing}")
        
        if missing_ref:
            print("   ❌ Colonnes manquantes dans RÉFÉRENCE:")
            for missing in missing_ref:
                print(f"      • {missing}")
        
        if not missing_source and not missing_ref:
            print("   ✅ Toutes les colonnes configurées sont présentes")
            
    except Exception as e:
        print(f"❌ Erreur lecture fichiers: {e}")
    
    print(f"\n💡 LOGIQUE:")
    print(f"   Pour chaque établissement du fichier SOURCE,")
    print(f"   on cherche dans le fichier RÉFÉRENCE l'établissement correspondant")
    if finess_strategy["has_reference_finess"]:
        print(f"   et on récupère son numéro FINESS.")
    else:
        print(f"   et on utilise le FINESS existant.")
    
    while True:
        confirm = input("\n❓ Cette configuration est-elle correcte? (oui/non/détails): ").strip().lower()
        
        if confirm in ['oui', 'o', 'yes', 'y']:
            print("✅ Configuration confirmée")
            break
        elif confirm in ['détails', 'd', 'details']:
            show_detailed_config()
            continue
        elif confirm in ['non', 'n', 'no']:
            print("❌ Veuillez relancer avec COLUMN_CONFIG_MODE = 'interactive' dans config.py")
            sys.exit(0)
        else:
            print("Répondez par 'oui', 'non' ou 'détails'")

def show_detailed_config():
    """
    Affiche la configuration détaillée
    """
    from config import (GEO_COMPARISON_TYPE, PRIMARY_FINESS_SOURCE, 
                       FUZZY_LEVEL, FUZZY_THRESHOLD, COLUMN_CONFIG_MODE)
    
    print("\n📋 === CONFIGURATION DÉTAILLÉE ===")
    print(f"Mode configuration: {COLUMN_CONFIG_MODE}")
    print(f"Type comparaison géo: {GEO_COMPARISON_TYPE}")
    print(f"Source FINESS primaire: {PRIMARY_FINESS_SOURCE}")
    print(f"Niveau fuzzy: {FUZZY_LEVEL} (seuil: {FUZZY_THRESHOLD}%)")
    print("="*40)

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
    from config import FUZZY_LEVEL, FUZZY_LEVELS, FUZZY_THRESHOLD, TEST_SAMPLE_SIZE
    fuzzy_info = FUZZY_LEVELS[FUZZY_LEVEL]
    print(f"🎯 Niveau de matching fuzzy: {fuzzy_info['description']} (Seuil: {FUZZY_THRESHOLD}%)")
    
    # Demander à l'utilisateur s'il souhaite reprendre l'historique
    use_history, test_mode = get_user_choice()
    
    # Choix de la gestion des types d'établissements
    differentiate_types, forced_type = choose_establishment_type_handling()
    
    try:
        # Créer le matcher avec le choix de l'utilisateur
        matcher = HospitalMatcher(reset_history=not use_history, differentiate_types=differentiate_types, forced_type=forced_type)
        
        # Activer le mode test si demandé
        if test_mode:
            from test_mode import create_test_hospital_matcher
            matcher = create_test_hospital_matcher(matcher, enable_test_mode=True, sample_size=TEST_SAMPLE_SIZE)
            print(f"🧪 Mode test activé - {TEST_SAMPLE_SIZE} établissements seront testés")
        
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
