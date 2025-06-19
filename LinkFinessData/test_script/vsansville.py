#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script optimisé pour faire correspondre et assigner le Code FINESS entre :
  - Table A (Data) : data_propre_ext_LP-167_Acc_Risque.xlsx
      • Colonnes essentielles : “Nom hopital” (ou “Nom clinique”), “Ville”, “Département”, “Mots significatifs”
  - Table B (DF) : Filtered_FINESS.xlsx
      • Colonnes essentielles : “Nom” (prioritaire), “Nom2” (secondaire), “Ville” (code postal + nom), “FINESS”

Spécificités intégrées :
  - Matching par département + ville → département seul → ville seul
  - Extraction de tokens > 3 lettres et filtrage STOPWORDS (Data)
  - DF conserve les abréviations hospitalières (CH, CHU, CHI, HCL, GHL)
  - Fallback abréviations si “Mots significatifs” vide

Usage :
  1. Ajuster en début de script les chemins PATH_TABLE_A, PATH_TABLE_B, OUTPUT_PATH
  2. pip install pandas openpyxl
  3. python match_finess_optimise.py
  4. Ajuster les noms des colonnes
"""

import pandas as pd
import os
import sys
from fuzzywuzzy import fuzz

# ──────────────────────────────────────────────────────────────────────────────
#                               RÉGLAGES À ADAPTER
# ──────────────────────────────────────────────────────────────────────────────

PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\data_propre_ext_LP-167_Acc_Risque.xlsx"
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Résultats\RésultatR123456_tout.xlsx"
OUTPUT_PATH  = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finess.xlsx"
DEBUG_PATH   = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\debug_report.txt"

# Colonnes Data (Table A)
COLA_NOM_HOPITAL  = "Nom hopital"
COLA_NOM_CLINIQUE = "Nom clinique"
COLA_DEPT         = "Département"
COLA_MOTS_SIG     = "Mots significatifs"

# Colonnes DF (Table B)
COLB_NOM = "Nom"
COLB_FINESS  = "FINESS"
# seuil initial et pas de variation
SEUIL_INIT  = 90
DELTA_SCORE = 5


def main():
    # 1) Vérification des fichiers
    for p in (PATH_TABLE_A, PATH_TABLE_B):
        if not os.path.isfile(p):
            print(f"❌ Fichier introuvable : {p}", file=sys.stderr)
            return

    # 2) Chargement des DataFrames
    dfA = pd.read_excel(PATH_TABLE_A, dtype=str)
    dfB = pd.read_excel(PATH_TABLE_B, dtype=str)

    # 3) Initialisation des colonnes de résultat
    dfA["FINESS_match"]  = None
    dfA["match_score"]   = 0
    dfA["used_threshold"] = 0

    # 4) Préparation du fichier debug
    debug_lines = []
    debug_lines.append("DEBUG MATCHING REPORT\n")
    debug_lines.append("============================================================\n")

    # 5) Boucle de matching
    for idxA, rowA in dfA.iterrows():
        nom_a     = (rowA[COLA_NOM_HOPITAL] or "").strip()
        dept_code = (rowA[COLA_DEPT] or "")[:2]

        # Filtrer dfB sur le département
        dfB_dept = dfB[dfB[COLB_FINESS].str[:2] == dept_code]

        # Calcul de tous les scores
        candidats = [(fuzz.token_set_ratio(nom_a, (rowB[COLB_NOM] or "").strip()),
                       rowB[COLB_FINESS])
                      for _, rowB in dfB_dept.iterrows()]
        # Tri décroissant
        candidats.sort(key=lambda x: x[0], reverse=True)

        # Ajustement dynamique du seuil
        seuil    = SEUIL_INIT
        matchés  = [c for c in candidats if c[0] >= seuil]

        # Baisse si aucun
        while not matchés and seuil > 0:
            seuil -= DELTA_SCORE
            matchés = [c for c in candidats if c[0] >= seuil]

        # Hausse si plusieurs
        while len(matchés) > 1 and seuil < 100:
            seuil += DELTA_SCORE
            matchés = [c for c in candidats if c[0] >= seuil]

        # Enregistrer le résultat
        if len(matchés) == 1:
            best_score, best_finess = matchés[0]
            # on retrouve aussi le nom correspondant dans dfB
            best_name = next(
                rowB[COLB_NOM]
                for _, rowB in dfB_dept.iterrows()
                if rowB[COLB_FINESS] == best_finess
            )
            dfA.at[idxA, "FINESS_match"]   = best_finess
            dfA.at[idxA, "match_score"]    = best_score
            statut = f"MATCHED -> {best_finess} ('{best_name}') score {best_score}"
        elif not matchés:
            statut = "NO MATCH"
        else:
            statut = f"MULTIPLE MATCHES ({len(matchés)})"

        dfA.at[idxA, "used_threshold"] = seuil

        # Ligne de debug
        debug_lines.append(
            f"Ligne {idxA+1}: '{nom_a}' | seuil={seuil} | {statut}\n"
        )


    # 6) Écriture du debug_report.txt
    with open(DEBUG_PATH, "w", encoding="utf-8") as dbg:
        dbg.writelines(debug_lines)

    # 7) Export Excel final
    dfA.to_excel(OUTPUT_PATH, index=False)
    print("✅ Fichier Excel généré :", OUTPUT_PATH)
    print("ℹ️ Rapport de debug écrit dans :", DEBUG_PATH)

if __name__ == "__main__":
    main()