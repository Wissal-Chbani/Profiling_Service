# Profiling Service API

Service de recommandation d'appels d'offres intelligent pour les chefs d'entreprise marocains.

## 📋 Aperçu

Ce service fait partie d'une application mobile destinée aux entrepreneurs marocains. Il centralise et analyse les opportunités business (appels d'offres, événements, réglementations) en utilisant un moteur d'analyse intelligent basé sur des règles métier et des techniques NLP/ML.

### Fonctionnalités principales

- **Profiling intelligent** : Questionnaire d'onboarding adaptatif
- **Recommandations personnalisées** : Algorithme de scoring multi-critères
- **Apprentissage automatique** : Amélioration continue basée sur les interactions
- **Analytics avancées** : Tableaux de bord et statistiques d'engagement
- **API RESTful** : Interface complète pour applications mobiles

## 🏗️ Architecture

```
profiling_service/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application FastAPI principale
│   ├── config.py              # Configuration et connexion DB
│   │
│   ├── models/
│   │   └── user_profile.py    # Modèles Pydantic (UserProfile, AppelOffre, etc.)
│   │
│   ├── routes/
│   │   └── recommend.py       # Routes API pour recommandations
│   │
│   ├── services/
│   │   └── scoring.py         # Service de calcul de score de pertinence
│   │
│   └── utils/
│       └── keywords.py        # Utilitaires pour extraction de mots-clés
│
├── .env                       # Variables d'environnement
├── requirements.txt           # Dépendances Python
├── .gitignore
└── README.md
```

## 🚀 Installation et Démarrage

### Prérequis

- Python 3.8+
- MongoDB 4.4+
- Git

### Installation

1. **Cloner le projet**
```bash
git clone https://github.com/votre-username/profiling-service.git
cd profiling-service
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
cp .env.example .env
# Éditer le fichier .env avec vos paramètres
```

5. **Démarrer MongoDB**
```bash
# Sur Ubuntu/Debian
sudo systemctl start mongod

# Ou avec Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

6. **Lancer l'application**
```bash
python app/main.py
```

L'API sera accessible sur `http://localhost:8000`

## 📊 Algorithme de Scoring

Le système utilise un algorithme de scoring multi-critères pour évaluer la pertinence des appels d'offres :

### Critères et Pondération

| Critère | Poids | Description |
|---------|-------|-------------|
| **Secteur d'activité** | 25% | Correspondance avec les secteurs de l'entreprise |
| **Géographique** | 20% | Localisation et rayon d'intervention |
| **Financier** | 20% | Budget et caution compatibles |
| **Temporel** | 15% | Délais selon préférences |
| **Mots-clés métier** | 15% | Analyse NLP du contenu |
| **Classification** | 5% | Type d'appel d'offres |

### Exemple de Calcul

```python
# Pour un appel d'offres donné
score_total = (
    score_secteur * 0.25 +
    score_geographique * 0.20 +
    score_financier * 0.20 +
    score_temporel * 0.15 +
    score_mots_cles * 0.15 +
    score_classification * 0.05
)

# Seuils de recommandation
if score_total >= 0.8:
    categorie = "Très pertinent"
elif score_total >= 0.6:
    categorie = "Pertinent"
else:
    categorie = "Peu pertinent"
```

## 🔗 API Endpoints

### Profiling

- `POST /recommend/profile` - Créer/mettre à jour un profil
- `GET /recommend/profile/{user_id}` - Récupérer un profil
- `PUT /recommend/profile/{user_id}/preferences` - Mettre à jour les préférences

### Recommandations

- `GET /recommend/appels-offres/{user_id}` - Obtenir les recommandations
- `POST /recommend/interaction` - Enregistrer une interaction

### Analytics

- `GET /recommend/stats/{user_id}` - Statistiques utilisateur
- `GET /stats/global` - Statistiques globales du système

### Utilitaires

- `GET /recommend/suggest/keywords` - Suggérer des mots-clés
- `GET /recommend/suggest/villes` - Suggérer des villes

## 💾 Modèles de Données

### UserProfile

```python
{
    "user_id": "user_123",
    "email": "chef@entreprise.ma",
    "nom_entreprise": "TechnoServices SARL",
    "secteur_activite": ["informatique", "telecommunications"],
    "taille_entreprise": "pme",
    "villes_preferees": ["Casablanca", "Rabat"],
    "rayon_intervention": "regional",
    "budget_min": 50000,
    "budget_max": 500000,
    "caution_max": 50000,
    "delai_preference": "moyen",
    "mots_cles_metier": ["développement web", "cybersécurité"],
    "classifications_preferees": ["services informatiques"],
    "profil_complete": true
}
```

### AppelOffre

```python
{
    "numero": "AO2025001",
    "reference": "REF-2025-001",
    "organisme": "Ministère de l'Intérieur",
    "objet": "Développement d'une application de gestion",
    "caution": 25000,
    "budget": 300000,
    "ville": "Rabat",
    "date_limite": "2025-02-15T23:59:59Z",
    "secteur": "informatique",
    "classification": "services informatiques",
    "texte_analyse": "développement web application mobile base données"
}
```

## 🧪 Tests

```bash
# Installer les dépendances de test
pip install pytest pytest-asyncio httpx

# Lancer les tests
pytest tests/

# Tests avec couverture
pytest --cov=app tests/
```

## 📈 Monitoring et Logs

Les logs sont configurés pour suivre :
- Connexions/déconnexions MongoDB
- Erreurs d'API
- Performance des recommandations
- Interactions utilisateurs

```bash
# Voir les logs en temps réel
tail -f profiling_service.log
```

## 🔧 Configuration Avancée

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `ENVIRONMENT` | Environnement (dev/prod/test) | development |
| `MONGODB_URL` | URL de connexion MongoDB | mongodb://localhost:27017 |
| `API_PORT` | Port de l'API | 8000 |
| `LOG_LEVEL` | Niveau de log | INFO |
| `ENABLE_ML_SCORING` | Activer le scoring ML | false |

### Optimisations MongoDB

```javascript
// Index recommandés
db.user_profiles.createIndex({ "user_id": 1 }, { unique: true })
db.appels_offres.createIndex({ "secteur": 1, "ville": 1, "date_limite": 1 })
db.interactions_users.createIndex({ "user_id": 1, "timestamp": -1 })
```

## 🚀 Déploiement

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app/main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
    depends_on:
      - mongo
  
  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

## 🔮 Roadmap

### Version 1.1
- [ ] Système de notifications push
- [ ] Cache Redis pour améliorer les performances
- [ ] API de gestion des favoris

### Version 1.2
- [ ] Machine Learning avancé (modèles personnalisés)
- [ ] Analyse sentiment des interactions
- [ ] Recommandations collaboratives

### Version 2.0
- [ ] Intégration intelligence artificielle
- [ ] Prédiction de succès des candidatures
- [ ] Tableau de bord analytics avancé
