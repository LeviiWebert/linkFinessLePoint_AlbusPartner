"""
Utilitaires pour la normalisation géographique
"""

import re
import unicodedata


def normalize_city_name(city_name):
    """
    Normalise un nom de ville pour améliorer le matching
    
    Args:
        city_name (str): Nom de ville à normaliser
        
    Returns:
        str: Nom de ville normalisé
    """
    if not city_name or str(city_name).strip() == "" or str(city_name).upper() == "NAN":
        return ""
    
    # Convertir en string et en majuscules
    normalized = str(city_name).upper().strip()
    
    # Supprimer les accents
    normalized = remove_accents(normalized)
    
    # Normaliser SAINT/ST
    normalized = re.sub(r'\bSAINT\b', 'ST', normalized)
    normalized = re.sub(r'\bSAINTE\b', 'STE', normalized)
    
    # Normaliser les tirets et espaces
    normalized = re.sub(r'[-\s]+', ' ', normalized)
    
    # Supprimer les caractères spéciaux sauf espaces
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Nettoyer les espaces multiples
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def normalize_department_name(dept_name):
    """
    Normalise un nom de département
    
    Args:
        dept_name (str): Nom ou code de département
        
    Returns:
        str: Département normalisé
    """
    if not dept_name or str(dept_name).strip() == "" or str(dept_name).upper() == "NAN":
        return ""
    
    normalized = str(dept_name).upper().strip()
    
    # Si c'est déjà un code numérique, le garder
    if normalized.isdigit():
        return normalized.zfill(2)  # Assurer 2 chiffres (ex: "1" -> "01")
    
    # Supprimer les accents
    normalized = remove_accents(normalized)
    
    # Dictionnaire des correspondances communes
    dept_mapping = {
        'AIN': '01',
        'AISNE': '02',
        'ALLIER': '03',
        'ALPES DE HAUTE PROVENCE': '04',
        'HAUTES ALPES': '05',
        'ALPES MARITIMES': '06',
        'ARDECHE': '07',
        'ARDENNES': '08',
        'ARIEGE': '09',
        'AUBE': '10',
        'BOUCHES DU RHONE': '13',
        'CALVADOS': '14',
        'CANTAL': '15',
        'CHARENTE': '16',
        'CHARENTE MARITIME': '17',
        'CHER': '18',
        'CORREZE': '19',
        'CORSE DU SUD': '2A',
        'HAUTE CORSE': '2B',
        'COTE D OR': '21',
        'COTES D ARMOR': '22',
        'CREUSE': '23',
        'DORDOGNE': '24',
        'DOUBS': '25',
        'DROME': '26',
        'EURE': '27',
        'EURE ET LOIR': '28',
        'FINISTERE': '29',
        'GARD': '30',
        'HAUTE GARONNE': '31',
        'GERS': '32',
        'GIRONDE': '33',
        'HERAULT': '34',
        'ILLE ET VILAINE': '35',
        'INDRE': '36',
        'INDRE ET LOIRE': '37',
        'ISERE': '38',
        'JURA': '39',
        'LANDES': '40',
        'LOIR ET CHER': '41',
        'LOIRE': '42',
        'HAUTE LOIRE': '43',
        'LOIRE ATLANTIQUE': '44',
        'LOIRET': '45',
        'LOT': '46',
        'LOT ET GARONNE': '47',
        'LOZERE': '48',
        'MAINE ET LOIRE': '49',
        'MANCHE': '50',
        'MARNE': '51',
        'HAUTE MARNE': '52',
        'MAYENNE': '53',
        'MEURTHE ET MOSELLE': '54',
        'MEUSE': '55',
        'MORBIHAN': '56',
        'MOSELLE': '57',
        'NIEVRE': '58',
        'NORD': '59',
        'OISE': '60',
        'ORNE': '61',
        'PAS DE CALAIS': '62',
        'PUY DE DOME': '63',
        'PYRENEES ATLANTIQUES': '64',
        'HAUTES PYRENEES': '65',
        'PYRENEES ORIENTALES': '66',
        'BAS RHIN': '67',
        'HAUT RHIN': '68',
        'RHONE': '69',
        'HAUTE SAONE': '70',
        'SAONE ET LOIRE': '71',
        'SARTHE': '72',
        'SAVOIE': '73',
        'HAUTE SAVOIE': '74',
        'PARIS': '75',
        'SEINE MARITIME': '76',
        'SEINE ET MARNE': '77',
        'YVELINES': '78',
        'DEUX SEVRES': '79',
        'SOMME': '80',
        'TARN': '81',
        'TARN ET GARONNE': '82',
        'VAR': '83',
        'VAUCLUSE': '84',
        'VENDEE': '85',
        'VIENNE': '86',
        'HAUTE VIENNE': '87',
        'VOSGES': '88',
        'YONNE': '89',
        'TERRITOIRE DE BELFORT': '90',
        'ESSONNE': '91',
        'HAUTS DE SEINE': '92',
        'SEINE SAINT DENIS': '93',
        'VAL DE MARNE': '94',
        'VAL D OISE': '95'
    }
    
    return dept_mapping.get(normalized, normalized)


def remove_accents(text):
    """
    Supprime les accents d'un texte
    
    Args:
        text (str): Texte avec accents
        
    Returns:
        str: Texte sans accents
    """
    if not text:
        return ""
    
    # Normaliser unicode puis supprimer les marques diacritiques
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    return without_accents


def create_geo_filter_key(city, department):
    """
    Crée une clé de filtrage géographique combinée
    
    Args:
        city (str): Nom de ville
        department (str): Code/nom de département
        
    Returns:
        str: Clé de filtrage normalisée
    """
    norm_city = normalize_city_name(city)
    norm_dept = normalize_department_name(department)
    
    return f"{norm_dept}_{norm_city}"


def cities_match(city1, city2, department1=None, department2=None):
    """
    Vérifie si deux villes correspondent (avec normalisation)
    
    Args:
        city1, city2 (str): Noms de villes à comparer
        department1, department2 (str): Départements optionnels
        
    Returns:
        bool: True si les villes correspondent
    """
    norm_city1 = normalize_city_name(city1)
    norm_city2 = normalize_city_name(city2)
    
    if not norm_city1 or not norm_city2:
        return False
    
    # Vérification exacte
    if norm_city1 == norm_city2:
        return True
    
    # Vérification contenue (pour les cas comme "PARIS 15" contient "PARIS")
    if norm_city1 in norm_city2 or norm_city2 in norm_city1:
        # Si départements fournis, vérifier aussi la cohérence
        if department1 and department2:
            norm_dept1 = normalize_department_name(department1)
            norm_dept2 = normalize_department_name(department2)
            return norm_dept1 == norm_dept2
        return True
    
    return False
