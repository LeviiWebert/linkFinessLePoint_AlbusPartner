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
from geo_utils import normalize_city_name, normalize_department_name


class HospitalMatcher:
    """
    Classe principale pour le matching des établissements de santé
    """
    
    def __init__(self, reset_history=False, differentiate_types=False, forced_type=None):
        self.total_ai_requests = 0
        self.processed_hospitals = 0
        self.df_lp = None
        self.df_sc = None
        self.last_save_index = 0  # Pour tracking des sauvegardes
        self.reset_history = reset_history
        self.differentiate_types = differentiate_types
        self.forced_type = forced_type  # None, "hopital", "clinique"
    
    def load_data(self):
        """
        Charge les données depuis les fichiers Excel et vérifie le travail déjà fait
        """
        print("📂 Chargement des données...")
        try:
            self.df_lp = pd.read_excel(PATH_TABLE_A)
            self.df_sc = pd.read_excel(PATH_TABLE_B)
            print(f"✅ Données sources chargées: {len(self.df_lp)} établissements à traiter, {len(self.df_sc)} références")
            
            # Vérifier si le fichier de résultats existe déjà
            self._check_existing_results()
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des données: {e}")
            raise
    
    def _check_existing_results(self):
        """
        Vérifie s'il existe déjà des résultats et les charge si possible
        """
        # Si l'utilisateur veut reset l'historique, on efface le fichier existant
        if self.reset_history:
            if os.path.exists(OUTPUT_PATH):
                try:
                    os.remove(OUTPUT_PATH)
                    print("🔄 Historique effacé - nouveau traitement complet")
                except Exception as e:
                    print(f"⚠️  Erreur lors de l'effacement de l'historique: {e}")
            
            # IMPORTANT: Toujours initialiser à None quand on reset
            print("🆕 Nouveau traitement complet demandé")
            self.df_lp[COLA_FINESS] = None
            if COLA_MATCH_NAME not in self.df_lp.columns:
                self.df_lp[COLA_MATCH_NAME] = None
            else:
                self.df_lp[COLA_MATCH_NAME] = None
            if COLA_MATCH_CONFIDENCE not in self.df_lp.columns:
                self.df_lp[COLA_MATCH_CONFIDENCE] = None
            else:
                self.df_lp[COLA_MATCH_CONFIDENCE] = None
            return
        
        # Seulement si on ne reset PAS l'historique
        if os.path.exists(OUTPUT_PATH):
            try:
                existing_df = pd.read_excel(OUTPUT_PATH)
                print(f"📋 Fichier de résultats existant trouvé: {OUTPUT_PATH}")
                
                # Vérifier si les colonnes correspondent
                if (len(existing_df) == len(self.df_lp) and 
                    COLA_FINESS in existing_df.columns):
                    
                    # Copier les résultats existants
                    self.df_lp[COLA_FINESS] = existing_df[COLA_FINESS]
                    
                    # Copier les nouvelles colonnes si elles existent
                    if COLA_MATCH_NAME in existing_df.columns:
                        self.df_lp[COLA_MATCH_NAME] = existing_df[COLA_MATCH_NAME]
                    else:
                        self.df_lp[COLA_MATCH_NAME] = None
                        
                    if COLA_MATCH_CONFIDENCE in existing_df.columns:
                        self.df_lp[COLA_MATCH_CONFIDENCE] = existing_df[COLA_MATCH_CONFIDENCE]
                    else:
                        self.df_lp[COLA_MATCH_CONFIDENCE] = None
                    
                    # Compter les hôpitaux déjà traités
                    already_processed = self.df_lp[COLA_FINESS].notna().sum()
                    print(f"🔄 Reprise du traitement: {already_processed} hôpitaux déjà traités")
                    print(f"📝 Reste à traiter: {len(self.df_lp) - already_processed} hôpitaux")
                else:
                    print("⚠️  Structure différente détectée, nouveau traitement complet")
                    self.df_lp[COLA_FINESS] = None
                    self.df_lp[COLA_MATCH_NAME] = None
                    self.df_lp[COLA_MATCH_CONFIDENCE] = None
            except Exception as e:
                print(f"⚠️  Erreur lors de la lecture du fichier existant: {e}")
                print("🔄 Démarrage d'un nouveau traitement...")
                self.df_lp[COLA_FINESS] = None
                self.df_lp[COLA_MATCH_NAME] = None
                self.df_lp[COLA_MATCH_CONFIDENCE] = None
        else:
            print("🆕 Nouveau traitement - aucun fichier de résultats existant")
            self.df_lp[COLA_FINESS] = None
            self.df_lp[COLA_MATCH_NAME] = None
            self.df_lp[COLA_MATCH_CONFIDENCE] = None
    
    def process_all_hospitals(self):
        """
        Traite tous les hôpitaux du fichier avec optimisations et reprise automatique
        """
        if self.df_lp is None or self.df_sc is None:
            raise ValueError("Les données doivent être chargées avant le traitement")
        
        # Vérification critique : s'assurer que la colonne FINESS est bien vide si reset
        if self.reset_history:
            self.df_lp[COLA_FINESS] = None
            print("🔄 Reset confirmé : colonne FINESS réinitialisée")
        
        # Initialiser les nouvelles colonnes si elles n'existent pas
        if COLA_MATCH_NAME not in self.df_lp.columns:
            self.df_lp[COLA_MATCH_NAME] = None
        if COLA_MATCH_CONFIDENCE not in self.df_lp.columns:
            self.df_lp[COLA_MATCH_CONFIDENCE] = None
        # Ajouter une colonne pour tracer la source du nom matché
        if "Source_Nom_Match" not in self.df_lp.columns:
            self.df_lp["Source_Nom_Match"] = None

        # Compter les hôpitaux déjà traités
        already_processed = self.df_lp[COLA_FINESS].notna().sum()
        total_hospitals = len(self.df_lp)
        remaining = total_hospitals - already_processed
        
        print(f"\n🏥 Démarrage du traitement:")
        print(f"📊 Total: {total_hospitals} établissements")
        print(f"✅ Déjà traités: {already_processed}")
        print(f"📝 Reste à traiter: {remaining}")
        print(f"💾 Sauvegarde automatique tous les {SAVE_INTERVAL} établissements")
        
        # Ne traiter que les hôpitaux non encore traités
        for idx, row in self.df_lp.iterrows():
            # Vérifier si cet hôpital a déjà été traité
            if pd.notna(self.df_lp.at[idx, COLA_FINESS]):
                continue  # Passer au suivant
            
            self._process_single_hospital(idx, row)
            
            # Sauvegarde régulière tous les SAVE_INTERVAL
            if (self.processed_hospitals % SAVE_INTERVAL == 0 and 
                self.processed_hospitals > self.last_save_index):
                self._save_intermediate_results(self.processed_hospitals)
                self.last_save_index = self.processed_hospitals
        
        self._print_final_statistics()
    
    def _process_single_hospital(self, idx, row):
        """
        Traite un seul hôpital (seulement s'il n'a pas déjà été traité)
        """
        self.processed_hospitals += 1
        
        # Calculer le nombre total d'hôpitaux restants à traiter
        total_remaining = self.df_lp[COLA_FINESS].isna().sum()
        current_remaining = total_remaining - self.processed_hospitals + 1
        
        print(f"\n=== Traitement {self.processed_hospitals} - Index: {idx} ===")
        print(f"📈 Progression: {current_remaining} hôpitaux restants")
        
        # Obtenir le nom et le type d'établissement
        establishment_name, establishment_type = get_establishment_name_and_type(row)
        
        # Appliquer les paramètres de gestion des types
        if not self.differentiate_types:
            establishment_type = "unknown"  # Ignorer le type
        elif self.forced_type:
            establishment_type = self.forced_type  # Forcer un type spécifique
        
        if not establishment_name:
            print(f"❌ Aucun nom d'établissement trouvé pour la ligne {idx}")
            self.df_lp.at[idx, COLA_FINESS] = None
            return
        
        type_info = f" (Type: {establishment_type.upper()})" if self.differentiate_types else " (Type ignoré)"
        print(f"🔍 Recherche pour: {establishment_name}{type_info}")
        
        # Affichage sécurisé des informations géographiques
        ville_info = row[COLA_VILLE] if COLA_VILLE and COLA_VILLE in row.index else "N/A"
        dept_info = row[COLA_DEPARTEMENT] if COLA_DEPARTEMENT and COLA_DEPARTEMENT in row.index else "N/A"
        print(f"📍 Ville: {ville_info} | Département: {dept_info}")
        
        # Filtrer les candidats par ville
        candidates = self._find_candidates_in_city(row, establishment_name, establishment_type)
        
        if not candidates:
            print(f"❌ Aucun établissement trouvé dans {ville_info} ({dept_info})")
            self.df_lp.at[idx, COLA_FINESS] = None
            return
        
        # Essayer le matching
        result = self._match_establishment(establishment_name, establishment_type, candidates)
        
        # Gérer le retour avec 4 valeurs
        if len(result) == 4:
            selected_finess, matched_name, confidence_score, source_column = result
        else:
            # Compatibilité avec l'ancien format (3 valeurs)
            selected_finess, matched_name, confidence_score = result
            source_column = "COLB_NOM_SC"  # Valeur par défaut
        
        if selected_finess:
            self.df_lp.at[idx, COLA_FINESS] = selected_finess
            self.df_lp.at[idx, COLA_MATCH_NAME] = matched_name
            self.df_lp.at[idx, COLA_MATCH_CONFIDENCE] = confidence_score
            self.df_lp.at[idx, "Source_Nom_Match"] = source_column
            print(f"✅ FINESS assigné: {selected_finess} (Confiance: {confidence_score}%)")
            print(f"   Nom matché: {matched_name} (Source: {source_column})")
        else:
            self.df_lp.at[idx, COLA_FINESS] = None
            self.df_lp.at[idx, COLA_MATCH_NAME] = None
            self.df_lp.at[idx, COLA_MATCH_CONFIDENCE] = 0
            self.df_lp.at[idx, "Source_Nom_Match"] = None
            print(f"❌ Aucun match trouvé")
        
        print(f"📊 Requêtes IA utilisées: {self.total_ai_requests}")
        
        # Petite pause pour éviter la surcharge API
        if self.total_ai_requests > 0 and self.total_ai_requests % 10 == 0:
            print("⏳ Pause de 5 secondes pour éviter la surcharge API...")
            time.sleep(5)
    
    def _find_candidates_in_city(self, row, establishment_name, establishment_type):
        """
        Trouve tous les candidats dans la même ville/département avec normalisation
        """
        # Utiliser la stratégie géographique configurée
        from config import get_geo_comparison_strategy
        geo_strategy = get_geo_comparison_strategy()
        
        # Vérifier que les colonnes existent avant de les utiliser
        search_city = None
        search_dept = None
        
        if geo_strategy["use_city"] and COLA_VILLE and COLA_VILLE in row.index:
            search_city = normalize_city_name(row[COLA_VILLE])
        
        if geo_strategy["use_department"] and COLA_DEPARTEMENT and COLA_DEPARTEMENT in row.index:
            search_dept = normalize_department_name(row[COLA_DEPARTEMENT])
        
        print(f"📍 Recherche normalisée: {search_city} ({search_dept})")
        print(f"🗺️ Stratégie géo: {geo_strategy['type']} ({'ville' if geo_strategy['use_city'] else ''}{' + ' if geo_strategy['both'] else ''}{'département' if geo_strategy['use_department'] else ''})")
        
        if not search_city and not search_dept:
            print("❌ Impossible de normaliser la ville/département ou colonnes manquantes")
            return []
        
        # Filtrer avec normalisation géographique optimisée
        candidates_indices = []
        
        for idx, candidate_row in self.df_sc.iterrows():
            candidate_city = None
            candidate_dept = None
            
            # Vérifier que les colonnes existent avant de les utiliser
            if geo_strategy["use_city"] and COLB_VILLE and COLB_VILLE in candidate_row.index:
                candidate_city = normalize_city_name(candidate_row[COLB_VILLE])
            
            if geo_strategy["use_department"] and COLB_DEPARTEMENT and COLB_DEPARTEMENT in candidate_row.index:
                candidate_dept = normalize_department_name(candidate_row[COLB_DEPARTEMENT])
            
            # Logique de correspondance selon la stratégie
            match_found = False
            
            if geo_strategy["city_only"]:
                # Ville uniquement
                match_found = (search_city and candidate_city and 
                             (search_city == candidate_city or 
                              search_city in candidate_city or 
                              candidate_city in search_city))
            
            elif geo_strategy["department_only"]:
                # Département uniquement
                match_found = (search_dept and candidate_dept and search_dept == candidate_dept)
            
            elif geo_strategy["both"]:
                # Ville ET département
                city_match = (search_city and candidate_city and 
                             (search_city == candidate_city or 
                              search_city in candidate_city or 
                              candidate_city in search_city))
                dept_match = (search_dept and candidate_dept and search_dept == candidate_dept)
                
                # Accepter si ville ET département correspondent, ou si seulement ville correspond (si pas de dept)
                if search_dept and candidate_dept:
                    match_found = city_match and dept_match
                else:
                    # Si pas de département disponible, utiliser seulement la ville
                    match_found = city_match
            
            if match_found:
                candidates_indices.append(idx)
        
        if not candidates_indices:
            print(f"❌ Aucun candidat trouvé avec les critères géographiques")
            return []
        
        df_sc_filtered = self.df_sc.loc[candidates_indices]
        print(f"🏢 {len(df_sc_filtered)} établissements trouvés")
        
        # Préparer les candidats avec filtrage par type
        all_candidates = []
        same_type_candidates = []
        
        for idx, row_sc in df_sc_filtered.iterrows():
            # Prioriser COLB_NOM_SC (colonne principale de matching) 
            # plutôt que de choisir automatiquement le nom le plus long
            best_name = get_best_candidate_name(
                row_sc, 
                [COLB_NOM_SC, COLB_NOM, COLB_NOM_2], 
                prioritize_first=True  # Prioriser la première colonne (celle du matching)
            )
            candidate_info = (best_name, row_sc[COLB_FIN_SCS])
            all_candidates.append(candidate_info)
            
            # Garder séparément les candidats du même type SEULEMENT si on différencie les types
            if self.differentiate_types and establishment_type != "unknown":
                candidate_type = detect_establishment_type(best_name)
                if candidate_type == establishment_type:
                    same_type_candidates.append(candidate_info)
        
        # Choisir les candidats à utiliser
        if self.differentiate_types and same_type_candidates:
            candidates = same_type_candidates
            print(f"🎯 Trouvé {len(same_type_candidates)} candidats du même type ({establishment_type})")
        else:
            candidates = all_candidates
            if self.differentiate_types:
                print(f"⚠️  Aucun candidat du type {establishment_type}, utilisation de tous les candidats ({len(all_candidates)})")
            else:
                print(f"🎯 Tous types confondus: {len(all_candidates)} candidats")
        
        return candidates
    
    def _match_establishment(self, establishment_name, establishment_type, candidates):
        """
        Effectue le matching d'un établissement avec les candidats (optimisé IA)
        
        Returns:
            tuple: (finess, nom_matché, score_confiance, source_colonne) ou (None, None, 0, None) si pas de match
        """
        establishment_name_clean = clean_name(establishment_name)
        
        # Si un seul candidat, pas besoin de fuzzy ou IA
        if len(candidates) == 1:
            print(f"🎯 Un seul candidat disponible: {candidates[0][0]}")
            return candidates[0][1], candidates[0][0], 95, "COLB_NOM_SC"  # Supposer que c'est la colonne principale
        
        # Essayer d'abord le matching fuzzy
        best_match_idx, best_score = self._fuzzy_match(establishment_name_clean, candidates)
        
        if best_score > FUZZY_THRESHOLD:
            print(f"🎯 Match fuzzy trouvé (score: {best_score})")
            print(f"   {establishment_name_clean} -> {candidates[best_match_idx][0]}")
            return candidates[best_match_idx][1], candidates[best_match_idx][0], best_score, "COLB_NOM_SC"
        else:
            # Utiliser l'IA pour choisir PARMI TOUS les candidats en une seule requête
            print(f"🤖 Score fuzzy insuffisant ({best_score}), utilisation de l'IA...")
            print(f"   Analyse de {len(candidates)} candidats en une requête...")
            self.total_ai_requests += 1
            
            selected_idx, matched_name, confidence_score = ai_compare_hospital_names_batch(
                establishment_name_clean, candidates, establishment_type
            )
            
            if selected_idx == -1:  # Aucune correspondance
                print(f"🤖 IA: Aucune correspondance trouvée")
                return None, "AUCUNE CORRESPONDANCE", 0, None
            
            print(f"🎯 Match IA sélectionné (confiance: {confidence_score}%):")
            print(f"   {establishment_name_clean} -> {matched_name}")
            return candidates[selected_idx][1], matched_name, confidence_score, "COLB_NOM_SC"
    
    def _fuzzy_match(self, establishment_name_clean, candidates):
        """
        Effectue un matching fuzzy et retourne le meilleur score
        """
        best_match_idx = -1
        best_score = 0
        
        for i, (candidate_name, finess) in enumerate(candidates):
            score = fuzz._token_sort(establishment_name_clean, candidate_name)
            if score > best_score:
                best_score = score
                best_match_idx = i
        
        return best_match_idx, best_score
    
    def _print_final_statistics(self):
        """
        Affiche les statistiques finales
        """
        print(f"\n🎉 === RÉSULTATS FINAUX ===")
        print(f"📊 Total d'établissements dans le fichier: {len(self.df_lp)}")
        print(f"🔄 Établissements traités dans cette session: {self.processed_hospitals}")
        print(f"🤖 Total de requêtes IA utilisées: {self.total_ai_requests}")
        
        matches_found = self.df_lp[COLA_FINESS].notna().sum()
        no_matches = self.df_lp[COLA_FINESS].isna().sum()
        success_rate = matches_found / len(self.df_lp) * 100
        
        print(f"✅ Matches trouvés: {matches_found}/{len(self.df_lp)} ({success_rate:.1f}%)")
        print(f"❌ Aucun match: {no_matches}")
        
        if no_matches == 0:
            print("🎊 Traitement 100% terminé !")
        else:
            print(f"⏳ {no_matches} établissements restent à traiter")
    
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
    
    def _save_intermediate_results(self, processed_count):
        """
        Sauvegarde intermédiaire tous les SAVE_INTERVAL hôpitaux
        """
        try:
            total_matches = self.df_lp[COLA_FINESS].notna().sum()
            print(f"\n💾 Sauvegarde intermédiaire après {processed_count} nouveaux hôpitaux traités...")
            print(f"📊 Total de matches dans le fichier: {total_matches}")
            
            # Sauvegarder dans le fichier principal (écrase à chaque fois)
            if not os.path.exists(os.path.dirname(OUTPUT_PATH)):
                os.makedirs(os.path.dirname(OUTPUT_PATH))
            
            self.df_lp.to_excel(OUTPUT_PATH, index=False)
            print(f"✅ Sauvegarde réussie: {OUTPUT_PATH}")
            
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde intermédiaire: {e}")
            # Continue le traitement même en cas d'erreur de sauvegarde
