"""
Processeur principal pour le matching des établissements de santé
"""

import pandas as pd
import time
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fuzzywuzzy import fuzz
from config import *
from establishment_utils import (
    get_establishment_name_and_type, 
    clean_name, 
    detect_establishment_type,
    get_best_candidate_name
)
from ai_service import ai_compare_hospital_names_batch


class HospitalMatcher:
    """
    Classe principale pour le matching des établissements de santé
    """
    
    def __init__(self):
        self.total_ai_requests = 0
        self.processed_hospitals = 0
        self.df_lp = None
        self.df_sc = None
    
    def load_data(self):
        """
        Charge les données depuis les fichiers Excel
        """
        print("Chargement des données...")
        try:
            self.df_lp = pd.read_excel(PATH_TABLE_A)
            self.df_sc = pd.read_excel(PATH_TABLE_B)
            print(f"✅ Données chargées: {len(self.df_lp)} établissements à traiter, {len(self.df_sc)} références")
        except Exception as e:
            print(f"❌ Erreur lors du chargement des données: {e}")
            raise
    
    def process_all_hospitals(self):
        """
        Traite tous les hôpitaux du fichier
        """
        if self.df_lp is None or self.df_sc is None:
            raise ValueError("Les données doivent être chargées avant le traitement")
        
        print(f"\n🏥 Démarrage du traitement de {len(self.df_lp)} établissements...")
        
        for idx, row in self.df_lp.iterrows():
            self._process_single_hospital(idx, row)
        
        self._print_final_statistics()
    
    def _process_single_hospital(self, idx, row):
        """
        Traite un seul hôpital
        """
        self.processed_hospitals += 1
        print(f"\n=== Traitement {self.processed_hospitals}/{len(self.df_lp)} - Index: {idx} ===")
        
        # Obtenir le nom et le type d'établissement
        establishment_name, establishment_type = get_establishment_name_and_type(row)
        
        if not establishment_name:
            print(f"❌ Aucun nom d'établissement trouvé pour la ligne {idx}")
            self.df_lp.at[idx, COLA_FINESS] = None
            return
        
        print(f"🔍 Recherche pour {establishment_type.upper()}: {establishment_name}")
        print(f"📍 Ville: {row[COLA_VILLE]}")
        
        # Filtrer les candidats par ville
        candidates = self._find_candidates_in_city(row, establishment_name, establishment_type)
        
        if not candidates:
            print(f"❌ Aucun établissement trouvé dans la ville {row[COLA_VILLE]}")
            self.df_lp.at[idx, COLA_FINESS] = None
            return
        
        # Essayer le matching
        selected_finess = self._match_establishment(establishment_name, establishment_type, candidates)
        
        if selected_finess:
            self.df_lp.at[idx, COLA_FINESS] = selected_finess
            print(f"✅ FINESS assigné: {selected_finess}")
        else:
            self.df_lp.at[idx, COLA_FINESS] = None
            print(f"❌ Aucun match trouvé")
        
        print(f"📊 Requêtes IA utilisées: {self.total_ai_requests}")
        
        # Petite pause pour éviter la surcharge API
        if self.total_ai_requests > 0 and self.total_ai_requests % 10 == 0:
            print("⏳ Pause de 5 secondes pour éviter la surcharge API...")
            time.sleep(5)
    
    def _find_candidates_in_city(self, row, establishment_name, establishment_type):
        """
        Trouve tous les candidats dans la même ville
        """
        city_filter = str(row[COLA_VILLE]).replace(" ST ", " SAINT ").upper()
        df_sc_filtered = self.df_sc[
            self.df_sc[COLB_VILLE].str.replace(" ST ", " SAINT ").str.upper().str.contains(city_filter, na=False)
        ]
        
        if df_sc_filtered.empty:
            return []
        
        print(f"🏢 {len(df_sc_filtered)} établissements trouvés dans la ville")
        
        # Préparer les candidats avec filtrage par type si possible
        all_candidates = []
        same_type_candidates = []
        
        for idx2, row_sc in df_sc_filtered.iterrows():
            best_name = get_best_candidate_name(row_sc, [COLB_NOM_SC, COLB_NOM, COLB_NOM_2])
            candidate_type = detect_establishment_type(best_name)
            candidate_info = (best_name, row_sc[COLB_FIN_SCS])
            
            all_candidates.append(candidate_info)
            
            # Garder séparément les candidats du même type
            if candidate_type == establishment_type:
                same_type_candidates.append(candidate_info)
        
        # Choisir les candidats à utiliser (priorité au même type)
        candidates = same_type_candidates if same_type_candidates else all_candidates
        
        if same_type_candidates:
            print(f"🎯 Trouvé {len(same_type_candidates)} candidats du même type ({establishment_type})")
        else:
            print(f"⚠️  Aucun candidat du même type, utilisation de tous les {len(all_candidates)} candidats")
        
        return candidates
    
    def _match_establishment(self, establishment_name, establishment_type, candidates):
        """
        Effectue le matching d'un établissement avec les candidats
        """
        establishment_name_clean = clean_name(establishment_name)
        
        # Essayer d'abord le matching fuzzy
        best_match_idx, best_score = self._fuzzy_match(establishment_name_clean, candidates)
        
        if best_score > FUZZY_THRESHOLD:
            selected_finess = candidates[best_match_idx][1]
            print(f"🎯 Match fuzzy trouvé (score: {best_score})")
            print(f"   {establishment_name_clean} -> {candidates[best_match_idx][0]}")
            return selected_finess
        else:
            # Utiliser l'IA pour choisir
            print(f"🤖 Score fuzzy insuffisant ({best_score}), utilisation de l'IA...")
            self.total_ai_requests += 1
            
            selected_idx = ai_compare_hospital_names_batch(
                establishment_name_clean, candidates, establishment_type
            )
            selected_finess = candidates[selected_idx][1]
            
            print(f"🎯 Match IA sélectionné:")
            print(f"   {establishment_name_clean} -> {candidates[selected_idx][0]}")
            return selected_finess
    
    def _fuzzy_match(self, establishment_name_clean, candidates):
        """
        Effectue un matching fuzzy et retourne le meilleur score
        """
        best_match_idx = -1
        best_score = 0
        
        for i, (candidate_name, finess) in enumerate(candidates):
            score = fuzz.ratio(establishment_name_clean, candidate_name)
            if score > best_score:
                best_score = score
                best_match_idx = i
        
        return best_match_idx, best_score
    
    def _print_final_statistics(self):
        """
        Affiche les statistiques finales
        """
        print(f"\n🎉 === RÉSULTATS FINAUX ===")
        print(f"📊 Total d'établissements traités: {self.processed_hospitals}")
        print(f"🤖 Total de requêtes IA utilisées: {self.total_ai_requests}")
        
        matches_found = self.df_lp[COLA_FINESS].notna().sum()
        success_rate = matches_found / len(self.df_lp) * 100
        
        print(f"✅ Matches trouvés: {matches_found}/{len(self.df_lp)} ({success_rate:.1f}%)")
    
    def save_results(self):
        """
        Sauvegarde les résultats dans un fichier Excel
        """
        print(f"\n💾 Enregistrement des résultats...")
        
        try:
            import os
            if not os.path.exists(os.path.dirname(OUTPUT_PATH)):
                os.makedirs(os.path.dirname(OUTPUT_PATH))
                
            self.df_lp.to_excel(OUTPUT_PATH, index=False)
            print(f"✅ Résultats enregistrés dans {OUTPUT_PATH}")
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement: {e}")
            raise
