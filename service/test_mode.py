"""
Module de test avec échantillonnage aléatoire et logging détaillé
"""

import pandas as pd
import random
import json
import os
from datetime import datetime
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestLogger:
    """
    Logger détaillé pour le mode test
    """
    
    def __init__(self, log_file_path=None):
        if log_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_path = f"test_log_{timestamp}.json"
        
        self.log_file_path = log_file_path
        self.logs = []
        self.current_establishment = None
    
    def start_establishment(self, idx, establishment_name, city, department):
        """
        Démarre le logging pour un nouvel établissement
        """
        self.current_establishment = {
            "index": idx,
            "establishment_name": establishment_name,
            "city": city,
            "department": department,
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "final_result": None
        }
        print(f"\n🔍 [TEST LOG] Début traitement établissement #{idx}: {establishment_name}")
    
    def log_step(self, step_name, details, data=None):
        """
        Enregistre une étape du processus
        """
        step = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "data": data
        }
        
        if self.current_establishment:
            self.current_establishment["steps"].append(step)
        
        print(f"📝 [TEST LOG] {step_name}: {details}")
        if data and isinstance(data, dict):
            for key, value in data.items():
                print(f"    • {key}: {value}")
    
    def log_geo_strategy(self, geo_strategy, search_city, search_dept):
        """
        Log de la stratégie géographique
        """
        self.log_step(
            "Stratégie géographique",
            f"Type: {geo_strategy['type']}, Ville: {geo_strategy['use_city']}, Département: {geo_strategy['use_department']}",
            {
                "search_city_normalized": search_city,
                "search_department_normalized": search_dept,
                "strategy": geo_strategy
            }
        )
    
    def log_candidates_found(self, candidates_count, candidates_list):
        """
        Log des candidats trouvés
        """
        candidates_details = []
        for i, (name, finess) in enumerate(candidates_list, 1):
            candidates_details.append({
                "index": i,
                "name": name,
                "finess": finess
            })
        
        self.log_step(
            "Candidats trouvés",
            f"{candidates_count} candidats identifiés",
            {"candidates": candidates_details}
        )
    
    def log_fuzzy_matching(self, establishment_name_clean, best_score, best_match_idx, threshold):
        """
        Log du matching fuzzy
        """
        self.log_step(
            "Matching Fuzzy",
            f"Meilleur score: {best_score}% (seuil: {threshold}%)",
            {
                "establishment_clean": establishment_name_clean,
                "best_score": best_score,
                "best_match_index": best_match_idx,
                "threshold": threshold,
                "fuzzy_success": best_score > threshold
            }
        )
    
    def log_ai_prompt(self, prompt, candidates_list, establishment_type):
        """
        Log du prompt envoyé à l'IA
        """
        self.log_step(
            "Prompt IA envoyé",
            f"Analyse de {len(candidates_list)} candidats par IA",
            {
                "establishment_type": establishment_type,
                "candidates_count": len(candidates_list),
                "full_prompt": prompt,
                "candidates_analyzed": [{"name": name, "finess": finess} for name, finess in candidates_list]
            }
        )
    
    def log_ai_response(self, raw_response, selected_index, matched_name, confidence):
        """
        Log de la réponse de l'IA
        """
        self.log_step(
            "Réponse IA reçue",
            f"Sélection: index {selected_index}, confiance: {confidence}%",
            {
                "raw_ai_response": raw_response,
                "selected_index": selected_index,
                "matched_name": matched_name,
                "confidence_score": confidence
            }
        )
    
    def log_final_result(self, finess, matched_name, confidence, method_used):
        """
        Log du résultat final
        """
        self.current_establishment["final_result"] = {
            "finess": finess,
            "matched_name": matched_name,
            "confidence": confidence,
            "method_used": method_used
        }
        
        self.log_step(
            "Résultat final",
            f"FINESS: {finess}, Méthode: {method_used}",
            {
                "finess": finess,
                "matched_name": matched_name,
                "confidence": confidence,
                "method": method_used
            }
        )
    
    def finish_establishment(self):
        """
        Termine le logging pour l'établissement actuel
        """
        if self.current_establishment:
            self.logs.append(self.current_establishment)
            print(f"✅ [TEST LOG] Fin traitement établissement #{self.current_establishment['index']}")
            self.current_establishment = None
    
    def save_logs(self):
        """
        Sauvegarde tous les logs dans un fichier JSON
        """
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, indent=2, ensure_ascii=False)
            print(f"💾 [TEST LOG] Logs sauvegardés dans: {self.log_file_path}")
            return self.log_file_path
        except Exception as e:
            print(f"❌ [TEST LOG] Erreur sauvegarde logs: {e}")
            return None
    
    def generate_summary(self):
        """
        Génère un résumé des tests
        """
        if not self.logs:
            return "Aucun log disponible"
        
        total = len(self.logs)
        successful = sum(1 for log in self.logs if log["final_result"] and log["final_result"]["finess"])
        
        methods_used = {}
        for log in self.logs:
            if log["final_result"]:
                method = log["final_result"].get("method_used", "unknown")
                methods_used[method] = methods_used.get(method, 0) + 1
        
        summary = f"""
🎯 === RÉSUMÉ DU TEST ===
📊 Total établissements testés: {total}
✅ Matches trouvés: {successful} ({successful/total*100:.1f}%)
❌ Aucun match: {total - successful} ({(total-successful)/total*100:.1f}%)

📈 Méthodes utilisées:
"""
        for method, count in methods_used.items():
            summary += f"   • {method}: {count} cas ({count/total*100:.1f}%)\n"
        
        summary += f"\n📁 Log détaillé: {self.log_file_path}"
        
        return summary


class TestSampler:
    """
    Gestionnaire d'échantillonnage pour les tests
    """
    
    def __init__(self, sample_size=25, random_seed=None):
        self.sample_size = sample_size
        self.random_seed = random_seed
        if random_seed:
            random.seed(random_seed)
    
    def sample_dataframe(self, df, sample_size=None):
        """
        Échantillonne aléatoirement un DataFrame
        """
        if sample_size is None:
            sample_size = self.sample_size
        
        if len(df) <= sample_size:
            print(f"⚠️  DataFrame contient seulement {len(df)} lignes, utilisation complète")
            return df.copy()
        
        # Échantillonnage aléatoire
        sampled_indices = random.sample(range(len(df)), sample_size)
        sampled_df = df.iloc[sampled_indices].copy().reset_index(drop=True)
        
        print(f"🎲 Échantillon de {sample_size} établissements sélectionné sur {len(df)} total")
        print(f"📋 Indices sélectionnés: {sorted(sampled_indices)}")
        
        return sampled_df
    
    def create_test_config(self, original_df, sampled_df):
        """
        Crée une configuration de test
        """
        config = {
            "test_timestamp": datetime.now().isoformat(),
            "original_size": len(original_df),
            "sample_size": len(sampled_df),
            "random_seed": self.random_seed,
            "sample_info": {
                "first_establishment": sampled_df.iloc[0].to_dict() if len(sampled_df) > 0 else None,
                "last_establishment": sampled_df.iloc[-1].to_dict() if len(sampled_df) > 0 else None
            }
        }
        return config


def create_test_hospital_matcher(original_matcher, enable_test_mode=True, sample_size=25):
    """
    Crée une version test du HospitalMatcher avec échantillonnage et logging
    """
    if not enable_test_mode:
        return original_matcher
    
    class TestHospitalMatcher(original_matcher.__class__):
        """
        Version test du HospitalMatcher avec logging détaillé
        """
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.test_mode = True
            self.test_logger = TestLogger()
            self.test_sampler = TestSampler(sample_size=sample_size)
            
            # Créer un chemin de sortie spécifique pour les tests
            self._setup_test_output_path()
            
        def _setup_test_output_path(self):
            """
            Configure un chemin de sortie spécifique pour les tests
            """
            from config import OUTPUT_PATH
            import os
            
            # Générer un nom de fichier unique pour le test
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.dirname(OUTPUT_PATH)
            base_name = os.path.splitext(os.path.basename(OUTPUT_PATH))[0]
            
            # Nom spécifique pour le mode test
            self.test_output_path = os.path.join(
                base_dir, 
                f"{base_name}_TEST_SAMPLE_{sample_size}_{timestamp}.xlsx"
            )
            
            print(f"📁 [TEST] Fichier de sortie: {self.test_output_path}")
            
        def load_data(self):
            """
            Charge les données et applique l'échantillonnage en mode test
            """
            print("\n🧪 === MODE TEST ACTIVÉ ===")
            super().load_data()
            
            # Échantillonner les données
            print(f"🎲 Échantillonnage de {sample_size} établissements...")
            original_df = self.df_lp.copy()  # Sauvegarder l'original pour la config
            self.df_lp = self.test_sampler.sample_dataframe(self.df_lp, sample_size)
            
            # Créer la configuration de test
            test_config = self.test_sampler.create_test_config(original_df, self.df_lp)
            self.test_logger.log_step("Configuration test", "Échantillonnage effectué", test_config)
            
            # Sauvegarder les informations d'échantillonnage dans un fichier séparé
            self._save_sample_info(test_config, original_df)
            
        def _save_sample_info(self, test_config, original_df):
            """
            Sauvegarde les informations sur l'échantillon dans un fichier Excel séparé
            """
            try:
                sample_info_path = self.test_output_path.replace('.xlsx', '_SAMPLE_INFO.xlsx')
                
                # Créer un DataFrame avec les informations de l'échantillon
                sample_df = self.df_lp.copy()
                sample_df['ORIGINAL_INDEX'] = sample_df.index
                sample_df['SELECTED_FOR_TEST'] = True
                
                # Créer un DataFrame résumé
                summary_data = {
                    'Paramètre': [
                        'Taille originale',
                        'Taille échantillon', 
                        'Pourcentage échantillonné',
                        'Graine aléatoire',
                        'Timestamp test',
                        'Fichier de logs',
                        'Fichier résultats'
                    ],
                    'Valeur': [
                        test_config['original_size'],
                        test_config['sample_size'],
                        f"{(test_config['sample_size']/test_config['original_size']*100):.1f}%",
                        test_config['random_seed'] or 'Aléatoire',
                        test_config['test_timestamp'],
                        self.test_logger.log_file_path,
                        self.test_output_path
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                
                # Sauvegarder dans un fichier Excel avec plusieurs feuilles
                with pd.ExcelWriter(sample_info_path, engine='openpyxl') as writer:
                    summary_df.to_excel(writer, sheet_name='Résumé Test', index=False)
                    sample_df.to_excel(writer, sheet_name='Échantillon Sélectionné', index=False)
                
                print(f"📋 [TEST] Informations échantillon sauvegardées: {sample_info_path}")
                
            except Exception as e:
                print(f"⚠️  [TEST] Erreur sauvegarde info échantillon: {e}")

        def _process_single_hospital(self, idx, row):
            """
            Version avec logging détaillé
            """
            from config import COLA_NOM_HOPITAL, COLA_VILLE, COLA_DEPARTEMENT, COLA_FINESS
            from establishment_utils import get_establishment_name_and_type
            
            # Commencer le logging pour cet établissement
            establishment_name, _ = get_establishment_name_and_type(row)
            city = row.get(COLA_VILLE, "N/A")
            dept = row.get(COLA_DEPARTEMENT, "N/A")
            
            self.test_logger.start_establishment(idx, establishment_name, city, dept)
            
            # Appeler la méthode parent avec logging
            try:
                result = super()._process_single_hospital(idx, row)
                
                # Logger le résultat
                finess = self.df_lp.at[idx, COLA_FINESS] if COLA_FINESS in self.df_lp.columns else None
                matched_name = self.df_lp.at[idx, "Nom_Match_Retenu"] if "Nom_Match_Retenu" in self.df_lp.columns else None
                confidence = self.df_lp.at[idx, "Confiance_Match"] if "Confiance_Match" in self.df_lp.columns else 0
                
                method = "unknown"
                if finess:
                    method = "fuzzy" if confidence >= 80 else "ai"
                else:
                    method = "no_match"
                
                self.test_logger.log_final_result(finess, matched_name, confidence, method)
                
            except Exception as e:
                self.test_logger.log_step("Erreur", f"Erreur durant le traitement: {str(e)}")
                raise
            finally:
                self.test_logger.finish_establishment()
            
            return result
        
        def _find_candidates_in_city(self, row, establishment_name, establishment_type):
            """
            Version avec logging de la recherche géographique
            """
            from config import get_geo_comparison_strategy, COLA_VILLE, COLA_DEPARTEMENT, COLB_VILLE, COLB_DEPARTEMENT
            from geo_utils import normalize_city_name, normalize_department_name
            
            # Logger la stratégie géographique
            geo_strategy = get_geo_comparison_strategy()
            
            search_city = None
            search_dept = None
            
            if geo_strategy["use_city"] and COLA_VILLE and COLA_VILLE in row.index:
                search_city = normalize_city_name(row[COLA_VILLE])
            
            if geo_strategy["use_department"] and COLA_DEPARTEMENT and COLA_DEPARTEMENT in row.index:
                search_dept = normalize_department_name(row[COLA_DEPARTEMENT])
            
            self.test_logger.log_geo_strategy(geo_strategy, search_city, search_dept)
            
            # Appeler la méthode parent
            candidates = super()._find_candidates_in_city(row, establishment_name, establishment_type)
            
            # Logger les candidats trouvés
            self.test_logger.log_candidates_found(len(candidates), candidates)
            
            return candidates
        
        def _match_establishment(self, establishment_name, establishment_type, candidates):
            """
            Version avec logging du matching
            """
            from config import FUZZY_THRESHOLD
            from establishment_utils import clean_name
            
            establishment_name_clean = clean_name(establishment_name)
            
            # Si un seul candidat
            if len(candidates) == 1:
                self.test_logger.log_step("Match unique", f"Un seul candidat: {candidates[0][0]}")
                return candidates[0][1], candidates[0][0], 95, "COLB_NOM_SC"
            
            # Essayer le fuzzy matching avec logging
            best_match_idx, best_score = self._fuzzy_match(establishment_name_clean, candidates)
            self.test_logger.log_fuzzy_matching(establishment_name_clean, best_score, best_match_idx, FUZZY_THRESHOLD)
            
            if best_score > FUZZY_THRESHOLD:
                method = "fuzzy_match"
                result = candidates[best_match_idx][1], candidates[best_match_idx][0], best_score, "COLB_NOM_SC"
            else:
                # Utiliser l'IA avec logging du prompt
                method = "ai_match"
                result = self._ai_match_with_logging(establishment_name_clean, candidates, establishment_type)
                # Ajouter la source_column si pas présente
                if len(result) == 3:
                    result = result + ("COLB_NOM_SC",)
            
            # Logger selon la méthode utilisée
            finess, matched_name, confidence, source_column = result
            if finess:
                self.test_logger.log_final_result(finess, matched_name, confidence, method)
            else:
                self.test_logger.log_final_result(None, "AUCUNE CORRESPONDANCE", 0, "no_match")
            
            return result
        
        def _ai_match_with_logging(self, establishment_name_clean, candidates, establishment_type):
            """
            Matching IA avec logging détaillé du prompt et de la réponse
            """
            from ai_service import ai_compare_hospital_names_batch
            from establishment_utils import detect_establishment_type
            
            # Construire le prompt exactement comme dans ai_service.py (SANS les types)
            candidates_text = ""
            for i, (name, finess) in enumerate(candidates, 1):
                # Supprimer l'affichage du type détecté - ne pas le montrer à Gemini
                candidates_text += f"- Option {i}: \"{name}\" (FINESS: {finess})\n"
            
            establishment_info = self._get_establishment_info(establishment_type)
            
            prompt = f"""
Tu es un expert en analyse de données médicales. Tu dois OBLIGATOIREMENT choisir la meilleure correspondance parmi les options données.

Nom de l'établissement recherché: "{establishment_name_clean}"

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
            
            # Logger le prompt
            self.test_logger.log_ai_prompt(prompt, candidates, establishment_type)
            
            # Appeler l'IA
            self.total_ai_requests += 1
            selected_idx, matched_name, confidence_score = ai_compare_hospital_names_batch(
                establishment_name_clean, candidates, establishment_type
            )
            
            # Logger la réponse (on ne peut pas capturer la réponse brute ici, mais on peut logger le résultat)
            self.test_logger.log_ai_response(
                f"Index sélectionné: {selected_idx}", 
                selected_idx, 
                matched_name, 
                confidence_score
            )
            
            if selected_idx == -1:
                return None, "AUCUNE CORRESPONDANCE", 0, None
            
            return candidates[selected_idx][1], matched_name, confidence_score, "COLB_NOM_SC"

        def _get_establishment_info(self, establishment_type):
            """
            Helper pour obtenir les infos sur le type d'établissement
            """
            if establishment_type == "hopital":
                return "Il s'agit d'un HÔPITAL, privilégie les établissements de type hôpital (CHU, CH, HOPITAL, etc.)."
            elif establishment_type == "clinique":
                return "Il s'agit d'une CLINIQUE, privilégie les établissements de type clinique (CLINIQUE, POLYCLINIQUE, etc.)."
            else:
                return "Type d'établissement non déterminé, utilise ton meilleur jugement."
        
        def save_results(self):
            """
            Sauvegarde avec génération du rapport de test et fichier Excel spécifique
            """
            print(f"\n💾 [TEST] Enregistrement des résultats de test...")
            
            try:
                import os
                
                # Créer le répertoire si nécessaire
                test_dir = os.path.dirname(self.test_output_path)
                if not os.path.exists(test_dir):
                    os.makedirs(test_dir)
                
                # Ajouter des colonnes spécifiques au test
                self.df_lp['TEST_MODE'] = True
                self.df_lp['TEST_TIMESTAMP'] = datetime.now().isoformat()
                self.df_lp['SAMPLE_SIZE'] = len(self.df_lp)
                
                # Sauvegarder dans le fichier spécifique au test
                self.df_lp.to_excel(self.test_output_path, index=False)
                print(f"✅ [TEST] Résultats test sauvegardés: {self.test_output_path}")
                
                # Sauvegarder les logs
                log_file = self.test_logger.save_logs()
                
                # Générer et afficher le résumé
                summary = self.test_logger.generate_summary()
                print(summary)
                
                # Sauvegarder le résumé dans un fichier texte
                if log_file:
                    summary_file = log_file.replace('.json', '_summary.txt')
                    try:
                        with open(summary_file, 'w', encoding='utf-8') as f:
                            f.write(summary)
                        print(f"📊 [TEST] Résumé sauvegardé: {summary_file}")
                    except Exception as e:
                        print(f"❌ [TEST] Erreur sauvegarde résumé: {e}")
                
                # Créer un fichier Excel consolidé avec tous les résultats
                self._create_consolidated_test_report(log_file)
                
            except Exception as e:
                print(f"❌ [TEST] Erreur lors de l'enregistrement: {e}")
                raise
        
        def _create_consolidated_test_report(self, log_file):
            """
            Crée un rapport Excel consolidé avec toutes les informations de test
            """
            try:
                consolidated_path = self.test_output_path.replace('.xlsx', '_RAPPORT_COMPLET.xlsx')
                
                # Préparer les données pour le rapport
                test_results = self.df_lp.copy()
                
                # Statistiques générales
                total_tested = len(test_results)
                successful_matches = test_results[test_results['FINESS'].notna()].shape[0]
                success_rate = (successful_matches / total_tested * 100) if total_tested > 0 else 0
                
                stats_data = {
                    'Métrique': [
                        'Total établissements testés',
                        'Matches réussis',
                        'Échecs',
                        'Taux de réussite (%)',
                        'Requêtes IA utilisées',
                        'Fichier de logs détaillé',
                        'Timestamp du test'
                    ],
                    'Valeur': [
                        total_tested,
                        successful_matches,
                        total_tested - successful_matches,
                        f"{success_rate:.1f}%",
                        self.total_ai_requests,
                        log_file or 'N/A',
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                
                # Analyse par confiance
                if 'Confiance_Match' in test_results.columns:
                    confidence_ranges = {
                        'Très élevée (90-100%)': len(test_results[test_results['Confiance_Match'] >= 90]),
                        'Élevée (80-89%)': len(test_results[(test_results['Confiance_Match'] >= 80) & (test_results['Confiance_Match'] < 90)]),
                        'Moyenne (70-79%)': len(test_results[(test_results['Confiance_Match'] >= 70) & (test_results['Confiance_Match'] < 80)]),
                        'Faible (60-69%)': len(test_results[(test_results['Confiance_Match'] >= 60) & (test_results['Confiance_Match'] < 70)]),
                        'Très faible (<60%)': len(test_results[test_results['Confiance_Match'] < 60])
                    }
                    
                    confidence_df = pd.DataFrame([
                        {'Niveau de confiance': k, 'Nombre': v, 'Pourcentage': f"{(v/total_tested*100):.1f}%"} 
                        for k, v in confidence_ranges.items()
                    ])
                else:
                    confidence_df = pd.DataFrame({'Info': ['Données de confiance non disponibles']})
                
                # Sauvegarder le rapport consolidé
                with pd.ExcelWriter(consolidated_path, engine='openpyxl') as writer:
                    stats_df.to_excel(writer, sheet_name='Statistiques Générales', index=False)
                    confidence_df.to_excel(writer, sheet_name='Analyse Confiance', index=False)
                    test_results.to_excel(writer, sheet_name='Résultats Détaillés', index=False)
                
                print(f"📈 [TEST] Rapport consolidé créé: {consolidated_path}")
                
            except Exception as e:
                print(f"⚠️  [TEST] Erreur création rapport consolidé: {e}")

    # Copier les attributs de l'instance originale
    test_matcher = TestHospitalMatcher(
        reset_history=original_matcher.reset_history,
        differentiate_types=original_matcher.differentiate_types,
        forced_type=original_matcher.forced_type
    )
    
    return test_matcher
    return test_matcher
