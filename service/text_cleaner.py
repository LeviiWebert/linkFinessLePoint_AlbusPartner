import re
import unicodedata
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
#                   CONSTANTES
# ──────────────────────────────────────────────────────────────────────────────

# Stopwords français pour filtrer les mots non significatifs
STOPWORDS = {
    "CENTRE", "GENERAL", "REGIONAL", "UNIVERSITAIRE", "PUBLIC", "PRIVE",
    "ETABLISSEMENT", "INSTITUTION", "FONDATION", "ASSOCIATION", "MAISON",
    "RESIDENCE", "GROUPE", "SECTEUR", "UNITE", "SERVICE", "DEPARTEMENT",
    "MEDICO", "SOCIAL", "SANTE", "SOINS", "MEDICAL", "MEDICALE"
}

# Abréviations hospitalières communes
HOSP_ABBREV = {
    "CHU", "CHR", "CHI", "CHS", "CHG", "CH", "CHRU", "APHP", "HCL", 
    "GHL", "GHT", "GHRMSA", "GCSMS", "HAD", "SSR", "EHPAD", "USLD"
}


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