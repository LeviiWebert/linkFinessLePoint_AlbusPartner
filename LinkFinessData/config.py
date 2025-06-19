"""
Configuration pour le matching des établissements de santé
"""

# Chemins des fichiers
PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\data_propre_ext_LP-167_Acc_Risque.xlsx"
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Résultats\DONNEES_REUNIES_COMPLETE.xlsx"
#PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Data-FINESS_Modele.xlsx"
OUTPUT_PATH = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finessR1_AI.xlsx"

# Colonnes Table A (données à traiter)
COLA_NOM_HOPITAL = "Nom hopital"
COLA_NOM_CLINIQUE = "Nom clinique"
COLA_VILLE = "Ville"
COLA_FINESS = "FINESS"

# Colonnes Table B (référence)
COLB_NOM_SC = "NomScanSante"
COLB_NOM = "Nom"
COLB_NOM_2 = "Nom2"
COLB_VILLE = "Ville"
COLB_FIN_SCS = "FINESSSCANSANTE"
#COLB_FIN_SCS = "FINESS"

# Mots à remplacer pour le nettoyage
REPLACE = {
    "-": " ",
    " DE ": " ",
    " DU ": " ",
    "D'": " ",
    " DES ": " "
}

# Configuration API Google AI
GOOGLE_API_KEY = "AIzaSyBfQjj1pNx0yDlXUSo4tdWUe5RcE35ON6o"
MODEL_NAME = "gemini-1.5-flash"

# Paramètres de matching
FUZZY_THRESHOLD = 85  # Score minimum pour considérer un match fuzzy
MAX_REQUESTS_PER_MINUTE = 15  # Limite API Gemini
TIME_WINDOW = 60  # Fenêtre de temps en secondes
