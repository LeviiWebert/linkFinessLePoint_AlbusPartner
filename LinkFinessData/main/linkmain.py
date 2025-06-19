import pandas as pd
import os
import sys
import re
from fuzzywuzzy import fuzz
import google.generativeai as genai

# Configure Google AI
genai.configure(api_key="AIzaSyBfQjj1pNx0yDlXUSo4tdWUe5RcE35ON6o")
model = genai.GenerativeModel('gemini-1.5-flash')


PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\data_propre_ext_LP-167_Acc_Risque.xlsx"
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Résultats\DONNEES_REUNIES_COMPLETE.xlsx"
OUTPUT_PATH  = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finessR1.xlsx"

# Colonnes Data (Table A)
COLA_NOM_HOPITAL  = "Nom hopital"
COLA_NOM_CLINIQUE = "Nom clinique"
COLA_VILLE        = "Ville"
COLA_FINESS       = "FINESS"


# Colonnes DF (Table B)
COLB_NOM_SC = "NomScanSante"
COLB_NOM = "Nom"
COLB_NOM_2 = "Nom2"
COLB_VILLE = "Ville"
COLB_FIN_SCS = "FINESSSCANSANTE"

REPLACE = {
    "-"," DE "," DU ",
    "D'"," DES "
}

df_lp = pd.read_excel(PATH_TABLE_A)
df_sc = pd.read_excel(PATH_TABLE_B)
# Compararé Rule 1 et Rule 2, on va essayer en faisant un match fyzzy à 90ù sur les même colonnes, compara le nombre de finess trové
#  Il faut limité le nombre de finess à 1 trouvé
# on peut diviser les recherches sur colonnes en différentes règles
for idx, row in df_lp.iterrows():
    print(f"L'index de la ligne est : {idx}\n\n")
    # Check if the city from Table A is contained within any city from Table B
    df_sc_filtered = df_sc[
        df_sc[COLB_VILLE].replace(" ST "," SAINT ").str.upper().str.contains(str(str(row[COLA_VILLE]).replace(" ST "," SAINT ")).upper())
    ]
    print(f"Recherche pour l'hôpital : {row[COLA_NOM_HOPITAL]} dans la ville : {row[COLA_VILLE]}")
    if df_sc_filtered.empty:
        print(f"Aucun hôpital trouvé pour {row[COLA_NOM_HOPITAL]} dans la ville {row[COLA_VILLE]}")
        row[COLA_FINESS] = None
        continue
    print(f"{len(df_sc_filtered)} hôpitaux trouvés pour {row[COLA_NOM_HOPITAL]} dans la ville {row[COLA_VILLE]}")
    # On va comparer les noms des hôpitaux avec les noms des SCS
    for idx2,row_sc in df_sc_filtered.iterrows():
        # On va comparer les noms des hôpitaux avec les noms des SCS
        # On va nettoyer les noms pour enlever les caractères spéciaux et les espaces
        print(f"Comparaison {str(row[COLA_NOM_HOPITAL]).upper()} avec le SCS : {row_sc[COLB_NOM_SC]}\n")
        nomhop = str(row[COLA_NOM_HOPITAL]).upper()
        nomscs = str(row_sc[COLB_NOM_SC]).upper()
        nom = str(row_sc[COLB_NOM]).upper()
        nom2 = str(row_sc[COLB_NOM_2]).upper()
        for mot in REPLACE:
            nom = nom.replace(mot, " ")
            nomscs = nomscs.replace(mot, " ")
            nomhop = nomhop.replace(mot, " ")
            nom2 = nom2.replace(mot, " ")

        # ST -> SAINT
        nom.replace(" ST "," SAINT ")
        nomscs.replace(" ST "," SAINT ")
        nomhop.replace(" ST "," SAINT ")
        nom2.replace(" ST "," SAINT ")
        # comparaison des mots entre eux en tant qu'entier

        mots_nom = nom.split()
        mots_nomscs = nomscs.split()
        mots_nom2 = nom2.split()
        mots_nomhop = nomhop.split()        
        # comparaison des mots entre eux en tant qu'entier
        if any(re.search(rf"\b{re.escape(mot)}\b", nomscs) for mot in mots_nomhop):
            print(f"Match trouvé : {nomhop} correspond à {nomscs} pour {row_sc[COLB_FIN_SCS]}")
            df_lp.at[idx, COLA_FINESS] = row_sc[COLB_FIN_SCS]
            break
        elif any(re.search(rf"\b{re.escape(mot)}\b", nom) for mot in mots_nomhop):
            print(f"Match trouvé : {nomhop} correspond à {nom} pour {row_sc[COLB_FIN_SCS]}")
            df_lp.at[idx, COLA_FINESS] = row_sc[COLB_FIN_SCS]
            break
        elif any(re.search(rf"\b{re.escape(mot)}\b", nom2) for mot in mots_nomhop):
            print(f"Match trouvé : {nomhop} correspond à {nom2} pour {row_sc[COLB_FIN_SCS]}")
            df_lp.at[idx, COLA_FINESS] = row_sc[COLB_FIN_SCS]
            break
        else:
            print(f"Aucun match trouvé pour {nomhop}\n") 
            df_lp.at[idx, COLA_FINESS] = None
# Enregistrer le DataFrame modifié  
print(df_lp[COLA_FINESS].view())
print("Enregistrement des résultats...")
if not os.path.exists(os.path.dirname(OUTPUT_PATH)):
    os.makedirs(os.path.dirname(OUTPUT_PATH))
try:
    df_lp.to_excel(OUTPUT_PATH, index=False)
except Exception as e:
    print(f"Erreur lors de l'enregistrement du fichier : {e}")
    sys.exit(1)
print(f"Résultats enregistrés dans {OUTPUT_PATH}")
