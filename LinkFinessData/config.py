"""
Configuration adaptable pour le matching des établissements de santé
"""
import pandas as pd
import os

# ========== CONFIGURATION PRINCIPALE ==========

# Chemins des fichiers
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\Data_matching\Fichier_ref\Data-FINESS_Modele.xlsx"
PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\emeis_ehpad_results.xlsx"
OUTPUT_PATH = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finess_emeis-SCS-ehpad.xlsx"

# ========== GESTION DE L'HISTORIQUE ==========
RESET_HISTORY = True  # True = recommencer à zéro, False = continuer
CREATE_NEW_OUTPUT = True  # True = nouveau fichier avec timestamp

# ========== AUTO-DÉTECTION DES COLONNES ==========

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

def get_dynamic_config(path_a, path_b, sheet_a="Sheet1", sheet_b="Sheet1"):
    """
    Génère une configuration dynamique basée sur les fichiers
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
    "COLA_NOM_HOPITAL": "Nom de l'Ehpad",
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
FUZZY_THRESHOLD = 85
MAX_REQUESTS_PER_MINUTE = 50
TIME_WINDOW = 60
SAVE_INTERVAL = 10
