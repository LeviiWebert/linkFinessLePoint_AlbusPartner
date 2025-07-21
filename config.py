"""
Configuration adaptable pour le matching des établissements de santé
"""
import pandas as pd
import os

# ========== CONFIGURATION PRINCIPALE ==========

# Chemins des fichiers
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\Data_ref\Data-FINESS_Modele.xlsx"
PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\classement ehpad\ClassementNouvelOBS_Complet.xlsx"
OUTPUT_PATH = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finess_emeis-SCS-clinique-V2.xlsx"

# ========== GESTION DE L'HISTORIQUE ==========
RESET_HISTORY = True  # True = recommencer à zéro, False = continuer
CREATE_NEW_OUTPUT = True  # True = nouveau fichier avec timestamp

# ========== GESTION DU TYPE D'ÉTABLISSEMENT ==========
USE_ESTABLISHMENT_TYPE = False  # True = différencier hôpital/clinique, False = ignorer les types
FORCE_ESTABLISHMENT_TYPE = None  # None, "hopital", "clinique" - Force un type spécifique si USE_ESTABLISHMENT_TYPE=True

# ========== PARAMÈTRES DE MATCHING FUZZY ==========
# Niveaux de match fuzzy prédéfinis
FUZZY_LEVELS = {
    "tres_strict": {"threshold": 95, "description": "Très strict - Correspondance quasi-parfaite uniquement"},
    "strict": {"threshold": 90, "description": "Strict - Correspondance très proche"},
    "normal": {"threshold": 85, "description": "Normal - Bon équilibre précision/rappel"},
    "permissif": {"threshold": 80, "description": "Permissif - Plus de correspondances acceptées"},
    "tres_permissif": {"threshold": 75, "description": "Très permissif - Accepte les correspondances approximatives"}
}

# Niveau par défaut (peut être modifié par l'utilisateur)
FUZZY_LEVEL = "tres_permissif"  # Choix: "tres_strict", "strict", "normal", "permissif", "tres_permissif"

# ========== AUTO-DÉTECTION DES COLONNES ==========

# Mode de configuration des colonnes
COLUMN_CONFIG_MODE = "interactive"  # "auto", "manual", "interactive"

# Définir les colonnes possibles pour chaque type de données
POSSIBLE_COLUMNS = {
    # Table A - Établissement à rechercher
    "nom_etablissement": [
        "Nom de l'Ehpad","Nom de la clinique", "Nom_Hopital", "Nom hopital", "Nom clinique", 
        "Libelle_Sans_Rang", "Nom", "NomEtablissement", "Etablissement"
    ],
    "ville": [
        "Ville", "VILLE", "Commune", "COMMUNE", "City", "Localite"
    ],
    "departement": [
        "Departement", "DEPARTEMENT", "Dept", "DEPT", "Department", "Dep"
    ],
    "finess": [
        "FINESS", "Finess", "CodeFINESS", "Code_FINESS", "FinessNumber"
    ],
    
    # Table B - Référence
    "nom_reference": [
        "Nom", "NomScanSante", "Nom_SC", "Name", "Denomination", "Libelle"
    ],
    "nom2_reference": [
        "Nom2", "Nom_2", "SecondName", "AliasName", "NomAlternatif"
    ],
    "ville_reference": [
        "Ville", "VILLE", "Commune", "COMMUNE", "City", "Localite"
    ],
    "departement_reference": [
        "Departement", "DEPARTEMENT", "Dept", "DEPT", "Department", "Dep"
    ],
    "finess_reference": [
        "FINESS", "Finess", "FINESSSCANSANTE", "CodeFINESS", "Code_FINESS"
    ]
}

def auto_detect_columns(df, column_type):
    """
    Détecte automatiquement les colonnes dans un DataFrame
    """
    possible_names = POSSIBLE_COLUMNS.get(column_type, [])
    available_columns = df.columns.tolist()
    
    # D'abord chercher une correspondance exacte
    for possible_name in possible_names:
        if possible_name in available_columns:
            return possible_name
    
    # Ensuite chercher par similarité (case insensitive)
    for possible_name in possible_names:
        for col in available_columns:
            if (possible_name.lower() == col.lower() or 
                possible_name.lower() in col.lower() or 
                col.lower() in possible_name.lower()):
                return col
    
    # Debug: afficher les colonnes disponibles si rien n'est trouvé
    print(f"⚠️  Colonne '{column_type}' non trouvée. Colonnes disponibles: {available_columns}")
    return None

def interactive_column_choice(df, column_type, description):
    """
    Permet à l'utilisateur de choisir interactivement une colonne
    """
    print(f"\n📋 Sélection de colonne pour: {description}")
    print("Colonnes disponibles dans le fichier:")
    
    columns = df.columns.tolist()
    for i, col in enumerate(columns, 1):
        print(f"  {i}. {col}")
    
    # Proposer auto-détection
    auto_detected = auto_detect_columns(df, column_type)
    if auto_detected:
        print(f"\n🤖 Auto-détection suggère: '{auto_detected}'")
        print("Voulez-vous utiliser cette suggestion ?")
        print("1. Oui, utiliser la suggestion")
        print("2. Non, choisir manuellement")
        
        choice = input("Votre choix (1-2): ").strip()
        if choice == "1":
            return auto_detected
    
    # Choix manuel
    while True:
        try:
            choice = input(f"\nChoisissez le numéro de colonne pour '{description}' (1-{len(columns)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(columns):
                    selected = columns[idx]
                    print(f"✅ Colonne sélectionnée: '{selected}'")
                    return selected
            print("❌ Choix invalide, veuillez réessayer.")
        except (ValueError, KeyboardInterrupt):
            print("❌ Choix invalide, veuillez réessayer.")

def configure_columns_interactively(path_a, path_b, sheet_a="Sheet1", sheet_b="Sheet1"):
    """
    Configuration interactive complète des colonnes
    """
    print("\n" + "="*60)
    print("🎯 CONFIGURATION INTERACTIVE DES COLONNES")
    print("="*60)
    
    try:
        # Charger les fichiers
        print("📂 Chargement des fichiers...")
        df_a = pd.read_excel(path_a, sheet_name=sheet_a, nrows=5)
        df_b = pd.read_excel(path_b, sheet_name=sheet_b, nrows=5)
        
        config = {}
        
        print(f"\n📊 TABLE A: {os.path.basename(path_a)}")
        print("-" * 40)
        
        # Configuration Table A
        config["COLA_NOM_HOPITAL"] = interactive_column_choice(
            df_a, "nom_etablissement", "Nom de l'établissement/hôpital/clinique"
        )
        
        config["COLA_VILLE"] = interactive_column_choice(
            df_a, "ville", "Ville de l'établissement"
        )
        
        print("\nColonnes optionnelles (appuyez sur Entrée pour ignorer):")
        
        # Département (optionnel)
        print(f"\n🏢 Département (optionnel):")
        auto_dept = auto_detect_columns(df_a, "departement")
        if auto_dept:
            use_dept = input(f"Utiliser '{auto_dept}' pour le département ? (o/n): ").strip().lower()
            if use_dept in ['o', 'oui', 'y', 'yes']:
                config["COLA_DEPARTEMENT"] = auto_dept
            else:
                config["COLA_DEPARTEMENT"] = None
        else:
            config["COLA_DEPARTEMENT"] = None
            
        # FINESS (optionnel)
        print(f"\n🏥 Code FINESS (optionnel):")
        auto_finess = auto_detect_columns(df_a, "finess")
        if auto_finess:
            use_finess = input(f"Utiliser '{auto_finess}' pour le code FINESS ? (o/n): ").strip().lower()
            if use_finess in ['o', 'oui', 'y', 'yes']:
                config["COLA_FINESS"] = auto_finess
            else:
                config["COLA_FINESS"] = None
        else:
            config["COLA_FINESS"] = None
        
        print(f"\n📊 TABLE B: {os.path.basename(path_b)}")
        print("-" * 40)
        
        # Configuration Table B
        config["COLB_NOM_SC"] = interactive_column_choice(
            df_b, "nom_reference", "Nom principal de référence"
        )
        
        config["COLB_VILLE"] = interactive_column_choice(
            df_b, "ville_reference", "Ville de référence"
        )
        
        # Nom secondaire (optionnel)
        print(f"\n📝 Nom secondaire/alternatif (optionnel):")
        auto_nom2 = auto_detect_columns(df_b, "nom2_reference")
        if auto_nom2:
            use_nom2 = input(f"Utiliser '{auto_nom2}' comme nom alternatif ? (o/n): ").strip().lower()
            if use_nom2 in ['o', 'oui', 'y', 'yes']:
                config["COLB_NOM_2"] = auto_nom2
            else:
                config["COLB_NOM_2"] = None
        else:
            config["COLB_NOM_2"] = None
        
        # Dupliquer nom principal si pas de nom2
        config["COLB_NOM"] = config["COLB_NOM_SC"]
        
        # Département référence (optionnel)
        auto_dept_ref = auto_detect_columns(df_b, "departement_reference")
        if auto_dept_ref:
            use_dept_ref = input(f"Utiliser '{auto_dept_ref}' pour le département de référence ? (o/n): ").strip().lower()
            if use_dept_ref in ['o', 'oui', 'y', 'yes']:
                config["COLB_DEPARTEMENT"] = auto_dept_ref
            else:
                config["COLB_DEPARTEMENT"] = None
        else:
            config["COLB_DEPARTEMENT"] = None
            
        # FINESS référence (optionnel)
        auto_finess_ref = auto_detect_columns(df_b, "finess_reference")
        if auto_finess_ref:
            use_finess_ref = input(f"Utiliser '{auto_finess_ref}' pour le FINESS de référence ? (o/n): ").strip().lower()
            if use_finess_ref in ['o', 'oui', 'y', 'yes']:
                config["COLB_FIN_SCS"] = auto_finess_ref
            else:
                config["COLB_FIN_SCS"] = None
        else:
            config["COLB_FIN_SCS"] = None
        
        print("\n" + "="*60)
        print("✅ CONFIGURATION TERMINÉE")
        print("="*60)
        print("Résumé de votre configuration:")
        for key, value in config.items():
            if value:
                print(f"  {key}: '{value}'")
            else:
                print(f"  {key}: Non utilisé")
        
        confirm = input("\nConfirmer cette configuration ? (o/n): ").strip().lower()
        if confirm in ['o', 'oui', 'y', 'yes']:
            return config
        else:
            print("Configuration annulée.")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return None

def get_dynamic_config(path_a, path_b, sheet_a="Sheet1", sheet_b="Sheet1"):
    """
    Génère une configuration dynamique basée sur le mode choisi
    """
    if COLUMN_CONFIG_MODE == "interactive":
        print("🎯 Mode interactif activé - Configuration des colonnes")
        return configure_columns_interactively(path_a, path_b, sheet_a, sheet_b)
    
    elif COLUMN_CONFIG_MODE == "manual":
        print("✏️  Mode manuel - Utilisation de la configuration statique")
        return None  # Utilise STATIC_CONFIG
    
    else:  # COLUMN_CONFIG_MODE == "auto"
        print("🤖 Mode automatique - Détection des colonnes")
        return get_auto_config(path_a, path_b, sheet_a, sheet_b)

def get_auto_config(path_a, path_b, sheet_a="Sheet1", sheet_b="Sheet1"):
    """
    Configuration automatique (ancien comportement)
    """
    try:
        # Charger les données pour analyser les colonnes
        df_a = pd.read_excel(path_a, sheet_name=sheet_a, nrows=5)  # Juste quelques lignes pour l'analyse
        df_b = pd.read_excel(path_b, sheet_name=sheet_b, nrows=5)
        
        config = {
            # Colonnes Table A
            "COLA_NOM_HOPITAL": auto_detect_columns(df_a, "nom_etablissement"),
            "COLA_VILLE": auto_detect_columns(df_a, "ville"),
            "COLA_DEPARTEMENT": auto_detect_columns(df_a, "departement"),
            "COLA_FINESS": auto_detect_columns(df_a, "finess"),
            
            # Colonnes Table B
            "COLB_NOM_SC": auto_detect_columns(df_b, "nom_reference"),
            "COLB_NOM": auto_detect_columns(df_b, "nom_reference"),
            "COLB_NOM_2": auto_detect_columns(df_b, "nom2_reference"),
            "COLB_VILLE": auto_detect_columns(df_b, "ville_reference"),
            "COLB_DEPARTEMENT": auto_detect_columns(df_b, "departement_reference"),
            "COLB_FIN_SCS": auto_detect_columns(df_b, "finess_reference"),
        }
        
        # Vérifier que les colonnes essentielles sont trouvées
        essential_columns = ["COLA_NOM_HOPITAL", "COLA_VILLE", "COLB_NOM_SC", "COLB_VILLE"]
        missing = [col for col in essential_columns if config[col] is None]
        
        if missing:
            print(f"❌ Colonnes essentielles non trouvées: {missing}")
            print("📋 Colonnes disponibles Table A:", df_a.columns.tolist())
            print("📋 Colonnes disponibles Table B:", df_b.columns.tolist())
            return None
        
        print("✅ Configuration automatique générée:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        
        return config
        
    except Exception as e:
        print(f"❌ Erreur lors de l'auto-détection: {e}")
        return None

# ========== CONFIGURATION FINALE ==========

# Configuration statique (fallback)
STATIC_CONFIG = {
    "COLA_NOM_HOPITAL": "Nom de la clinique",
    "COLA_VILLE": "Ville",
    "COLA_DEPARTEMENT": "Departement",
    "COLA_FINESS": "FINESS",
    "COLB_NOM_SC": "Nom",
    "COLB_NOM": "Nom",
    "COLB_NOM_2": "Nom2",
    "COLB_VILLE": "Ville",
    "COLB_DEPARTEMENT": "Departement",
    "COLB_FIN_SCS": "FINESS",
}

# Générer la configuration finale
DYNAMIC_CONFIG = get_dynamic_config(PATH_TABLE_A, PATH_TABLE_B)
FINAL_CONFIG = DYNAMIC_CONFIG if DYNAMIC_CONFIG else STATIC_CONFIG

# Vérification supplémentaire : forcer la correction si la colonne détectée est incorrecte
def verify_and_fix_config():
    """Vérifie et corrige la configuration si nécessaire"""
    global FINAL_CONFIG
    try:
        df_a = pd.read_excel(PATH_TABLE_A, nrows=1)
        actual_columns = df_a.columns.tolist()
        
        # Si "Nom de l'Ehpad" existe mais qu'on a détecté autre chose
        if "Nom de l'Ehpad" in actual_columns and FINAL_CONFIG["COLA_NOM_HOPITAL"] != "Nom de l'Ehpad":
            print(f"🔧 Correction automatique: '{FINAL_CONFIG['COLA_NOM_HOPITAL']}' → 'Nom de l'Ehpad'")
            FINAL_CONFIG["COLA_NOM_HOPITAL"] = "Nom de l'Ehpad"
            
    except Exception as e:
        print(f"⚠️  Impossible de vérifier la configuration: {e}")

# Appliquer la vérification
verify_and_fix_config()

# Assigner les variables finales
COLA_NOM_HOPITAL = FINAL_CONFIG["COLA_NOM_HOPITAL"]
COLA_NOM_CLINIQUE = COLA_NOM_HOPITAL
COLA_VILLE = FINAL_CONFIG["COLA_VILLE"]
COLA_DEPARTEMENT = FINAL_CONFIG["COLA_DEPARTEMENT"]
COLA_FINESS = FINAL_CONFIG["COLA_FINESS"]
COLA_MATCH_NAME = "Nom_Match_Retenu"  # Nom de l'établissement qui a été matché
COLA_MATCH_CONFIDENCE = "Confiance_Match"  # Score de confiance du match

COLB_NOM_SC = FINAL_CONFIG["COLB_NOM_SC"]
COLB_NOM = FINAL_CONFIG["COLB_NOM"]
COLB_NOM_2 = FINAL_CONFIG["COLB_NOM_2"]
COLB_VILLE = FINAL_CONFIG["COLB_VILLE"]
COLB_DEPARTEMENT = FINAL_CONFIG["COLB_DEPARTEMENT"]
COLB_FIN_SCS = FINAL_CONFIG["COLB_FIN_SCS"]

# ========== AUTRES PARAMÈTRES ==========

# Gestion de l'historique et des fichiers de sortie
if CREATE_NEW_OUTPUT:
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(OUTPUT_PATH)[0]
    extension = os.path.splitext(OUTPUT_PATH)[1]
    OUTPUT_PATH = f"{base_name}_{timestamp}{extension}"

# Mots à remplacer pour le nettoyage
REPLACE = {"-": " ", " DE ": " ", " DU ": " ", "D'": " ", " DES ": " "}

# Configuration API
GOOGLE_API_KEY = "AIzaSyBfQjj1pNx0yDlXUSo4tdWUe5RcE35ON6o"
MODEL_NAME = "gemini-2.5-flash"

# Paramètres de matching fuzzy (utilise le niveau choisi)
FUZZY_THRESHOLD = FUZZY_LEVELS[FUZZY_LEVEL]["threshold"]

MAX_REQUESTS_PER_MINUTE = 50
TIME_WINDOW = 60
SAVE_INTERVAL = 10
