"""
Configuration adaptable pour le matching des établissements de santé
"""
import pandas as pd
import os

# ========== CONFIGURATION PRINCIPALE ==========

# Chemins des fichiers
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\Data_ref\Data-FINESS_Modele.xlsx"
PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\Emeis\Scrapping_emeis\emeis_ehpad_results.xlsx"
OUTPUT_PATH = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finess_emeis-EHPAD-V2.xlsx"

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
COLUMN_CONFIG_MODE = "auto"  # "auto", "manual", "interactive"

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
    Configuration interactive flexible des colonnes - choix des comparaisons
    """
    print("\n" + "="*60)
    print("🎯 CONFIGURATION INTERACTIVE DES COLONNES")
    print("="*60)
    
    try:
        # Charger les fichiers
        print("📂 Chargement des fichiers...")
        df_a = pd.read_excel(path_a, sheet_name=sheet_a, nrows=5)
        df_b = pd.read_excel(path_b, sheet_name=sheet_b, nrows=5)
        
        print(f"\n📊 TABLE A (à rechercher): {os.path.basename(path_a)}")
        print("Colonnes disponibles:")
        cols_a = df_a.columns.tolist()
        for i, col in enumerate(cols_a, 1):
            sample_data = str(df_a[col].iloc[0]) if not df_a[col].iloc[0] is None else "N/A"
            print(f"  {i:2d}. {col:<30} (ex: {sample_data[:30]})")
        
        print(f"\n📊 TABLE B (référence): {os.path.basename(path_b)}")
        print("Colonnes disponibles:")
        cols_b = df_b.columns.tolist()
        for i, col in enumerate(cols_b, 1):
            sample_data = str(df_b[col].iloc[0]) if not df_b[col].iloc[0] is None else "N/A"
            print(f"  {i:2d}. {col:<30} (ex: {sample_data[:30]})")
        
        config = {}
        
        # === ÉTAPE 1: Définir les colonnes principales de comparaison ===
        print("\n" + "="*60)
        print("📋 ÉTAPE 1: COLONNES PRINCIPALES DE COMPARAISON")
        print("="*60)
        
        # Nom principal Table A
        print(f"\n🏥 Sélectionnez la colonne PRINCIPALE contenant les noms d'établissements dans TABLE A:")
        config["COLA_NOM_HOPITAL"] = select_column_by_number(cols_a, "nom principal établissement (Table A)")
        
        # Nom principal Table B
        print(f"\n🏥 Sélectionnez la colonne PRINCIPALE contenant les noms d'établissements dans TABLE B:")
        config["COLB_NOM_SC"] = select_column_by_number(cols_b, "nom principal établissement (Table B)")
        config["COLB_NOM"] = config["COLB_NOM_SC"]  # Duplication pour compatibilité
        
        # Ville Table A
        print(f"\n🏙️ Sélectionnez la colonne contenant les VILLES dans TABLE A:")
        config["COLA_VILLE"] = select_column_by_number(cols_a, "ville (Table A)")
        
        # Ville Table B
        print(f"\n🏙️ Sélectionnez la colonne contenant les VILLES dans TABLE B:")
        config["COLB_VILLE"] = select_column_by_number(cols_b, "ville (Table B)")
        
        # === ÉTAPE 1.5: Choix du type de comparaison géographique ===
        print("\n" + "="*60)
        print("🗺️ ÉTAPE 1.5: TYPE DE COMPARAISON GÉOGRAPHIQUE")
        print("="*60)
        
        print("Comment voulez-vous comparer la localisation géographique ?")
        print("1. Ville uniquement (recommandé si pas de département)")
        print("2. Département uniquement") 
        print("3. Ville ET département (double vérification)")
        
        geo_choice = select_choice([1, 2, 3], "type de comparaison géographique")
        config["GEO_COMPARISON_TYPE"] = geo_choice
        
        # Configurer les départements selon le choix
        if geo_choice in [2, 3]:  # Département requis
            print(f"\n🗺️ Vous avez choisi d'utiliser le département.")
            
            # Département Table A
            dept_a_available = any("dept" in col.lower() or "departement" in col.lower() for col in cols_a)
            if dept_a_available or ask_yes_no("Y a-t-il une colonne département dans TABLE A"):
                config["COLA_DEPARTEMENT"] = select_column_by_number(cols_a, "département (Table A)")
            else:
                print("⚠️  Aucune colonne département dans TABLE A - utilisation ville uniquement")
                config["COLA_DEPARTEMENT"] = None
                if geo_choice == 2:  # Si département uniquement était choisi
                    config["GEO_COMPARISON_TYPE"] = 1  # Basculer sur ville uniquement
            
            # Département Table B
            dept_b_available = any("dept" in col.lower() or "departement" in col.lower() for col in cols_b)
            if dept_b_available or ask_yes_no("Y a-t-il une colonne département dans TABLE B"):
                config["COLB_DEPARTEMENT"] = select_column_by_number(cols_b, "département (Table B)")
            else:
                print("⚠️  Aucune colonne département dans TABLE B - utilisation ville uniquement")
                config["COLB_DEPARTEMENT"] = None
                if geo_choice == 2:  # Si département uniquement était choisi
                    config["GEO_COMPARISON_TYPE"] = 1  # Basculer sur ville uniquement
        else:
            config["COLA_DEPARTEMENT"] = None
            config["COLB_DEPARTEMENT"] = None
        
        # === ÉTAPE 2: Colonnes optionnelles ===
        print("\n" + "="*60)
        print("📋 ÉTAPE 2: COLONNES OPTIONNELLES")
        print("="*60)
        
        # Nom alternatif Table B
        print(f"\n📝 Y a-t-il une colonne avec un NOM ALTERNATIF/SECONDAIRE dans TABLE B ?")
        if ask_yes_no("Utiliser un nom alternatif"):
            config["COLB_NOM_2"] = select_column_by_number(cols_b, "nom alternatif (Table B)")
        else:
            config["COLB_NOM_2"] = None
        
        # Supprimer les anciennes sections département (déplacées plus haut)
        
        # === ÉTAPE 3: Identification du bon FINESS ===
        print("\n" + "="*60)
        print("🎯 ÉTAPE 3: IDENTIFICATION DU BON CODE FINESS")
        print("="*60)
        
        print("Dans quelle table se trouve le BON code FINESS (le plus fiable) ?")
        print("1. Table A (fichier à rechercher)")
        print("2. Table B (fichier de référence)")
        print("3. Les deux tables ont des codes FINESS")
        
        finess_choice = select_choice([1, 2, 3], "source du bon FINESS")
        
        if finess_choice in [1, 3]:
            print(f"\n🏥 Sélectionnez la colonne contenant le code FINESS dans TABLE A:")
            config["COLA_FINESS"] = select_column_by_number(cols_a, "FINESS (Table A)")
        else:
            config["COLA_FINESS"] = None
            
        if finess_choice in [2, 3]:
            print(f"\n🏥 Sélectionnez la colonne contenant le code FINESS dans TABLE B:")
            config["COLB_FIN_SCS"] = select_column_by_number(cols_b, "FINESS (Table B)")
        else:
            config["COLB_FIN_SCS"] = None
        
        # Déterminer quelle est la source principale du FINESS
        if finess_choice == 1:
            config["PRIMARY_FINESS_SOURCE"] = "TABLE_A"
        elif finess_choice == 2:
            config["PRIMARY_FINESS_SOURCE"] = "TABLE_B"
        else:
            print("\n🤔 Les deux tables ont des codes FINESS. Laquelle est la plus fiable ?")
            print("1. Table A (fichier à rechercher)")
            print("2. Table B (fichier de référence)")
            primary_choice = select_choice([1, 2], "source principale du FINESS")
            config["PRIMARY_FINESS_SOURCE"] = "TABLE_A" if primary_choice == 1 else "TABLE_B"
        
        # === RÉSUMÉ ET CONFIRMATION ===
        print("\n" + "="*60)
        print("✅ RÉSUMÉ DE LA CONFIGURATION")
        print("="*60)
        
        print("🔍 Comparaisons principales:")
        print(f"  • Noms: '{config['COLA_NOM_HOPITAL']}' ↔ '{config['COLB_NOM_SC']}'")
        
        # Affichage de la stratégie géographique
        geo_type = config.get("GEO_COMPARISON_TYPE", 1)
        if geo_type == 1:
            print(f"  • Géographie: Ville uniquement - '{config['COLA_VILLE']}' ↔ '{config['COLB_VILLE']}'")
        elif geo_type == 2:
            if config.get("COLA_DEPARTEMENT") and config.get("COLB_DEPARTEMENT"):
                print(f"  • Géographie: Département uniquement - '{config['COLA_DEPARTEMENT']}' ↔ '{config['COLB_DEPARTEMENT']}'")
            else:
                print(f"  • Géographie: Ville (département non disponible) - '{config['COLA_VILLE']}' ↔ '{config['COLB_VILLE']}'")
        else:  # geo_type == 3
            print(f"  • Géographie: Ville - '{config['COLA_VILLE']}' ↔ '{config['COLB_VILLE']}'")
            if config.get("COLA_DEPARTEMENT") and config.get("COLB_DEPARTEMENT"):
                print(f"  • Géographie: + Département - '{config['COLA_DEPARTEMENT']}' ↔ '{config['COLB_DEPARTEMENT']}'")
        
        if config.get("COLB_NOM_2"):
            print(f"  • Nom alternatif: '{config['COLB_NOM_2']}'")
        
        print("\n🏥 Codes FINESS:")
        if config.get("COLA_FINESS"):
            print(f"  • Table A: '{config['COLA_FINESS']}'")
        if config.get("COLB_FIN_SCS"):
            print(f"  • Table B: '{config['COLB_FIN_SCS']}'")
        print(f"  • Source principale: {config['PRIMARY_FINESS_SOURCE']}")
        
        if ask_yes_no("Confirmer cette configuration"):
            return config
        else:
            print("❌ Configuration annulée.")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return None

def select_column_by_number(columns, description):
    """
    Permet de sélectionner une colonne par son numéro
    """
    while True:
        try:
            choice = input(f"\nChoisissez le numéro pour {description} (1-{len(columns)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(columns):
                    selected = columns[idx]
                    print(f"✅ Sélectionné: '{selected}'")
                    return selected
            print("❌ Numéro invalide, veuillez réessayer.")
        except (ValueError, KeyboardInterrupt):
            print("❌ Entrée invalide, veuillez réessayer.")

def select_choice(valid_choices, description):
    """
    Permet de sélectionner parmi des choix valides
    """
    while True:
        try:
            choice = input(f"\nVotre choix pour {description}: ").strip()
            if choice.isdigit() and int(choice) in valid_choices:
                return int(choice)
            print(f"❌ Choix invalide. Options valides: {valid_choices}")
        except (ValueError, KeyboardInterrupt):
            print("❌ Entrée invalide, veuillez réessayer.")

def ask_yes_no(question):
    """
    Pose une question oui/non
    """
    while True:
        response = input(f"{question} ? (o/n): ").strip().lower()
        if response in ['o', 'oui', 'y', 'yes']:
            return True
        elif response in ['n', 'non', 'no']:
            return False
        print("❌ Répondez par 'o' (oui) ou 'n' (non)")

def get_dynamic_config(path_a, path_b, sheet_a="Sheet1", sheet_b="Sheet1"):
    """
    Génère une configuration dynamique basée sur le mode choisi
    """
    if COLUMN_CONFIG_MODE == "interactive":
        print("🎯 Mode interactif activé - Configuration flexible des colonnes")
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
    "COLA_NOM_HOPITAL": "Nom",
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

# Variables ajoutées pour la compatibilité avec les autres modules
GEO_COMPARISON_TYPE = FINAL_CONFIG.get("GEO_COMPARISON_TYPE", 1)  # 1=ville, 2=dept, 3=les deux
PRIMARY_FINESS_SOURCE = FINAL_CONFIG.get("PRIMARY_FINESS_SOURCE", "TABLE_B")  # TABLE_A ou TABLE_B

# Variables héritées pour la compatibilité (anciennes configurations)
if FINAL_CONFIG == STATIC_CONFIG:
    # Mode de compatibilité - utilise les anciennes valeurs par défaut
    GEO_COMPARISON_TYPE = 1  # Ville uniquement par défaut
    PRIMARY_FINESS_SOURCE = "TABLE_B"  # Table B par défaut
    
    # Ajuster selon la disponibilité des colonnes
    if COLA_DEPARTEMENT and COLB_DEPARTEMENT:
        GEO_COMPARISON_TYPE = 3  # Utiliser ville ET département si disponibles

# ========== AUTRES PARAMÈTRES ==========

# Gestion de l'historique et des fichiers de sortie
if CREATE_NEW_OUTPUT:
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(OUTPUT_PATH)[0]
    extension = os.path.splitext(OUTPUT_PATH)[1]
    OUTPUT_PATH = f"{base_name}_{timestamp}{extension}"

# Mots à remplacer pour le nettoyage (VARIABLE MANQUANTE AJOUTÉE)
REPLACE = {"-": " ", " DE ": " ", " DU ": " ", "D'": " ", " DES ": " "}

# Configuration API
GOOGLE_API_KEY = "AIzaSyBfQjj1pNx0yDlXUSo4tdWUe5RcE35ON6o"
MODEL_NAME = "gemini-2.5-flash"

# Paramètres de matching fuzzy (utilise le niveau choisi)
FUZZY_THRESHOLD = FUZZY_LEVELS[FUZZY_LEVEL]["threshold"]

MAX_REQUESTS_PER_MINUTE = 50
TIME_WINDOW = 60
SAVE_INTERVAL = 10

# ========== MODE TEST ==========
TEST_MODE = False  # True = mode test avec échantillonnage, False = mode normal
TEST_SAMPLE_SIZE = 25  # Nombre d'établissements à tester en mode test
TEST_RANDOM_SEED = 42  # Graine pour la reproductibilité (None = aléatoire)
TEST_OUTPUT_DIR = "test_results"  # Sous-dossier pour les résultats de test

# Fonctions utilitaires pour les autres modules
def get_geo_comparison_strategy():
    """
    Retourne la stratégie de comparaison géographique configurée
    """
    return {
        "type": GEO_COMPARISON_TYPE,
        "use_city": GEO_COMPARISON_TYPE in [1, 3],
        "use_department": GEO_COMPARISON_TYPE in [2, 3],
        "city_only": GEO_COMPARISON_TYPE == 1,
        "department_only": GEO_COMPARISON_TYPE == 2,
        "both": GEO_COMPARISON_TYPE == 3
    }

def get_finess_strategy():
    """
    Retourne la stratégie de gestion des codes FINESS
    """
    return {
        "primary_source": PRIMARY_FINESS_SOURCE,
        "has_source_finess": COLA_FINESS is not None,
        "has_reference_finess": COLB_FIN_SCS is not None,
        "prefer_source": PRIMARY_FINESS_SOURCE == "TABLE_A",
        "prefer_reference": PRIMARY_FINESS_SOURCE == "TABLE_B"
    }

def get_column_mapping():
    """
    Retourne un mapping complet des colonnes configurées
    """
    return {
        "source": {
            "name": COLA_NOM_HOPITAL,
            "city": COLA_VILLE,
            "department": COLA_DEPARTEMENT,
            "finess": COLA_FINESS
        },
        "reference": {
            "name_primary": COLB_NOM_SC,
            "name_secondary": COLB_NOM_2,
            "city": COLB_VILLE,
            "department": COLB_DEPARTEMENT,
            "finess": COLB_FIN_SCS
        },
        "output": {
            "match_name": COLA_MATCH_NAME,
            "confidence": COLA_MATCH_CONFIDENCE
        }
    }

def validate_configuration():
    """
    Valide que la configuration est cohérente
    """
    errors = []
    warnings = []
    
    # Vérifications essentielles
    if not COLA_NOM_HOPITAL:
        errors.append("Colonne nom établissement source manquante")
    if not COLB_NOM_SC:
        errors.append("Colonne nom établissement référence manquante")
    if not COLA_VILLE:
        errors.append("Colonne ville source manquante")
    if not COLB_VILLE:
        errors.append("Colonne ville référence manquante")
    
    # Vérifications géographiques
    geo_strategy = get_geo_comparison_strategy()
    if geo_strategy["use_department"]:
        if not COLA_DEPARTEMENT:
            warnings.append("Comparaison département demandée mais colonne source manquante")
        if not COLB_DEPARTEMENT:
            warnings.append("Comparaison département demandée mais colonne référence manquante")
    
    # Vérifications FINESS
    finess_strategy = get_finess_strategy()
    if not finess_strategy["has_source_finess"] and not finess_strategy["has_reference_finess"]:
        warnings.append("Aucune colonne FINESS configurée")
    
    # Auto-correction si département demandé mais pas disponible
    if geo_strategy["use_department"] and (not COLA_DEPARTEMENT or not COLB_DEPARTEMENT):
        print("🔧 Auto-correction: Basculement sur ville uniquement (département non disponible)")
        global GEO_COMPARISON_TYPE
        GEO_COMPARISON_TYPE = 1  # Forcer ville uniquement
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# Validation automatique au chargement
_validation = validate_configuration()
if not _validation["valid"]:
    print("❌ Configuration invalide:")
    for error in _validation["errors"]:
        print(f"   • {error}")

if _validation["warnings"]:
    print("⚠️  Avertissements configuration:")
    for warning in _validation["warnings"]:
        print(f"   • {warning}")
