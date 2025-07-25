# Matching d'Établissements de Santé avec IA

## 📝 Description

Ce projet permet de faire correspondre automatiquement des établissements de santé (hôpitaux et cliniques) entre deux bases de données en utilisant l'intelligence artificielle de Google Gemini.

## 🏗️ Architecture

Le code est organisé en modules spécialisés :

### 📁 Structure des fichiers

```
LinkFinessData/
├── config.py                     # Configuration centralisée
├── main/                         # Scripts principaux
│   ├── main.py                   # Point d'entrée du programme
│   ├── linkmain.py              # Version classique du matching
│   └── linkmainAI.py            # Version avec IA (ancien fichier)
├── service/                      # Services et utilitaires
│   ├── ai_service.py            # Service IA pour les comparaisons
│   ├── AIRateLimiter.py         # Ancien rate limiter
│   ├── establishment_utils.py    # Utilitaires pour les établissements
│   ├── hospital_matcher.py      # Processeur principal de matching
│   ├── rate_limiter.py          # Gestionnaire de limites API
│   └── text_cleaner.py          # Utilitaires de nettoyage de texte
├── test_script/                  # Scripts de test
│   ├── testAPIAI.py             # Tests API IA
│   ├── testfilitre.py           # Tests de filtrage
│   ├── vsansdebug.py            # Version sans debug
│   └── vsansville.py            # Tests par ville
└── README.md                     # Documentation
```

## 🗂️ Organisation du projet

### 📋 **Scripts principaux**
- **`main/main.py`** - Version modulaire moderne avec IA optimisée
- **`main/linkmain.py`** - Version classique avec matching simple
- **`main/linkmainAI.py`** - Version legacy monolithique (historique)

### ⚙️ **Services**
- **`service/hospital_matcher.py`** - Logique de matching principal
- **`service/ai_service.py`** - Interface avec Google Gemini
- **`service/establishment_utils.py`** - Utilitaires métier
- **`service/rate_limiter.py`** - Gestion des limites API

### 🧪 **Tests et validation**
- **`test_script/testAPIAI.py`** - Validation de l'API Google AI
- **`test_script/testfilitre.py`** - Tests des algorithmes de filtrage
- **`test_script/vsansdebug.py`** - Version optimisée sans logs
- **`test_script/vsansville.py`** - Tests spécifiques par ville

## 🚀 Utilisation

### Prérequis

```bash
pip install pandas openpyxl fuzzywuzzy google-generativeai
```

### Exécution

#### Version principale (recommandée)
```bash
cd main/
python main.py
```

**🎛️ Prompt interactif au lancement :**

Le script vous proposera 3 options :

1. **Reprendre l'historique existant (recommandé)** : Continue le traitement là où il s'était arrêté, en utilisant le fichier de résultats existant
2. **Recommencer à zéro** : Efface l'historique et recommence un traitement complet (avec demande de confirmation)
3. **Quitter** : Sort du programme

Cette fonctionnalité permet de :
- ✅ Reprendre le travail après une interruption
- ✅ Éviter de perdre du temps et des requêtes IA
- ✅ Gérer différents scénarios d'usage
- ✅ Éviter les doublons et optimiser les ressources

#### Versions alternatives
```bash
# Version classique sans IA
cd main/
python linkmain.py

# Version monolithique avec IA (legacy)
cd main/
python linkmainAI.py
```

#### Tests
```bash
# Test de l'API IA
cd test_script/
python testAPIAI.py

# Tests de filtrage
python testfilitre.py
```

## 🎯 Fonctionnalités

- **Matching intelligent** : Fuzzy matching + IA
- **Détection automatique** : Différencie hôpitaux et cliniques
- **Optimisation API** : Respect des limites (15 req/min)
- **Statistiques** : Suivi en temps réel

## 📈 Performance

- Fuzzy matching : ~85% des cas résolus sans IA
- IA : ~15% des cas complexes
- Précision : >95% de matches corrects

## ⚙️ Configuration

Le fichier `config.py` centralise tous les paramètres :

```python
# Chemins des fichiers Excel
PATH_TABLE_A = "votre_fichier_source.xlsx"
PATH_TABLE_B = "votre_fichier_reference.xlsx"  
OUTPUT_PATH = "resultats.xlsx"

# Paramètres de matching
FUZZY_THRESHOLD = 85  # Score minimum pour match fuzzy
MAX_REQUESTS_PER_MINUTE = 15  # Limite API Google

# Clé API Google AI
GOOGLE_API_KEY = "votre_cle_api_google"
```

## 🔧 Personnalisation

### Modifier les seuils de matching
```python
# Dans config.py
FUZZY_THRESHOLD = 90  # Plus strict
```

### Ajouter des mots-clés d'établissements
```python
# Dans service/establishment_utils.py
clinic_keywords = ["CLINIQUE", "VOTRE_MOT_CLE"]
hospital_keywords = ["HOPITAL", "CHU", "VOTRE_MOT_CLE"]
```

### Personnaliser les prompts IA
```python
# Dans service/ai_service.py
# Modifier la fonction ai_compare_hospital_names_batch()
```

## 🐛 Débogage et versions

### 📁 Scripts disponibles
| Script | Description | Usage |
|--------|-------------|-------|
| `main/main.py` | Version moderne modulaire | Production recommandée |
| `main/linkmain.py` | Version classique | Test sans IA |
| `main/linkmainAI.py` | Version legacy | Compatibilité historique |
| `test_script/testAPIAI.py` | Test API Google | Validation connexion |
| `test_script/testfilitre.py` | Test filtres | Debug algorithmes |

### 🔍 Debugging
```bash
# Logs détaillés avec la version principale
cd main/
python main.py

# Version sans debug pour performance
cd test_script/  
python vsansdebug.py

# Test spécifique par ville
python vsansville.py
```

### 📊 Monitoring
Le système affiche des statistiques en temps réel :
```
🎉 === RÉSULTATS FINAUX ===
📊 Établissements traités: 167
🤖 Requêtes IA utilisées: 25  
✅ Matches trouvés: 159/167 (95.2%)
```