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
        int: Index du candidat sélectionné
    """
    # Vérifier et attendre si nécessaire
    rate_limiter.wait_if_needed()
    
    try:
        # Construire la liste des candidats avec leur type détecté
        candidates_text = ""
        for i, (name, finess) in enumerate(candidates_list, 1):
            candidate_type = detect_establishment_type(name)
            type_info = f" [TYPE: {candidate_type.upper()}]" if candidate_type != "unknown" else ""
            candidates_text += f"- Option {i}: \"{name}\"{type_info} (FINESS: {finess})\n"
        
        # Définir le type d'établissement recherché
        establishment_info = _get_establishment_info(establishment_type)
        
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
