import os
from typing import Optional
import motor.motor_asyncio
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configuration de l'application"""
    ENVIRONMENT: str = Field(default="development")
    
    # Configuration MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "profiling_service"
    
    # Configuration API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Configuration JWT (pour l'authentification future)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Configuration logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configuration scoring
    SCORING_CACHE_TTL: int = 300  # 5 minutes
    MAX_RECOMMENDATIONS: int = 100
    DEFAULT_RECOMMENDATIONS: int = 20
    
    # Configuration notifications
    ENABLE_NOTIFICATIONS: bool = True
    NOTIFICATION_BATCH_SIZE: int = 50
    
    # Configuration ML/NLP (pour futures améliorations)
    ENABLE_ML_SCORING: bool = False
    ML_MODEL_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instance globale des paramètres
settings = Settings()

# Client MongoDB global
mongodb_client = None
database = None

async def connect_to_mongodb():
    """Établit la connexion à MongoDB"""
    global mongodb_client, database
    
    try:
        mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        database = mongodb_client[settings.MONGODB_DATABASE]
        
        # Test de la connexion
        await database.command("ping")
        print(f"✅ Connexion MongoDB établie: {settings.MONGODB_DATABASE}")
        
        # Créer les index nécessaires
        await create_indexes()
        
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {e}")
        raise

async def close_mongodb_connection():
    """Ferme la connexion MongoDB"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✅ Connexion MongoDB fermée")

async def get_database():
    """Retourne l'instance de la base de données"""
    global database
    if database is None:
        await connect_to_mongodb()
    return database

async def create_indexes():
    """Crée les index nécessaires pour optimiser les performances"""
    global database
    
    try:
        # Index pour la collection user_profiles
        await database.user_profiles.create_index("user_id", unique=True)
        await database.user_profiles.create_index("email", unique=True)
        await database.user_profiles.create_index("secteur_activite")
        await database.user_profiles.create_index("villes_preferees")
        await database.user_profiles.create_index("date_modification")
        
        # Index pour la collection appels_offres
        await database.appels_offres.create_index("numero", unique=True)
        await database.appels_offres.create_index("secteur")
        await database.appels_offres.create_index("ville")
        await database.appels_offres.create_index("date_limite")
        await database.appels_offres.create_index("budget")
        await database.appels_offres.create_index("classification")
        
        # Index composé pour les recherches fréquentes
        await database.appels_offres.create_index([
            ("secteur", 1),
            ("ville", 1),
            ("date_limite", 1)
        ])
        
        # Index pour la collection interactions_users
        await database.interactions_users.create_index("user_id")
        await database.interactions_users.create_index("appel_offre_id")
        await database.interactions_users.create_index("timestamp")
        await database.interactions_users.create_index([
            ("user_id", 1),
            ("timestamp", -1)
        ])
        
        # Index de texte pour la recherche textuelle
        await database.appels_offres.create_index([
            ("objet", "text"),
            ("texte_analyse", "text")
        ])
        
        print("✅ Index MongoDB créés avec succès")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la création des index: {e}")

# Configuration du logging
import logging

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("profiling_service.log")
        ]
    )
    
    # Logger spécifique pour MongoDB
    logging.getLogger("motor").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Configuration des constantes métier
class BusinessConstants:
    """Constantes métier pour le système de recommandation"""
    
    # Villes principales du Maroc
    VILLES_PRINCIPALES = [
        "Casablanca", "Rabat", "Fès", "Marrakech", "Tanger", "Agadir",
        "Meknès", "Oujda", "Salé", "Témara", "Mohammedia", "Settat",
        "Safi", "El Jadida", "Nador", "Tétouan", "Béni Mellal", "Khémisset",
        "Khouribga", "Larache", "Berkane", "Chefchaouen", "Ouarzazate"
    ]
    
    # Régions du Maroc
    REGIONS_MAROC = {
        "Tanger-Tétouan-Al Hoceïma": ["Tanger", "Tétouan", "Al Hoceïma", "Larache", "Chefchaouen"],
        "Oriental": ["Oujda", "Nador", "Berkane", "Taourirt", "Jerada"],
        "Fès-Meknès": ["Fès", "Meknès", "Ifrane", "Khenifra", "Errachidia"],
        "Rabat-Salé-Kénitra": ["Rabat", "Salé", "Témara", "Kénitra", "Skhirat"],
        "Béni Mellal-Khénifra": ["Béni Mellal", "Khouribga", "Azilal", "Khénifra"],
        "Casablanca-Settat": ["Casablanca", "Settat", "Mohammedia", "El Jadida", "Berrechid"],
        "Marrakech-Safi": ["Marrakech", "Safi", "Essaouira", "Kelaat Es-Seraghna"],
        "Drâa-Tafilalet": ["Ouarzazate", "Zagora", "Tinghir", "Midelt"],
        "Souss-Massa": ["Agadir", "Tiznit", "Taroudant", "Inezgane"],
        "Guelmim-Oued Noun": ["Guelmim", "Tan-Tan", "Sidi Ifni"],
        "Laâyoune-Sakia El Hamra": ["Laâyoune", "Boujdour", "Smara"],
        "Dakhla-Oued Ed-Dahab": ["Dakhla", "Aousserd"]
    }
    
    # Secteurs d'activité principaux
    SECTEURS_ACTIVITE = [
        "Informatique et télécommunications",
        "Bâtiment et travaux publics",
        "Transport et logistique",
        "Santé et médical",
        "Éducation et formation",
        "Agriculture et agroalimentaire",
        "Énergie et environnement",
        "Tourisme et hôtellerie",
        "Industrie et manufacturing",
        "Finance et assurance",
        "Communication et marketing",
        "Sécurité et surveillance",
        "Textile et cuir",
        "Conseil et services aux entreprises",
        "Commerce et distribution"
    ]
    
    # Types de prestations
    TYPES_PRESTATIONS = [
        "Fourniture",
        "Service",
        "Travaux",
        "Études",
        "Formation",
        "Maintenance",
        "Installation",
        "Conseil",
        "Audit",
        "Assistance technique"
    ]
    
    # Tranches budgétaires (en MAD)
    TRANCHES_BUDGET = {
        "Très petit marché": (0, 50000),
        "Petit marché": (50000, 200000),
        "Marché moyen": (200000, 1000000),
        "Grand marché": (1000000, 5000000),
        "Très grand marché": (5000000, float('inf'))
    }
    
    # Délais types
    DELAIS_TYPES = {
        "Très urgent": 7,      # < 7 jours
        "Urgent": 15,          # < 15 jours
        "Court terme": 30,     # < 30 jours
        "Moyen terme": 90,     # < 90 jours
        "Long terme": 365      # < 1 an
    }

# Configuration de développement vs production
class DevelopmentConfig(Settings):
    """Configuration pour l'environnement de développement"""
    API_RELOAD: bool = True
    LOG_LEVEL: str = "DEBUG"
    MONGODB_DATABASE: str = "profiling_service_dev"

class ProductionConfig(Settings):
    """Configuration pour l'environnement de production"""
    API_RELOAD: bool = False
    LOG_LEVEL: str = "INFO"
    MONGODB_DATABASE: str = "profiling_service_prod"
    ENABLE_NOTIFICATIONS: bool = True

class TestConfig(Settings):
    """Configuration pour les tests"""
    MONGODB_DATABASE: str = "profiling_service_test"
    LOG_LEVEL: str = "DEBUG"
    ENABLE_NOTIFICATIONS: bool = False

# Sélection de l'environnement
def get_settings() -> Settings:
    """Retourne la configuration selon l'environnement"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "test":
        return TestConfig()
    else:
        return DevelopmentConfig()

# Instance de configuration basée sur l'environnement
settings = get_settings()