"""
Utilitaires pour la détection et le nettoyage des noms d'établissements
"""

import pandas as pd
import re
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import COLA_NOM_HOPITAL, COLA_NOM_CLINIQUE, REPLACE


def detect_establishment_type(name):
    """
    Détecte le type d'établissement (hôpital ou clinique) basé sur le nom
    
    Args:
        name (str): Nom de l'établissement
        
    Returns:
        str: "hopital", "clinique" ou "unknown"
    """
    if pd.isna(name) or name == "":
        return "unknown"
    
    name_upper = str(name).upper()
    
    # Mots-clés pour les cliniques
    clinic_keywords = ["CLINIQUE", "CLINIC", "POLYCLINIQUE", "POLICLINIQUE"]
    
    # Mots-clés pour les hôpitaux
    hospital_keywords = [
        "HOPITAL", "HÔPITAL", "CHU", "CHR", "CH ", 
        "CENTRE HOSPITALIER", "HOSPITAL"
    ]
    
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
    
    Args:
        row: Ligne du DataFrame pandas
        
    Returns:
        tuple: (nom_etablissement, type_etablissement)
    """
    # Vérifier d'abord la colonne hôpital
    if pd.notna(row[COLA_NOM_HOPITAL]) and str(row[COLA_NOM_HOPITAL]).strip() != "":
        return str(row[COLA_NOM_HOPITAL]), "hopital"
    
    # Puis vérifier la colonne clinique
    if pd.notna(row[COLA_NOM_CLINIQUE]) and str(row[COLA_NOM_CLINIQUE]).strip() != "":
        return str(row[COLA_NOM_CLINIQUE]), "clinique"
    
    return "", "unknown"


def clean_name(name):
    """
    Nettoie un nom d'établissement en appliquant les remplacements standard
    
    Args:
        name (str): Nom à nettoyer
        
    Returns:
        str: Nom nettoyé
    """
    if pd.isna(name):
        return ""
    
    cleaned = str(name).upper()
    
    # Appliquer les remplacements
    for old, new in REPLACE.items():
        cleaned = cleaned.replace(old, new)
    
    # Remplacer ST par SAINT
    cleaned = cleaned.replace(" ST ", " SAINT ")
    
    # Nettoyer les espaces multiples
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def get_best_candidate_name(row_sc, columns):
    """
    Choisit le meilleur nom de candidat parmi plusieurs colonnes
    
    Args:
        row_sc: Ligne du DataFrame des candidats
        columns (list): Liste des colonnes à considérer
        
    Returns:
        str: Meilleur nom trouvé
    """
    names = []
    for col in columns:
        if pd.notna(row_sc[col]) and str(row_sc[col]).strip():
            cleaned = clean_name(row_sc[col])
            if cleaned:
                names.append(cleaned)
    
    # Retourner le nom le plus long (généralement plus complet)
    return max(names, key=len) if names else "INCONNU"
