import pandas as pd
import os
import sys
import re
import time
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import google.generativeai as genai
import AIRateLimiter

# Configure Google AI
genai.configure(api_key="AIzaSyBfQjj1pNx0yDlXUSo4tdWUe5RcE35ON6o")
model = genai.GenerativeModel('gemini-1.5-flash')

rate_limiter = AIRateLimiter()


PATH_TABLE_A = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\data_propre_ext_LP-167_Acc_Risque.xlsx"
PATH_TABLE_B = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\Résultats\DONNEES_REUNIES_COMPLETE.xlsx"
OUTPUT_PATH  = r"C:\Users\LeviWEBERT\OneDrive - ALBUS PARTNERS\Bureau\Scan Medecine\TABLEAU à TRAIté\résultat_matches_finessR1_AI.xlsx"

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

def ai_compare_hospital_names_batch(hospital_name, candidates_list, establishment_type="unknown"):
    """
    Compare un nom d'hôpital avec plusieurs candidats en une seule requête IA
    pour optimiser l'utilisation des tokens
    """
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.wait_time()
        print(f"Limite API atteinte. Attente de {wait_time} secondes...")
        time.sleep(wait_time + 1)
    
    try:
        # Construire la liste des candidats avec leur type détecté
        candidates_text = ""
        for i, (name, finess) in enumerate(candidates_list, 1):
            candidate_type = detect_establishment_type(name)
            type_info = f" [TYPE: {candidate_type.upper()}]" if candidate_type != "unknown" else ""
            candidates_text += f"- Option {i}: \"{name}\"{type_info} (FINESS: {finess})\n"
        
        # Définir le type d'établissement recherché
        establishment_info = ""
        if establishment_type == "hopital":
            establishment_info = "Il s'agit d'un HÔPITAL, priorise les établissements de type hôpital (CHU, CH, HOPITAL, etc.)."
        elif establishment_type == "clinique":
            establishment_info = "Il s'agit d'une CLINIQUE, priorise les établissements de type clinique (CLINIQUE, POLYCLINIQUE, etc.)."
        else:
            establishment_info = "Type d'établissement non déterminé, utilise ton meilleur jugement."
        
        prompt = f"""
        Tu es un expert en analyse de données médicales. Tu dois OBLIGATOIREMENT choisir la meilleure correspondance parmi les options données.
        
        Nom de l'établissement recherché: "{hospital_name}"
        Type d'établissement: {establishment_type.upper()}
        
        {establishment_info}
        
        Options disponibles:
        {candidates_text}
        
        Règles STRICTES:
        - Tu DOIS choisir une option, même si la correspondance n'est pas parfaite
        - PRIORITÉ ABSOLUE: Choisis un établissement du même type (hôpital avec hôpital, clinique avec clinique)
        - Si aucun établissement du même type, choisis le plus proche par nom
        - Ignore les différences mineures (accents, espaces, tirets, ponctuation)
        - "ST" = "SAINT", "CHU" = "CENTRE HOSPITALIER UNIVERSITAIRE"
        - "CH" = "CENTRE HOSPITALIER", "HOPITAL" = "HÔPITAL"
        - "CLINIQUE" = "CLINIC", "POLYCLINIQUE" = "POLICLINIQUE"
        - Les abréviations sont acceptées (ex: "CARDIO" pour "CARDIOLOGIE")
        - En cas de doute entre établissements du même type, choisis le nom le plus détaillé
        
        IMPORTANT: Tu dois TOUJOURS retourner un numéro d'option, JAMAIS "NO_MATCH"
        
        Réponds uniquement par le numéro de l'option choisie (1, 2, 3, etc.)
        """
        
        if rate_limiter.make_request():
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # Extraire le numéro de l'option
            try:
                option_num = int(result)
                if 1 <= option_num <= len(candidates_list):
                    return option_num - 1  # Retourner l'index (0-based)
                else:
                    print(f"IA a retourné un numéro invalide: {result}, utilise la première option")
                    return 0
            except ValueError:
                print(f"IA a retourné une réponse non numérique: {result}, utilise la première option")
                return 0
        else:
            print("Impossible de faire une requête IA, utilise la première option")
            return 0
            
    except Exception as e:
        print(f"Erreur IA: {e}, utilise la première option")
        return 0

def detect_establishment_type(name):
    """
    Détecte le type d'établissement (hôpital ou clinique) basé sur le nom
    """
    if pd.isna(name) or name == "":
        return "unknown"
    
    name_upper = str(name).upper()
    
    # Mots-clés pour les cliniques
    clinic_keywords = ["CLINIQUE", "CLINIC", "POLYCLINIQUE", "POLICLINIQUE"]
    
    # Mots-clés pour les hôpitaux
    hospital_keywords = ["HOPITAL", "HÔPITAL", "CHU", "CHR", "CH ", "CENTRE HOSPITALIER", "HOSPITAL"]
    
    # Vérifier d'abord les cliniques
    for keyword in clinic_keywords:
        if keyword in name_upper:
            return "clinique"
    
    # Puis vérifier les hôpitaux
    for keyword in hospital_keywords:
        if keyword in name_upper:
            return "hopital"
    
    return "unknown"

def get_establishment_name_and_type(row):
    """
    Retourne le nom de l'établissement et son type à partir d'une ligne du DataFrame
    """
    # Vérifier d'abord la colonne hôpital
    if pd.notna(row[COLA_NOM_HOPITAL]) and str(row[COLA_NOM_HOPITAL]).strip() != "":
        return str(row[COLA_NOM_HOPITAL]), "hopital"
    
    # Puis vérifier la colonne clinique
    if pd.notna(row[COLA_NOM_CLINIQUE]) and str(row[COLA_NOM_CLINIQUE]).strip() != "":
        return str(row[COLA_NOM_CLINIQUE]), "clinique"
    
    return "", "unknown"

df_lp = pd.read_excel(PATH_TABLE_A)
df_sc = pd.read_excel(PATH_TABLE_B)

# Compteurs pour la gestion des requêtes
total_ai_requests = 0
processed_hospitals = 0

print(f"Démarrage du traitement de {len(df_lp)} hôpitaux...")

for idx, row in df_lp.iterrows():
    processed_hospitals += 1
    print(f"\n=== Traitement {processed_hospitals}/{len(df_lp)} - Index: {idx} ===")
    
    # Obtenir le nom et le type d'établissement
    establishment_name, establishment_type = get_establishment_name_and_type(row)
    
    if not establishment_name:
        print(f"Aucun nom d'établissement trouvé pour la ligne {idx}")
        df_lp.at[idx, COLA_FINESS] = None
        continue
    
    print(f"Recherche pour {establishment_type.upper()}: {establishment_name} dans la ville: {row[COLA_VILLE]}")
    
    # Filtrer par ville
    city_filter = str(row[COLA_VILLE]).replace(" ST ", " SAINT ").upper()
    df_sc_filtered = df_sc[
        df_sc[COLB_VILLE].str.replace(" ST ", " SAINT ").str.upper().str.contains(city_filter, na=False)
    ]    
    if df_sc_filtered.empty:
        print(f"Aucun établissement trouvé pour {establishment_name} dans la ville {row[COLA_VILLE]}")
        df_lp.at[idx, COLA_FINESS] = None
        continue
    
    print(f"{len(df_sc_filtered)} établissements trouvés dans la ville {row[COLA_VILLE]}")
    
    # Préparer les candidats pour l'IA avec filtrage par type si possible
    all_candidates = []
    same_type_candidates = []
    
    for idx2, row_sc in df_sc_filtered.iterrows():
        # Nettoyer les noms
        nomscs = str(row_sc[COLB_NOM_SC]).upper() if pd.notna(row_sc[COLB_NOM_SC]) else ""
        nom = str(row_sc[COLB_NOM]).upper() if pd.notna(row_sc[COLB_NOM]) else ""
        nom2 = str(row_sc[COLB_NOM_2]).upper() if pd.notna(row_sc[COLB_NOM_2]) else ""
        
        # Appliquer les remplacements
        for mot in REPLACE:
            nomscs = nomscs.replace(mot, " ")
            nom = nom.replace(mot, " ")
            nom2 = nom2.replace(mot, " ")
        
        # Choisir le meilleur nom (le plus long/complet)
        best_name = max([nomscs, nom, nom2], key=len) if any([nomscs, nom, nom2]) else "INCONNU"
        
        candidate_type = detect_establishment_type(best_name)
        candidate_info = (best_name, row_sc[COLB_FIN_SCS])
        
        all_candidates.append(candidate_info)
        
        # Garder séparément les candidats du même type
        if candidate_type == establishment_type:
            same_type_candidates.append(candidate_info)
    
    # Choisir les candidats à utiliser (priorité au même type)
    candidates = same_type_candidates if same_type_candidates else all_candidates
    
    if same_type_candidates:
        print(f"Trouvé {len(same_type_candidates)} candidats du même type ({establishment_type})")
    else:
        print(f"Aucun candidat du même type, utilisation de tous les {len(all_candidates)} candidats")
    
    # Essayer d'abord une correspondance exacte ou fuzzy
    establishment_name_clean = establishment_name.upper()
    for mot in REPLACE:
        establishment_name_clean = establishment_name_clean.replace(mot, " ")
    
    best_match_idx = -1
    best_score = 0
    
    # Recherche fuzzy d'abord
    for i, (candidate_name, finess) in enumerate(candidates):
        score = fuzz.ratio(establishment_name_clean, candidate_name)
        if score > best_score:
            best_score = score
            best_match_idx = i
    
    # Si score fuzzy > 85, utiliser ce match
    if best_score > 85:
        selected_finess = candidates[best_match_idx][1]
        print(f"Match fuzzy trouvé (score: {best_score}): {establishment_name_clean} -> {candidates[best_match_idx][0]}")
        df_lp.at[idx, COLA_FINESS] = selected_finess
    else:
        # Utiliser l'IA pour choisir
        print(f"Score fuzzy insuffisant ({best_score}), utilisation de l'IA...")
        total_ai_requests += 1
        
        selected_idx = ai_compare_hospital_names_batch(establishment_name_clean, candidates, establishment_type)
        selected_finess = candidates[selected_idx][1]
        
        print(f"Match IA sélectionné: {establishment_name_clean} -> {candidates[selected_idx][0]} (FINESS: {selected_finess})")
        df_lp.at[idx, COLA_FINESS] = selected_finess
    
    print(f"Requêtes IA utilisées: {total_ai_requests}")
    
    # Petite pause pour éviter de surcharger l'API
    if total_ai_requests > 0 and total_ai_requests % 10 == 0:
        print("Pause de 5 secondes pour éviter la surcharge API...")
        time.sleep(5)
# Enregistrer le DataFrame modifié
print(f"\n=== RÉSULTATS FINAUX ===")
print(f"Total d'hôpitaux traités: {processed_hospitals}")
print(f"Total de requêtes IA utilisées: {total_ai_requests}")
matches_found = df_lp[COLA_FINESS].notna().sum()
print(f"Matches trouvés: {matches_found}/{len(df_lp)} ({matches_found/len(df_lp)*100:.1f}%)")

print("\nEnregistrement des résultats...")
if not os.path.exists(os.path.dirname(OUTPUT_PATH)):
    os.makedirs(os.path.dirname(OUTPUT_PATH))
try:
    df_lp.to_excel(OUTPUT_PATH, index=False)
    print(f"Résultats enregistrés dans {OUTPUT_PATH}")
except Exception as e:
    print(f"Erreur lors de l'enregistrement du fichier : {e}")
    sys.exit(1)

