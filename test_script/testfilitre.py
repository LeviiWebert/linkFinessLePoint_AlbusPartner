#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour la fonction filter_candidates.
Il charge le fichier Filtered_FINESS.xlsx, crée l’index par département,
puis affiche le résultat de filter_candidates en mode 'dept', 'dept_city' et 'city'.
"""

import pandas as pd
import re
import unicodedata
import os
import sys

# ──────────────────────────────────────────────────────────────────────────────
# Chemin vers le fichier Filtered_FINESS.xlsx
# ──────────────────────────────────────────────────────────────────────────────

PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Filtered_FINESS.xlsx" # Ajuster si nécessaire

# Colonnes DF (Table B)
COLB_VILLE       = "Ville"
COLB_NOM         = "Nom"
COLB_NOM2        = "Nom2"
COLB_CODE_FINESS = "Code FINESS"

# ──────────────────────────────────────────────────────────────────────────────
# Outlines de la fonction filter_candidates (copiée ici pour tests)
# ──────────────────────────────────────────────────────────────────────────────

def normalize_df_city(v: str) -> str:
    """
    Normalise la ville dans DF (format 'XXXXX NOM' ou 'XXXXX NOM CEDEX') :
      - Supprime accents, majuscule, trim,
      - Retire le code postal (5 chiffres) + espace, supprime 'CEDEX',
      - Remplace tirets/apostrophes → espaces, SAINT → ST, puis réduit les espaces.
    """
    if pd.isna(v):
        return ""
    # Retirer accents
    nfkd = unicodedata.normalize("NFKD", str(v))
    s = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    s = s.strip().upper()
    # Supprimer code postal
    s = re.sub(r"^\d{5}\s*", "", s)
    # Supprimer 'CEDEX' en fin
    s = re.sub(r"\s+CEDEX$", "", s)
    # Remplacer apostrophes/tirets
    s = re.sub(r"[’'\-–]", " ", s)
    # SAINT → ST
    s = re.sub(r"\bSAINT\b", "ST", s)
    # Réduire espaces multiples
    return re.sub(r"\s+", " ", s).strip()

def filter_candidates(mode, deptA, cityA, dfB_indexed):
    """
    Renvoie un sous-DataFrame filtré selon le mode :
      - 'dept_city' → Dept + City_norm
      - 'dept'      → Dept seul
      - 'city'      → City_norm seul (parcours de tous les départements)
    """
    if mode in ("dept_city", "dept"):
        candidats_dept = dfB_indexed.get(deptA, pd.DataFrame())
        if candidats_dept.empty:
            return pd.DataFrame()

        if mode == "dept":
            return candidats_dept.reset_index(drop=True)
        
        # mode == "dept_city"
        filt_both = candidats_dept["City_norm"] == cityA
        return candidats_dept[filt_both].reset_index(drop=True)

    elif mode == "city":
        candidats_city = []
        for _, sub in dfB_indexed.items():
            filt_city = (sub["City_norm"] == cityA)
            if filt_city.any():
                candidats_city.append(sub[filt_city])
        if candidats_city:
            return pd.concat(candidats_city, ignore_index=True)
        else:
            return pd.DataFrame()
    
    else:
        raise ValueError(f"Mode de filtre inconnu : {mode}")

# ──────────────────────────────────────────────────────────────────────────────
# Bloc principal de test
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # Vérifier que le fichier existe
    if not os.path.isfile(PATH_TABLE_B):
        print(f"❌ Fichier introuvable : {PATH_TABLE_B}", file=sys.stderr)
        return

    # Charger DF
    dfB = pd.read_excel(PATH_TABLE_B, dtype=str)

    # 1) Extraire code département + normaliser la ville
    #    - Le département est pris comme les 2 premiers caractères du champ "Ville"
    dfB["Dept"] = dfB[COLB_VILLE].astype(str).str.strip().str[:2].str.zfill(2)
    dfB["City_norm"] = dfB[COLB_VILLE].apply(normalize_df_city)

    # 2) Indexer par département
    dfB_grouped = dfB.groupby("Dept")
    dfB_indexed = {dept: sub.reset_index(drop=True) for dept, sub in dfB_grouped}

    # 3) Afficher les départements disponibles
    print("Départements dans dfB_indexed :", sorted(dfB_indexed.keys()))
    print()

    # Exemple de tests pour quelques départements et villes
    exemples = [
        ("31", "TOULOUSE"),
        ("75", "PARIS"),
        ("13", "MARSEILLE"),
        ("69", "LYON"),
        ("21", "DIJON"),
    ]

    for dept_test, city_test in exemples:
        print(f"--- Test pour Département='{dept_test}', Ville='{city_test}' ---")
        
        # mode = 'dept'
        cand_dept = filter_candidates("dept", dept_test, city_test, dfB_indexed)
        print(f"Mode 'dept' → {len(cand_dept)} lignes trouvées")
        if not cand_dept.empty:
            print(cand_dept[[COLB_NOM, "Dept", "City_norm"]].head(5))
        print()

        # mode = 'dept_city'
        cand_both = filter_candidates("dept_city", dept_test, city_test, dfB_indexed)
        print(f"Mode 'dept_city' → {len(cand_both)} lignes trouvées")
        if not cand_both.empty:
            print(cand_both[[COLB_NOM, "Dept", "City_norm"]].head(5))
        print()

        # mode = 'city'
        cand_city = filter_candidates("city", dept_test, city_test, dfB_indexed)
        print(f"Mode 'city' → {len(cand_city)} lignes trouvées")
        if not cand_city.empty:
            print(cand_city[[COLB_NOM, "Dept", "City_norm"]].head(5))
        print()

    print("=== Fin des tests ===")

if __name__ == "__main__":
    main()
