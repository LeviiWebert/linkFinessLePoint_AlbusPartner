"""
Service IA pour la comparaison intelligente des noms d'établissements
"""

import sys
import os
import google.generativeai as genai

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import GOOGLE_API_KEY, MODEL_NAME
from rate_limiter import AIRateLimiter
from establishment_utils import detect_establishment_type


# Configuration Google AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Instance du gestionnaire de taux
rate_limiter = AIRateLimiter()


def ai_compare_hospital_names_batch(hospital_name, candidates_list, establishment_type="unknown"):
    """
    Compare un nom d'hôpital avec plusieurs candidats en une seule requête IA
    pour optimiser l'utilisation des tokens
    
    Args:
        hospital_name (str): Nom de l'établissement recherché
        candidates_list (list): Liste de tuples (nom_candidat, finess)
        establishment_type (str): Type d'établissement ("hopital", "clinique", "unknown")
        
    Returns:
        tuple: (index du candidat sélectionné, nom du candidat, score de confiance)
    """
    # Vérifier et attendre si nécessaire
    rate_limiter.wait_if_needed()
    
    try:
        # Construire la liste des candidats SANS afficher le type détecté
        candidates_text = ""
        for i, (name, finess) in enumerate(candidates_list, 1):
            # Supprimer l'affichage du type détecté par le système
            candidates_text += f"- Option {i}: \"{name}\" (FINESS: {finess})\n"
        
        # Définir le type d'établissement recherché
        establishment_info = _get_establishment_info(establishment_type)
        
        prompt = f"""
        Tu es un expert en analyse de données médicales. Tu dois OBLIGATOIREMENT choisir la meilleure correspondance parmi les options données.
        
        Nom de l'établissement recherché: "{hospital_name}"
        
        {establishment_info}
        
        Options disponibles:
        {candidates_text}
        
        Règles STRICTES:
        - Tu DOIS choisir une option, même si la correspondance n'est pas parfaite
        - Si aucun établissement du même type, choisis le plus proche par nom
        - Ignore les différences mineures (accents, espaces, tirets, ponctuation)
        - Les abréviations sont acceptées (ex: "CARDIO" pour "CARDIOLOGIE")
        - En cas de doute entre établissements du même type, choisis le nom le plus détaillé
        - les libelles comporte aussi la ville et le département, ne les prends pas en compte dans la comparaison
        Cependant si la correspondance est vraiment pas pareil, tu peux retourner 0 pour indiquer "AUCUNE CORRESPONDANCE".
        
        Réponds uniquement par le numéro de l'option choisie (1, 2, 3, etc.)
        """
        
        if rate_limiter.make_request():
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # Extraire le numéro de l'option
            try:
                option_num = int(result)
                if 1 <= option_num <= len(candidates_list):
                    selected_index = option_num - 1
                    selected_candidate = candidates_list[selected_index]
                    
                    # Vérification de cohérence supplémentaire
                    confidence_score = ai_verify_match_coherence(hospital_name, selected_candidate[0])
                    
                    return selected_index, selected_candidate[0], confidence_score
                elif option_num == 0:
                    return -1, "AUCUNE CORRESPONDANCE", 0
                else:
                    print(f"IA a retourné un numéro invalide: {result}, utilise la première option")
                    return 0, candidates_list[0][0], 50
            except ValueError:
                print(f"IA a retourné une réponse non numérique: {result}, utilise la première option")
                return 0, candidates_list[0][0], 50
        else:
            print("Impossible de faire une requête IA, utilise la première option")
            return 0, candidates_list[0][0], 50
            
    except Exception as e:
        print(f"Erreur IA: {e}, utilise la première option")
        return 0, candidates_list[0][0], 50


def ai_verify_match_coherence(original_name, matched_name):
    """
    Vérifie la cohérence du match avec un prompt de vérification supplémentaire
    
    Args:
        original_name (str): Nom original de l'établissement
        matched_name (str): Nom de l'établissement matché
        
    Returns:
        int: Score de confiance (0-100)
    """
    rate_limiter.wait_if_needed()
    
    try:
        prompt = f"""
        Tu es un expert en validation de correspondances d'établissements de santé.
        
        Établissement original: "{original_name}"
        Établissement matché: "{matched_name}"
        
        Évalue la cohérence de cette correspondance sur une échelle de 0 à 100:
        
        - 90-100: Correspondance parfaite ou quasi-parfaite
        - 80-89: Correspondance très probable (même établissement, variations mineures)
        - 70-79: Correspondance probable (possibles abréviations ou différences d'écriture)
        - 60-69: Correspondance incertaine mais plausible
        - 40-59: Correspondance douteuse
        - 20-39: Correspondance peu probable
        - 0-19: Correspondance très improbable
        
        Critères d'évaluation:
        - Similarité des noms (ignorant ponctuation, accents, espaces)
        - Cohérence du type d'établissement (hôpital/clinique)
        - Présence d'abréviations communes dans le domaine médical
        - Ne prends pas en compte la logique géographique mais seulement les mots similaire ou exactement pareil
        
        Réponds uniquement par un nombre entre 0 et 100.
        """
        
        if rate_limiter.make_request():
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            try:
                confidence = int(result)
                # S'assurer que le score est dans la plage 0-100
                return max(0, min(100, confidence))
            except ValueError:
                print(f"Erreur parsing score confiance: {result}, utilise 75")
                return 75
        else:
            return 75  # Score par défaut si impossible de faire la requête
            
    except Exception as e:
        print(f"Erreur vérification cohérence: {e}")
        return 75


def _get_establishment_info(establishment_type):
    """
    Retourne les informations contextuelles pour le type d'établissement
    """
    if establishment_type == "hopital":
        return "Il s'agit d'un HÔPITAL, privilégie les établissements de type hôpital (CHU, CH, HOPITAL, etc.)."
    elif establishment_type == "clinique":
        return "Il s'agit d'une CLINIQUE, privilégie les établissements de type clinique (CLINIQUE, POLYCLINIQUE, etc.)."
    else:
        return "Type d'établissement non déterminé, utilise ton meilleur jugement."
        return "Type d'établissement non déterminé, utilise ton meilleur jugement."
