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
import re
import os
import sys
import unicodedata

# ──────────────────────────────────────────────────────────────────────────────
#                               RÉGLAGES À ADAPTER
# ──────────────────────────────────────────────────────────────────────────────

PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\data_propre_ext_LP-167_Acc_Risque.xlsx"
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Filt_Fine_SCSant.xlsx"
OUTPUT_PATH  = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finess.xlsx"

# Colonnes Data (Table A)
COLA_NOM_HOPITAL  = "Nom hopital"
COLA_NOM_CLINIQUE = "Nom clinique"
COLA_VILLE        = "Ville"
COLA_DEPT         = "Département"
COLA_MOTS_SIG     = "Mots significatifs"

# Colonnes DF (Table B)
COLB_NOM          = "Nom"
COLB_NOM2         = "Nom2"
COLB_VILLE        = "Ville"
COLB_CODE_FINESS  = "FINESS"
COLB_CODE_FINESSJ  = "FINESSJ"

# STOPWORDS et abréviations
STOPWORDS = {
    "DE","DU","DES","UN","UNE","LE","LA","LES","AU","AUX","ET","EN","L",
    "GRAND","HÔPITAL","HOPITAL","CLINIQUE","HCL","GHL"
}
HOSP_ABBREV = {"CHU","CHI","CH","HCL","GHL"}

# ──────────────────────────────────────────────────────────────────────────────
#                   FONCTIONS UTILITAIRES
# ──────────────────────────────────────────────────────────────────────────────

def remove_accents(s: str) -> str:
    """
    Enlève les accents d'une chaîne Unicode :
    'CÔTE' -> 'COTE', 'BICÊTRE' -> 'BICETRE'
    """
    if not isinstance(s, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def extract_significant(text: str) -> str:
    """
    Extrait les mots 'significatifs' d'une chaîne (Data) :
      - Supprime accents puis majuscule, 
        ponctuation/apostrophes/tirets -> espaces
      - Garde les tokens alphabétiques (> 3 lettres, hors STOPWORDS)
    """
    if pd.isna(text):
        return ""
    s = remove_accents(str(text))
    s = re.sub(r"[’'\-–_/(),]", " ", s).upper()
    raw_tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", s)
    filtered = [t for t in raw_tokens if len(t) > 3 and t not in STOPWORDS]
    return " ".join(filtered)

def tokenize(text: str, mode: str) -> list:
    """
    Extrait les tokens alphabétiques :
      - mode='data' : tokens > 3 lettres, hors STOPWORDS
      - mode='df'   : same + conserve abréviations hospitalières
    """
    if pd.isna(text) or not str(text).strip():
        return []
    s = remove_accents(str(text))
    s = re.sub(r"[’'\-–_/(),]", " ", s).upper()
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", s)
    if mode == "data":
        return [t for t in raw if len(t) > 3 and t not in STOPWORDS]
    elif mode == "df":
        tokens = []
        for t in raw:
            if (len(t) > 3 and t not in STOPWORDS) or (t in HOSP_ABBREV):
                tokens.append(t)
        return tokens
    else:
        raise ValueError(f"Mode de tokenization inconnu : {mode}")

def extract_fallback_abbrev(name: str) -> list:
    """
    Si tokens_A vide, extrait abréviations hospitalières (CHU, CHI, CH, HCL, GHL) du nom Data.
    """
    if pd.isna(name):
        return []
    s = remove_accents(str(name)).upper()
    return [abbr for abbr in HOSP_ABBREV if re.search(rf"\b{abbr}\b", s)]

def normalize_city(v: str, is_df: bool) -> str:
    """
    Normalise une ville :
      - is_df=True  (DF)   : supprime code postal (5 chiffres) + 'CEDEX'
      - is_df=False (Data) : ne fait que majuscule, remplace tirets/apostrophes, 'SAINT'→'ST'
    """
    if pd.isna(v):
        return ""
    s = remove_accents(str(v)).strip().upper()
    if is_df:
        s = re.sub(r"^\d{5}\s*", "", s)    # supprime le code postal
        s = re.sub(r"\s+CEDEX$", "", s)    # supprime 'CEDEX'
    s = re.sub(r"[’'\-–]", " ", s)         # apostrophes/tirets → espace
    s = re.sub(r"\bSAINT\b", "ST", s)      # 'SAINT' → 'ST'
    return re.sub(r"\s+", " ", s).strip()  # espaces multiples → un seul

def try_match_on_column(candidates: pd.DataFrame, column: str, tokens_req: list) -> list:
    """
    Parmi candidats (filtrés sur département/ville), renvoie d'abord la liste
    des codes FINESS où tous tokens_req ∈ tokenize(rowB[column], "df").
    Si aucun, teste ceux où au moins un token_req ∈ tokenize(rowB[column], "df").
    """
    matched_all, matched_any = [], []

    for _, rowB in candidates.iterrows():
        nom_b = rowB.get(column, "")
        tokensB = tokenize(nom_b, "df")
        if tokens_req and all(tok in tokensB for tok in tokens_req):
            matched_all.append(str(rowB[COLB_CODE_FINESS]).strip())

    if matched_all:
        return matched_all

    for _, rowB in candidates.iterrows():
        nom_b = rowB.get(column, "")
        tokensB = tokenize(nom_b, "df")
        if tokens_req and any(tok in tokensB for tok in tokens_req):
            matched_any.append(str(rowB[COLB_CODE_FINESS]).strip())

    return matched_any

def do_token_match(cand_df, tokens_req, label: str) -> list:
    """
    Applique la logique "ALL → ANY" sur deux colonnes :
      1) ALL sur Nom
      2) Si plusieurs résultats, ALL sur Nom2
      3) Sinon ANY sur Nom
      4) Si >1 et Nom2 existe, ANY sur Nom2
    Renvoie la liste des codes FINESS.
    """
    # === ALL sur Nom ===
    all_codes = []
    for _, rowB in cand_df.iterrows():
        tokensB = tokenize(rowB[COLB_NOM], "df")
        if tokens_req and all(tok in tokensB for tok in tokens_req):
            all_codes.append(str(rowB[COLB_CODE_FINESS]).strip())
    if all_codes:
        return all_codes

    # === ANY sur Nom ===
    any_codes = []
    for _, rowB in cand_df.iterrows():
        tokensB = tokenize(rowB[COLB_NOM], "df")
        if tokens_req and any(tok in tokensB for tok in tokens_req):
            any_codes.append(str(rowB[COLB_CODE_FINESS]).strip())

    # Si plusieurs et Nom2 existe, on retente ALL puis ANY sur Nom2
    if len(any_codes) > 1 and COLB_NOM2 in cand_df.columns:
        all_codes_nom2 = []
        for _, rowB in cand_df.iterrows():
            tokensB2 = tokenize(rowB[COLB_NOM2], "df")
            if tokens_req and all(tok in tokensB2 for tok in tokens_req):
                all_codes_nom2.append(str(rowB[COLB_CODE_FINESS]).strip())
        if all_codes_nom2:
            return all_codes_nom2

        any_codes_nom2 = []
        for _, rowB in cand_df.iterrows():
            tokensB2 = tokenize(rowB[COLB_NOM2], "df")
            if tokens_req and any(tok in tokensB2 for tok in tokens_req):
                any_codes_nom2.append(str(rowB[COLB_CODE_FINESS]).strip())
        return any_codes_nom2

    return any_codes

def verif_finessj(cand_df: pd.DataFrame) -> str:
    if cand_df.empty:
        return ""
    # Récupère les valeurs non nulles, en chaîne, sans espaces superflus
    vals = (
        cand_df[COLB_CODE_FINESSJ]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )
    # Si une seule valeur unique, on la renvoie
    if len(vals) == 1:
        return vals[0]
    # Sinon (0 ou >1 valeurs distinctes), on renvoie chaîne vide
    return ""
def filter_candidates(mode: str, deptA: str, cityA: str, dfB_indexed: dict) -> pd.DataFrame:
    """
    Renvoie un sous-DataFrame filtré selon mode :
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
        return pd.DataFrame()

    else:
        raise ValueError(f"Mode de filtre inconnu : {mode}")

def match_row(rowA: pd.Series, dfB_indexed: dict, idxA: int = None) -> tuple:
    """
    Pour une ligne Data, on tente successivement :
      1) Matching sur département + ville
      2) Si aucun résultat, matching sur département seul
      3) Si encore impossible, matching sur ville seule

    Renvoie (code_finess, statut). Logique "ALL → ANY" puis "Nom2" pour désambiguïser.
    """
    # 1) Construire tokensA (Mots significatifs ou fallback abrév)
    tokensA = tokenize(rowA[COLA_MOTS_SIG], "data")
    if not tokensA:
        source = rowA.get(COLA_NOM_HOPITAL, "") or rowA.get(COLA_NOM_CLINIQUE, "")
        tokensA = extract_fallback_abbrev(source)

    # 2) Préparer clés département et ville
    deptA = str(rowA[COLA_DEPT]).zfill(2)
    cityA = normalize_city(rowA[COLA_VILLE], False)

    # 3) Tentatives successives : dept+ville → dept → ville
    for mode in ["dept_city", "dept", "city"]:
        candidats = filter_candidates(mode, deptA, cityA, dfB_indexed)
        if not candidats.empty:
            codes = do_token_match(candidats, tokensA, mode)
            if codes:
                # Filtrer les codes vides / NaN avant d’évaluer l’unicité
                codes_nonvides = [c for c in codes if str(c).strip() not in ("", "nan")]
                if len(codes_nonvides) == 1:
                    return codes_nonvides[0], "1 - réussi"
                elif len(set(codes_nonvides)) == 1:
                    seul_code = list(set(codes_nonvides))[0]
                    return seul_code, "1 - réussi (identique sur plusieurs lignes)"
                else:
                    # plusieurs codes différents → on regarde si tous les finessj des candidats sont identiques
                    code_unique = verif_finessj(candidats)
                    if len(code_unique)>0:
                        print("condition validé")
                        return code_unique, "PLUSIEURS CAS"
                    return "PLUSIEURS CAS", "PLUSIEURS CAS"

    # 4) Aucun matching trouvé
    return "", "0 - pas bon"

def main():
    # Vérifier existence des fichiers
    for p in (PATH_TABLE_A, PATH_TABLE_B):
        if not os.path.isfile(p):
            print(f"❌ Fichier introuvable : {p}", file=sys.stderr)
            return

    # Charger Data et DF
    dfA = pd.read_excel(PATH_TABLE_A, dtype=str)
    dfB = pd.read_excel(PATH_TABLE_B, dtype=str)

    # Identifier colonne “Nom hopital” OU “Nom clinique”
    if COLA_NOM_HOPITAL in dfA.columns:
        nomA_col = COLA_NOM_HOPITAL
    elif COLA_NOM_CLINIQUE in dfA.columns:
        nomA_col = COLA_NOM_CLINIQUE
    else:
        print("❌ Ni 'Nom hopital' ni 'Nom clinique' introuvés dans Data.", file=sys.stderr)
        return

    # Vérifier colonnes nécessaires dans Data
    for col in (COLA_DEPT, COLA_VILLE, COLA_MOTS_SIG):
        if col not in dfA.columns:
            print(f"❌ Colonne '{col}' absente dans Data.", file=sys.stderr)
            return

    # Vérifier colonnes nécessaires dans DF
    for col in (COLB_NOM, COLB_VILLE, COLB_CODE_FINESS):
        if col not in dfB.columns:
            print(f"❌ Colonne '{col}' absente dans DF.", file=sys.stderr)
            return

    # 1) Générer/recalculer "Mots significatifs" dans Data
    dfA[COLA_MOTS_SIG] = dfA[nomA_col].apply(lambda x: extract_significant(x))

    # 2) Normaliser "Département" (2 chiffres) et "Ville" (nom simple) dans Data
    dfA[COLA_DEPT] = dfA[COLA_DEPT].astype(str).str.strip().str.zfill(2)
    dfA["City_norm_A"] = dfA[COLA_VILLE].apply(lambda x: normalize_city(x, False))

    # 3) Préparer DF : extraire code département + normaliser ville
    dfB["Dept"]      = dfB[COLB_VILLE].astype(str).str.strip().str[:2].str.zfill(2)
    dfB["City_norm"] = dfB[COLB_VILLE].apply(lambda x: normalize_city(x, True))

    # Grouper DF par département
    dfB_grouped  = dfB.groupby("Dept")
    dfB_indexed  = {dept: sub.reset_index(drop=True) for dept, sub in dfB_grouped}

    # 4) Parcourir chaque ligne Data, faire correspondance
    codes_fin, statuts = [], []
    for idxA, rowA in dfA.iterrows():
        code, statut = match_row(rowA, dfB_indexed, idxA)
        codes_fin.append(code)
        statuts.append(statut)

    dfA["Code FINESS final"] = codes_fin
    dfA["Statut final"]      = statuts

    # 5) Préparer et sauvegarder le résultat
    cols_to_keep = [nomA_col, COLA_DEPT, "City_norm_A", COLA_MOTS_SIG, "Code FINESS final", "Statut final"]
    other_cols  = [c for c in dfA.columns if c not in cols_to_keep]
    final_df    = dfA[cols_to_keep + other_cols]

    final_df.to_excel(OUTPUT_PATH, index=False)
    print(f"\n✅ Résultat enregistré dans : {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
