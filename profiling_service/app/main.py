from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from config import connect_to_mongodb, close_mongodb_connection, setup_logging, settings
from routes.recommend import router as recommend_router

# Configuration du logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application"""
    # Démarrage
    logger.info("🚀 Démarrage du service de profiling...")
    try:
        await connect_to_mongodb()
        logger.info("✅ Service de profiling prêt")
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise
    
    yield
    
    # Arrêt
    logger.info("🔄 Arrêt du service de profiling...")
    await close_mongodb_connection()
    logger.info("✅ Service de profiling arrêté proprement")

# Création de l'application FastAPI
app = FastAPI(
    title="Profiling Service API",
    description="""
    API de recommandation d'appels d'offres pour les chefs d'entreprise marocains.
    
    Ce service permet de :
    - Créer et gérer des profils d'entreprise
    - Générer des recommandations personnalisées d'appels d'offres
    - Suivre les interactions et améliorer les recommandations
    - Fournir des statistiques d'engagement
    
    ## Fonctionnalités principales :
    
    ### Profiling
    - **Création de profil** : Questionnaire d'onboarding pour définir les préférences
    - **Mise à jour** : Modification des préférences utilisateur
    - **Suggestions** : Aide à la saisie (villes, mots-clés, secteurs)
    
    ### Recommandations
    - **Algorithme de scoring** : Basé sur 6 critères pondérés
    - **Filtrage intelligent** : Exclusions et préférences utilisateur
    - **Explications** : Raisons des recommandations fournies
    
    ### Analytics
    - **Tracking des interactions** : Vues, clics, favoris, candidatures
    - **Score d'engagement** : Évaluation de l'activité utilisateur
    - **Statistiques** : Tableaux de bord personnalisés
    """,
    version="1.0.0",
    contact={
        "name": "Équipe Développement",
        "email": "wiwidev@votreentreprise.ma",
    },
    license_info={
        "name": "Propriétaire",
    },
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(recommend_router)

# Routes de base
@app.get("/", tags=["Système"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "service": "Profiling Service API",
        "version": "1.0.0",
        "status": "active",
        "environment": settings.__class__.__name__,
        "features": {
            "profiling": True,
            "recommendations": True,
            "analytics": True,
            "ml_scoring": settings.ENABLE_ML_SCORING,
            "notifications": settings.ENABLE_NOTIFICATIONS
        }
    }

@app.get("/health", tags=["Système"])
async def health_check():
    """Vérification de l'état du service"""
    from config import get_database
    
    try:
        # Test de connexion MongoDB
        db = await get_database()
        await db.command("ping")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/stats/global", tags=["Système"])
async def get_global_stats():
    """Statistiques globales du système"""
    from config import get_database
    
    try:
        db = await get_database()
        
        # Compter les documents dans chaque collection
        stats = {
            "users_total": await db.user_profiles.count_documents({}),
            "users_with_complete_profile": await db.user_profiles.count_documents({"profil_complete": True}),
            "appels_offres_actifs": await db.appels_offres.count_documents({
                "date_limite": {"$gte": "2025-01-01T00:00:00Z"}
            }),
            "interactions_total": await db.interactions_users.count_documents({}),
            "secteurs_disponibles": len(settings.BusinessConstants.SECTEURS_ACTIVITE),
            "villes_disponibles": len(settings.BusinessConstants.VILLES_PRINCIPALES)
        }
        
        # Calculer le taux de profils complets
        if stats["users_total"] > 0:
            stats["taux_profils_complets"] = round(
                (stats["users_with_complete_profile"] / stats["users_total"]) * 100, 2
            )
        else:
            stats["taux_profils_complets"] = 0.0
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": "2025-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")

# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erreur interne du serveur",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else "Une erreur inattendue s'est produite"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )