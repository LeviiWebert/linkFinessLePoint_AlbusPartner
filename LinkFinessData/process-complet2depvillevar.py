#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script optimisé pour faire correspondre et assigner le Code FINESS entre :
  - Table A (Data) : data_propre_ext_LP-167_Acc_Risque.xlsx
      • Colonnes essentielles : “Nom hopital” (ou “Nom clinique”), “Ville”, “Département”, “Mots significatifs”
  - Table B (DF) : Filtered_FINESS.xlsx
      • Colonnes essentielles : “Nom” (prioritaire), “Nom2” (secondaire), “Ville” (code postal + nom), “Code FINESS”

Spécificités intégrées :
  - Matching par département + ville → département seul → ville seul
  - Extraction de tokens > 3 lettres et filtrage STOPWORDS (Data)
  - DF conserve les abréviations hospitalières (CH, CHU, CHI, HCL, GHL)
  - Fallback abréviations si “Mots significatifs” vide
  - Mode DEBUG : tous les logs sont envoyés dans “debug.txt” au lieu de la console

Usage :
  1. Ajuster en début de script les chemins PATH_TABLE_A, PATH_TABLE_B, OUTPUT_PATH
  2. pip install pandas openpyxl
  3. python match_finess_optimise_logs.py
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
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Filtered_FINESS.xlsx"
OUTPUT_PATH  = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finess.xlsx"
DEBUG_LOG    = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\debug.txt"

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
COLB_CODE_FINESS  = "Code FINESS"

# STOPWORDS et abréviations
STOPWORDS = {
    "DE","DU","DES","UN","UNE","LE","LA","LES","AU","AUX","ET","EN","L",
    "GRAND","HÔPITAL","HOPITAL","CLINIQUE","MATERNITÉ","MATERNITE","HCL","GHL"
}
HOSP_ABBREV = {"CHU","CHI","CH","HCL","GHL"}

# Activer/désactiver le mode DEBUG
DEBUG = True

# ──────────────────────────────────────────────────────────────────────────────
#                   FONCTIONS DE LOGGING & UTILITAIRES
# ──────────────────────────────────────────────────────────────────────────────

def init_debug_log(path: str):
    """
    Crée (ou écrase) le fichier de log DEBUG.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("=== DEBUG LOG START ===\n")
    except Exception as e:
        print(f"Erreur à l'ouverture du fichier DEBUG : {e}", file=sys.stderr)

def debug_print(msg: str):
    """
    Écrit une ligne de debug dans le fichier DEBUG_LOG si DEBUG est True.
    """
    if not DEBUG:
        return
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

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
      - Supprime accents puis MAJUSCULE, ponctuation/apostrophes/tirets -> espaces
      - Garde les tokens alphabétiques (> 3 lettres, hors STOPWORDS)
    """
    if pd.isna(text):
        return ""
    s = remove_accents(str(text))
    s = re.sub(r"[’'\-–_/(),]", " ", s).upper()
    raw_tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", s)
    filtered = [t for t in raw_tokens if len(t) > 3 and t not in STOPWORDS]
    return " ".join(filtered)

def tokenize_data(text: str) -> list:
    """
    Extrait les tokens alphabétiques (> 3 lettres, hors STOPWORDS) en MAJUSCULE pour Data.
    """
    if pd.isna(text) or not str(text).strip():
        return []
    s = remove_accents(str(text))
    s = re.sub(r"[’'\-–_/(),]", " ", s).upper()
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", s)
    return [t for t in raw if len(t) > 3 and t not in STOPWORDS]

def tokenize_df(text: str) -> list:
    """
    Extrait les tokens alphabétiques pour DF :
      - Garde tokens > 3 lettres hors STOPWORDS, 
      - Conserve les abréviations hospitalières (CH, CHU, CHI, HCL, GHL)
    """
    if pd.isna(text) or not str(text).strip():
        return []
    s = remove_accents(str(text))
    s = re.sub(r"[’'\-–_/(),]", " ", s).upper()
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", s)
    tokens = []
    for t in raw:
        if (len(t) > 3 and t not in STOPWORDS) or (t in HOSP_ABBREV):
            tokens.append(t)
    return tokens

def extract_fallback_abbrev(name: str) -> list:
    """
    Si tokens_A vide, extrait abréviations hospitalières (CHU, CHI, CH, HCL, GHL) du nom Data.
    """
    if pd.isna(name):
        return []
    s = remove_accents(str(name)).upper()
    found = [abbr for abbr in HOSP_ABBREV if re.search(rf"\b{abbr}\b", s)]
    return found

def normalize_data_city(v: str) -> str:
    """
    Normalise la ville dans Data (nom simple) :
      - Supprime accents, majuscule, trim,
      - Remplace tirets/apostrophes -> espaces, SAINT -> ST, puis un seul espace.
    """
    if pd.isna(v):
        return ""
    s = remove_accents(str(v)).strip().upper()
    s = re.sub(r"[’'\-–]", " ", s)
    s = re.sub(r"\bSAINT\b", "ST", s)
    return re.sub(r"\s+", " ", s).strip()

def normalize_df_city(v: str) -> str:
    """
    Normalise la ville dans DF (format 'XXXXX NOM' ou 'XXXXX NOM CEDEX') :
      - Supprime accents, majuscule, trim,
      - Retire le code postal (5 chiffres) + espace, supprime 'CEDEX',
      - Remplace tirets/apostrophes -> espaces, SAINT -> ST, puis un seul espace.
    """
    if pd.isna(v):
        return ""
    s = remove_accents(str(v)).strip().upper()
    s = re.sub(r"^\d{5}\s*", "", s)           # supprime code postal
    s = re.sub(r"\s+CEDEX$", "", s)           # supprime CEDEX
    s = re.sub(r"[’'\-–]", " ", s)
    s = re.sub(r"\bSAINT\b", "ST", s)
    return re.sub(r"\s+", " ", s).strip()

def try_match_on_column(candidates: pd.DataFrame, column: str, tokens_req: list, debug_prefix="") -> list:
    """
    Parmi candidats (déjà filtrés sur département/ville), renvoie d'abord la liste
    des Code FINESS où tous tokens_req ∈ tokenize_df(rowB[column]). Si aucun,
    renvoie ceux où au moins un token_req ∈ tokenize_df(rowB[column]).
    Les logs sont écrits dans debug.txt via debug_print, 
    en incluant toujours le nom et les tokensB pour chaque comparaison.
    """
    matched_all, matched_any = [], []

    for idxB, rowB in candidates.iterrows():
        nom_b = rowB.get(column, "")
        tokensB = tokenize_df(nom_b)
        if DEBUG:
            debug_print(f"{debug_prefix}>> Candidat [{column}] idx {idxB}: '{nom_b}' → tokensB = {tokensB}")

        # Étape 'all'
        if tokens_req and all(tok in tokensB for tok in tokens_req):
            matched_all.append(str(rowB[COLB_CODE_FINESS]).strip())
            if DEBUG:
                debug_print(f"{debug_prefix}   → ALL match: tokens_req {tokens_req} sont tous dans {tokensB} (Nom trouvé: '{nom_b}')")

    if matched_all:
        return matched_all

    # Si rien trouvé en 'all', on teste 'any'
    for idxB, rowB in candidates.iterrows():
        nom_b = rowB.get(column, "")
        tokensB = tokenize_df(nom_b)
        if tokens_req and any(tok in tokensB for tok in tokens_req):
            matched_any.append(str(rowB[COLB_CODE_FINESS]).strip())
            if DEBUG:
                debug_print(f"{debug_prefix}   → ANY match: au moins un de {tokens_req} est dans {tokensB} (Nom trouvé: '{nom_b}')")

    return matched_any

def match_row(rowA, dfB_indexed, idxA=None):
    """
    Pour une ligne Data, on tente successivement :
      1) Matching sur département + ville
      2) Si aucun résultat, matching sur département seul
      3) Si encore impossible, matching sur ville seule

    Renvoie (code_finess, statut). On garde la logique
    'all tokens → any token' puis 'Nom2' pour désambiguïser.
    Les logs détaillés sont écrits dans debug.txt via debug_print.
    """
    prefix = f"[Data idx {idxA}] " if idxA is not None else ""

    # 1) Construire tokensA (Mots significatifs ou fallback abrév)
    tokensA = tokenize_data(rowA[COLA_MOTS_SIG])
    if DEBUG:
        debug_print(f"[Ligne {idxA}] tokensA générés = {tokensA}")
    if not tokensA:
        source = rowA.get(COLA_NOM_HOPITAL, "") or rowA.get(COLA_NOM_CLINIQUE, "")
        tokensA = extract_fallback_abbrev(source)
        if DEBUG:
            debug_print(f"[Ligne {idxA}] Fallback abrév → tokensA = {tokensA}")

    # 2) Préparer clés département et ville
    deptA = str(rowA[COLA_DEPT]).zfill(2)               # ex. '31'
    cityA = normalize_data_city(rowA[COLA_VILLE])       # ex. 'TOULOUSE'
    if DEBUG:
        debug_print(f"{prefix}Département Data: '{rowA[COLA_DEPT]}' → '{deptA}'")
        debug_print(f"{prefix}Ville Data: '{rowA[COLA_VILLE]}' → '{cityA}'")

    # 3) Extraire candidats DF pour département
    candidats_dept = dfB_indexed.get(deptA, pd.DataFrame())
    if DEBUG:
        if not candidats_dept.empty:
            noms_dept = candidats_dept[COLB_NOM].tolist()
            debug_print(f"[Ligne {idxA}] Candidats après filtre DÉPT nom('{deptA}') → Noms disponibles = {noms_dept}")
            noms_dept2 = candidats_dept[COLB_NOM2].tolist()
            debug_print(f"[Ligne {idxA}] Candidats après filtre DÉPT nom2('{deptA}') → Noms2 disponibles = {noms_dept2}")
        else:
            debug_print(f"[Ligne {idxA}] Aucun candidat après filtre DÉPT ('{deptA}')")

    # Fonction interne de matching (ALL → ANY + Nom2)        
    def do_token_match(cand_df, tokens_req, label, debug_pref=""):
        """
        Essaie sur cand_df (déjà filtré sur dépt/ville) :
          1) ALL sur 'label.Nom'
          2) Si plusieurs, ALL sur 'label.Nom2'
          3) Sinon ANY sur 'label.Nom', puis ANY sur 'label.Nom2'
        Renvoie liste des codes trouvés (peut être vide).
        """
        # === ALL sur 'Nom' ===
        if DEBUG:
            debug_print(f"{debug_pref}--- ALL sur '{label}.Nom' ---")
        all_codes = []
        for i, rowB in cand_df.iterrows():
            tokensB = tokenize_df(rowB[COLB_NOM])
            if tokens_req and all(tok in tokensB for tok in tokens_req):
                all_codes.append(str(rowB[COLB_CODE_FINESS]).strip())
                if DEBUG:
                    debug_print(f"{debug_pref}    [ALL match Nom] '{rowB[COLB_NOM]}' → tokensB = {tokensB}")

        if all_codes:
            return all_codes

        # === ANY sur 'Nom' ===
        if DEBUG:
            debug_print(f"{debug_pref}--- ANY sur '{label}.Nom' ---")
        any_codes = []
        for i, rowB in cand_df.iterrows():
            tokensB = tokenize_df(rowB[COLB_NOM])
            if tokens_req and any(tok in tokensB for tok in tokens_req):
                any_codes.append(str(rowB[COLB_CODE_FINESS]).strip())
                if DEBUG:
                    debug_print(f"{debug_pref}    [ANY match Nom] '{rowB[COLB_NOM]}' → tokensB = {tokensB}")

        # Si plusieurs ANY et Nom2 existe, on retente ALL puis ANY sur Nom2
        if len(any_codes) > 1 and COLB_NOM2 in cand_df.columns:
            if DEBUG:
                debug_print(f"{debug_pref}--- Désambiguïsation: ALL sur '{label}.Nom2' ---")
            all_codes_nom2 = []
            for i, rowB in cand_df.iterrows():
                tokensB2 = tokenize_df(rowB[COLB_NOM2])
                if tokens_req and all(tok in tokensB2 for tok in tokens_req):
                    all_codes_nom2.append(str(rowB[COLB_CODE_FINESS]).strip())
                    if DEBUG:
                        debug_print(f"{debug_pref}    [ALL match Nom2] '{rowB[COLB_NOM2]}' → tokensB2 = {tokensB2}")
            if all_codes_nom2:
                return all_codes_nom2

            if DEBUG:
                debug_print(f"{debug_pref}--- Désambiguïsation: ANY sur '{label}.Nom2' ---")
            any_codes_nom2 = []
            for i, rowB in cand_df.iterrows():
                tokensB2 = tokenize_df(rowB[COLB_NOM2])
                if tokens_req and any(tok in tokensB2 for tok in tokens_req):
                    any_codes_nom2.append(str(rowB[COLB_CODE_FINESS]).strip())
                    if DEBUG:
                        debug_print(f"{debug_pref}    [ANY match Nom2] '{rowB[COLB_NOM2]}' → tokensB2 = {tokensB2}")
            return any_codes_nom2

        return any_codes

    # ─── ÉTAPE 1 : DÉPARTEMENT + VILLE ────────────────────────────────────────────
    if not candidats_dept.empty and tokensA:
        # Filtrer par ville normalisée
        filt_both = candidats_dept["City_norm"] == cityA
        candidats_both = candidats_dept[filt_both].reset_index(drop=True)
        if DEBUG:
            if not candidats_both.empty:
                noms_both = candidats_both[COLB_NOM].tolist()
                debug_print(f"[Ligne {idxA}] Candidats après filtre DÉPT+VILLE ('{deptA}','{cityA}') → Noms disponibles = {noms_both}")
                noms_both2 = candidats_both[COLB_NOM2].tolist()
                debug_print(f"[Ligne {idxA}] Candidats après filtre DÉPT+VILLE nom2 ('{deptA}','{cityA}') → Noms2 disponibles = {noms_both2}")
            else:
                debug_print(f"[Ligne {idxA}] Aucun candidat après filtre DÉPT+VILLE ('{deptA}','{cityA}')")

        if not candidats_both.empty:
            codes_both = do_token_match(candidats_both, tokensA, "Both", debug_pref=prefix + "  [Both] ")
            if codes_both:
                if len(codes_both) == 1:
                    if DEBUG:
                        debug_print(f"{prefix}  → Correspondance unique (dépt+ville) : {codes_both[0]}")
                    return codes_both[0], "1 - réussi"
                else:
                    if DEBUG:
                        debug_print(f"{prefix}  → Plusieurs correspondances (dépt+ville) : {codes_both} → PLUSIEURS CAS")
                    return "PLUSIEURS CAS", "PLUSIEURS CAS"
            else:
                if DEBUG:
                    debug_print(f"{prefix}  → Aucun code trouvé (dépt+ville)")

    # ─── ÉTAPE 2 : DÉPARTEMENT SEUL ───────────────────────────────────────────────
    if not candidats_dept.empty and tokensA:
        if DEBUG:
            noms_dept_seul = candidats_dept[COLB_NOM].tolist()
            debug_print(f"[Ligne {idxA}] Candidats après filtre DÉPT SEUL ('{deptA}') → Noms disponibles = {noms_dept_seul}")
            noms_dept_seul2 = candidats_dept[COLB_NOM2].tolist()
            debug_print(f"[Ligne {idxA}] Candidats après filtre DÉPT SEUL nom2 ('{deptA}') → Noms2 disponibles = {noms_dept_seul2}")

        codes_dept = do_token_match(candidats_dept, tokensA, "Dept", debug_pref=prefix + "  [Dept] ")
        if codes_dept:
            if len(codes_dept) == 1:
                if DEBUG:
                    debug_print(f"{prefix}  → Correspondance unique (dépt seul) : {codes_dept[0]}")
                return codes_dept[0], "1 - réussi"
            else:
                if DEBUG:
                    debug_print(f"{prefix}  → Plusieurs correspondances (dépt seul) : {codes_dept} → PLUSIEURS CAS")
                return "PLUSIEURS CAS", "PLUSIEURS CAS"
        else:
            if DEBUG:
                debug_print(f"{prefix}  → Aucun code trouvé (dépt seul)")

    # ─── ÉTAPE 3 : VILLE SEULE ──────────────────────────────────────────────────
    candidats_city = []
    for _, sub in dfB_indexed.items():
        filt_city = (sub["City_norm"] == cityA)
        if filt_city.any():
            candidats_city.append(sub[filt_city])
    if candidats_city:
        candidats_city = pd.concat(candidats_city, ignore_index=True)
    else:
        candidats_city = pd.DataFrame()

    if DEBUG:
        if not candidats_city.empty:
            noms_city = candidats_city[COLB_NOM].tolist()
            debug_print(f"[Ligne {idxA}] Candidats après filtre VILLE SEULE ('{cityA}') → Noms disponibles = {noms_city}")
            noms_city2 = candidats_city[COLB_NOM2].tolist()
            debug_print(f"[Ligne {idxA}] Candidats après filtre VILLE SEULE nom2 ('{cityA}') → Noms2 disponibles = {noms_city2}")
        else:
            debug_print(f"[Ligne {idxA}] Aucun candidat pour VILLE SEULE ('{cityA}')")

    if not candidats_city.empty and tokensA:
        codes_city = do_token_match(candidats_city, tokensA, "City", debug_pref=prefix + "  [City] ")
        if codes_city:
            if len(codes_city) == 1:
                if DEBUG:
                    debug_print(f"{prefix}  → Correspondance unique (ville seul) : {codes_city[0]}")
                return codes_city[0], "1 - réussi"
            else:
                if DEBUG:
                    debug_print(f"{prefix}  → Plusieurs correspondances (ville seul) : {codes_city} → PLUSIEURS CAS")
                return "PLUSIEURS CAS", "PLUSIEURS CAS"
        else:
            if DEBUG:
                debug_print(f"{prefix}  → Aucun code trouvé (ville seul)")

    # ――― Aucune correspondance ――――――――――――――
    if DEBUG:
        debug_print(f"{prefix}Aucune correspondance trouvée dans aucune étape → 0 - pas bon")
    return "", "0 - pas bon"

def main():
    # Initialiser le fichier de debug
    if DEBUG:
        init_debug_log(DEBUG_LOG)

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
    if DEBUG:
        debug_print("==> Colonne 'Mots significatifs' générée dans Data")

    # 2) Normaliser "Département" (2 chiffres) et "Ville" (nom simple) dans Data
    dfA[COLA_DEPT] = dfA[COLA_DEPT].astype(str).str.strip().str.zfill(2)
    dfA["City_norm_A"] = dfA[COLA_VILLE].apply(normalize_data_city)
    if DEBUG:
        debug_print("==> Colonnes 'Département' et 'City_norm_A' créées dans Data")

    # 3) Préparer DF : extraire code département + normaliser ville
    dfB["Dept"]      = dfB[COLB_VILLE].astype(str).str.strip().str[:2].str.zfill(2)
    dfB["City_norm"] = dfB[COLB_VILLE].apply(normalize_df_city)
    if DEBUG:
        debug_print("==> Colonnes 'Dept' et 'City_norm' créées dans DF")

    # Grouper DF par département
    dfB_grouped  = dfB.groupby("Dept")
    dfB_indexed  = {dept: sub.reset_index(drop=True) for dept, sub in dfB_grouped}
    if DEBUG:
        debug_print("==> DF indexé par 'Dept'")

    # 4) Parcourir chaque ligne Data, faire correspondance
    codes_fin, statuts = [], []
    for idxA, rowA in dfA.iterrows():
        if DEBUG:
            debug_print(f"\n--> Traitement de la ligne {idxA} de Data")
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
    if DEBUG:
        debug_print("=== DEBUG LOG END ===")

if __name__ == "__main__":
    main()
