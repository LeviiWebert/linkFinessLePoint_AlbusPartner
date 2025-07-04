"""
Script de démonstration du prompt interactif
Montre les différentes options disponibles au lancement
"""

import sys
import os

# Simuler un environnement de test
print("🏥 === MATCHING D'ÉTABLISSEMENTS DE SANTÉ AVEC IA ===")
print("Version modulaire - Optimisée pour Gemini 1.5 Flash")
print("=" * 60)

print("\n📋 OPTIONS DE TRAITEMENT:")
print("1. Reprendre l'historique existant (recommandé)")
print("2. Recommencer à zéro (efface l'historique)")
print("3. Quitter")

print("\n💡 EXEMPLES D'USAGE :")
print()
print("🔄 Choix 1 - Reprendre l'historique :")
print("   → Idéal après une interruption du script")
print("   → Continue là où le travail s'était arrêté")
print("   → Évite de refaire les requêtes IA déjà effectuées")
print("   → Économise du temps et des tokens")

print("\n🆕 Choix 2 - Recommencer à zéro :")
print("   → Efface tout l'historique précédent")
print("   → Demande une confirmation de sécurité")
print("   → Recommence le matching complet")
print("   → Utile si vous voulez tester de nouveaux paramètres")

print("\n🚪 Choix 3 - Quitter :")
print("   → Sort proprement du programme")
print("   → Aucune modification n'est effectuée")

print("\n📊 AVANTAGES DE CETTE APPROCHE :")
print("✅ Gestion intelligente de l'historique")
print("✅ Reprise automatique après interruption")
print("✅ Économie de ressources IA")
print("✅ Flexibilité d'usage")
print("✅ Protection contre les erreurs")
print("✅ Interface utilisateur conviviale")

print("\n🛡️ SÉCURITÉ :")
print("• Sauvegarde automatique tous les 10 hôpitaux traités")
print("• Confirmation requise pour effacer l'historique")
print("• Gestion propre des interruptions (Ctrl+C)")
print("• Validation des données avant traitement")

print("\n📁 FICHIERS GÉNÉRÉS :")
print(f"• Fichier de résultats principal")
print(f"• Sauvegardes automatiques en cours de traitement")
print(f"• Logs de progression détaillés")
