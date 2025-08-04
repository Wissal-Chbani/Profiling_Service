from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.user_profile import UserProfile, AppelOffre, InteractionUser
from services.scoring import ScoringService
from utils.keywords import KeywordExtractor
from config import get_database

router = APIRouter(prefix="/recommend", tags=["Recommandations"])
logger = logging.getLogger(__name__)

# Injection de dépendances
def get_scoring_service():
    return ScoringService()

def get_keyword_extractor():
    return KeywordExtractor()

@router.post("/profile", summary="Créer ou mettre à jour le profil utilisateur")
async def create_or_update_profile(
    profile: UserProfile,
    db = Depends(get_database)
):
    """Créer ou mettre à jour le profil d'un utilisateur"""
    try:
        # ✅ CORRECTION : Ne plus forcer profil_complete = True
        # Le @root_validator dans UserProfile se charge automatiquement de définir profil_complete
        
        # Mettre à jour la date de modification
        profile.date_modification = datetime.utcnow()
        
        # Sauvegarder en base
        collection = db[UserProfile.Config.collection]
        
        # Upsert (update or insert)
        result = await collection.replace_one(
            {"user_id": profile.user_id},
            profile.dict(),
            upsert=True
        )
        
        logger.info(f"Profil {'créé' if result.upserted_id else 'mis à jour'} pour user_id: {profile.user_id}")
        logger.info(f"Profil complet: {profile.profil_complete}")
        
        return {
            "success": True,
            "message": "Profil sauvegardé avec succès",
            "user_id": profile.user_id,
            "profile_complete": profile.profil_complete
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du profil: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du profil")

@router.get("/profile/{user_id}", summary="Récupérer le profil utilisateur")
async def get_profile(
    user_id: str,
    db = Depends(get_database)
):
    """Récupérer le profil d'un utilisateur"""
    try:
        collection = db[UserProfile.Config.collection]
        profile_data = await collection.find_one({"user_id": user_id})
        
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profil utilisateur non trouvé")
        
        # Supprimer l'_id MongoDB pour la sérialisation
        profile_data.pop('_id', None)
        profile = UserProfile(**profile_data)
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du profil")

@router.put("/profile/{user_id}/refresh-completeness", summary="Recalculer la complétude du profil")
async def refresh_profile_completeness(
    user_id: str,
    db = Depends(get_database)
):
    """Recalcule et met à jour la complétude d'un profil existant"""
    try:
        collection = db[UserProfile.Config.collection]
        profile_data = await collection.find_one({"user_id": user_id})
        
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profil utilisateur non trouvé")
        
        # Supprimer l'_id MongoDB
        profile_data.pop('_id', None)
        
        # Recréer l'objet UserProfile pour déclencher la validation
        profile = UserProfile(**profile_data)
        
        # Sauvegarder avec la nouvelle valeur de profil_complete
        await collection.replace_one(
            {"user_id": user_id},
            profile.dict()
        )
        
        logger.info(f"Complétude recalculée pour user_id: {user_id} -> {profile.profil_complete}")
        
        return {
            "success": True,
            "message": "Complétude du profil recalculée",
            "user_id": user_id,
            "profile_complete": profile.profil_complete,
            "updated_at": profile.date_modification
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du recalcul de complétude: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du recalcul de complétude")

@router.get("/appels-offres/{user_id}", summary="Obtenir les appels d'offres recommandés")
async def get_recommended_appels_offres(
    user_id: str,
    limite: int = Query(20, ge=1, le=100, description="Nombre d'appels d'offres à retourner"),
    score_min: float = Query(0.6, ge=0.0, le=1.0, description="Score minimum de pertinence"),
    scoring_service: ScoringService = Depends(get_scoring_service),
    db = Depends(get_database)
):
    """Récupérer les appels d'offres recommandés pour un utilisateur"""
    try:
        # Récupérer le profil utilisateur
        profiles_collection = db[UserProfile.Config.collection]
        profile_data = await profiles_collection.find_one({"user_id": user_id})
        
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profil utilisateur non trouvé")
        
        profile_data.pop('_id', None)
        profil = UserProfile(**profile_data)
        
        if not profil.profil_complete:
            return {
                "success": False,
                "message": "Profil incomplet. Veuillez compléter votre profil pour recevoir des recommandations.",
                "recommendations": [],
                "missing_fields": _get_missing_fields(profil)
            }
        
        # Récupérer les appels d'offres actifs
        appels_collection = db[AppelOffre.Config.collection]
        
        # Filtre pour appels d'offres actifs (non expirés)
        filter_query = {
            "date_limite": {"$gte": datetime.utcnow()}
        }
        
        appels_data = await appels_collection.find(filter_query).to_list(length=1000)
        
        if not appels_data:
            return {
                "success": True,
                "message": "Aucun appel d'offres actif trouvé",
                "recommendations": []
            }
        
        # Convertir en objets AppelOffre
        appels_offres = []
        for appel_data in appels_data:
            appel_data.pop('_id', None)
            appels_offres.append(AppelOffre(**appel_data))
        
        # Calculer les recommandations
        scoring_service.seuil_recommandation = score_min
        recommandations = scoring_service.recommander_appels_offres(profil, appels_offres, limite)
        
        # Formater la réponse
        resultats = []
        for appel_offre, score_detail in recommandations:
            resultats.append({
                "appel_offre": appel_offre.dict(),
                "score": {
                    "total": round(score_detail.score_total, 3),
                    "secteur": round(score_detail.score_secteur, 3),
                    "geographique": round(score_detail.score_geographique, 3),
                    "financier": round(score_detail.score_financier, 3),
                    "temporel": round(score_detail.score_temporel, 3),
                    "mots_cles": round(score_detail.score_mots_cles, 3),
                    "classification": round(score_detail.score_classification, 3)
                },
                "raisons": score_detail.raisons,
                "penalites": score_detail.penalites,
                "categorie": scoring_service.categoriser_recommandation(score_detail.score_total)
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "total_recommandations": len(resultats),
            "recommendations": resultats,
            "metadata": {
                "total_appels_actifs": len(appels_offres),
                "score_minimum": score_min,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération des recommandations")

@router.post("/interaction", summary="Enregistrer une interaction utilisateur")
async def record_interaction(
    interaction: InteractionUser,
    db = Depends(get_database)
):
    """Enregistrer une interaction utilisateur pour améliorer les recommandations"""
    try:
        collection = db[InteractionUser.Config.collection]
        
        # Sauvegarder l'interaction
        result = await collection.insert_one(interaction.dict())
        
        # Mettre à jour le score d'engagement de l'utilisateur
        await update_user_engagement_score(interaction.user_id, interaction.type_interaction, db)
        
        logger.info(f"Interaction enregistrée: {interaction.type_interaction} pour user {interaction.user_id}")
        
        return {
            "success": True,
            "message": "Interaction enregistrée avec succès",
            "interaction_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'interaction: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement de l'interaction")

@router.get("/stats/{user_id}", summary="Statistiques des recommandations")
async def get_recommendation_stats(
    user_id: str,
    periode_jours: int = Query(30, ge=1, le=365, description="Période en jours pour les statistiques"),
    db = Depends(get_database)
):
    """Obtenir des statistiques sur les recommandations et interactions d'un utilisateur"""
    try:
        from datetime import timedelta
        
        date_debut = datetime.utcnow() - timedelta(days=periode_jours)
        
        # Récupérer les interactions de la période
        interactions_collection = db[InteractionUser.Config.collection]
        interactions = await interactions_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": date_debut}
        }).to_list(length=1000)
        
        # Calculer les statistiques
        stats = {
            "total_interactions": len(interactions),
            "interactions_par_type": {},
            "taux_engagement": 0.0,
            "appels_favoris": 0,
            "candidatures": 0,
            "duree_moyenne_consultation": 0.0
        }
        
        # Analyser les interactions
        durees_consultation = []
        for interaction in interactions:
            type_inter = interaction.get("type_interaction", "unknown")
            stats["interactions_par_type"][type_inter] = stats["interactions_par_type"].get(type_inter, 0) + 1
            
            if type_inter == "favori":
                stats["appels_favoris"] += 1
            elif type_inter == "candidature":
                stats["candidatures"] += 1
            
            if interaction.get("duree_consultation"):
                durees_consultation.append(interaction["duree_consultation"])
        
        # Calculer la durée moyenne de consultation
        if durees_consultation:
            stats["duree_moyenne_consultation"] = sum(durees_consultation) / len(durees_consultation)
        
        # Calculer le taux d'engagement
        vues = stats["interactions_par_type"].get("vue", 0)
        actions = stats["appels_favoris"] + stats["candidatures"]
        if vues > 0:
            stats["taux_engagement"] = (actions / vues) * 100
        
        return {
            "success": True,
            "user_id": user_id,
            "periode_jours": periode_jours,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")

@router.put("/profile/{user_id}/preferences", summary="Mettre à jour les préférences utilisateur")
async def update_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    db = Depends(get_database)
):
    """Mettre à jour seulement les préférences d'un utilisateur"""
    try:
        collection = db[UserProfile.Config.collection]
        
        # Champs autorisés pour la mise à jour
        champs_autorises = {
            'secteur_activite', 'villes_preferees', 'rayon_intervention',
            'budget_min', 'budget_max', 'caution_max', 'delai_preference',
            'mots_cles_metier', 'classifications_preferees', 'secteurs_exclus',
            'villes_exclues', 'notifications_actives', 'frequence_notifications'
        }
        
        # Filtrer les préférences valides
        updates = {k: v for k, v in preferences.items() if k in champs_autorises}
        updates['date_modification'] = datetime.utcnow()
        
        if not updates:
            raise HTTPException(status_code=400, detail="Aucune préférence valide fournie")
        
        # Récupérer le profil actuel pour recalculer la complétude
        profile_data = await collection.find_one({"user_id": user_id})
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profil utilisateur non trouvé")
        
        # Supprimer l'_id MongoDB
        profile_data.pop('_id', None)
        
        # Appliquer les mises à jour
        profile_data.update(updates)
        
        # Recréer l'objet UserProfile pour déclencher la validation de complétude
        profile = UserProfile(**profile_data)
        
        # Sauvegarder avec la nouvelle valeur de profil_complete
        result = await collection.replace_one(
            {"user_id": user_id},
            profile.dict()
        )
        
        logger.info(f"Préférences mises à jour pour user_id: {user_id}")
        logger.info(f"Nouveau statut profil_complete: {profile.profil_complete}")
        
        return {
            "success": True,
            "message": "Préférences mises à jour avec succès",
            "updated_fields": list(updates.keys()),
            "profile_complete": profile.profil_complete
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des préférences: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour des préférences")

@router.get("/suggest/keywords", summary="Suggérer des mots-clés métier")
async def suggest_keywords(
    secteur: str = Query(..., description="Secteur d'activité"),
    keyword_extractor: KeywordExtractor = Depends(get_keyword_extractor)
):
    """Suggérer des mots-clés métier basés sur le secteur d'activité"""
    try:
        suggestions = keyword_extractor.get_keywords_by_sector(secteur)
        
        return {
            "success": True,
            "secteur": secteur,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la suggestion de mots-clés: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suggestion de mots-clés")

@router.get("/suggest/villes", summary="Suggérer des villes selon la région")
async def suggest_cities(
    region: Optional[str] = Query(None, description="Région du Maroc"),
    db = Depends(get_database)
):
    """Suggérer des villes selon la région ou retourner toutes les villes populaires"""
    try:
        # Mapping des villes par région
        villes_par_region = {
            "grand_casablanca": ["Casablanca", "Mohammedia", "Settat", "Berrechid", "El Jadida"],
            "rabat_sale": ["Rabat", "Salé", "Témara", "Skhirat", "Khémisset"],
            "fes_meknes": ["Fès", "Meknès", "Ifrane", "Khenifra", "Errachidia"],
            "marrakech_safi": ["Marrakech", "Safi", "Essaouira", "Kelaat Es-Seraghna"],
            "tanger_tetouan": ["Tanger", "Tétouan", "Larache", "Chefchaouen", "Al Hoceima"],
            "oriental": ["Oujda", "Nador", "Berkane", "Taourirt", "Jerada"],
            "souss_massa": ["Agadir", "Tiznit", "Taroudant", "Ouarzazate", "Zagora"],
            "beni_mellal": ["Beni Mellal", "Khouribga", "Azilal", "Fquih Ben Salah"],
            "draa_tafilalet": ["Ouarzazate", "Zagora", "Tinghir", "Midelt"],
            "laayoune": ["Laayoune", "Dakhla", "Boujdour", "Smara"],
            "guelmim": ["Guelmim", "Tan-Tan", "Sidi Ifni", "Assa-Zag"]
        }
        
        if region and region.lower() in villes_par_region:
            suggestions = villes_par_region[region.lower()]
        else:
            # Retourner les villes les plus populaires
            suggestions = [
                "Casablanca", "Rabat", "Fès", "Marrakech", "Tanger", "Agadir",
                "Meknès", "Oujda", "Salé", "Témara", "Mohammedia", "Settat",
                "Safi", "El Jadida", "Nador", "Tétouan", "Béni Mellal", "Khémisset"
            ]
        
        return {
            "success": True,
            "region": region,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la suggestion de villes: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suggestion de villes")

# Fonction utilitaire pour mettre à jour le score d'engagement
async def update_user_engagement_score(user_id: str, type_interaction: str, db):
    """Mettre à jour le score d'engagement utilisateur basé sur les interactions"""
    try:
        # Pondération des actions
        poids_actions = {
            "vue": 1,
            "clic": 2,
            "favori": 5,
            "candidature": 10,
            "ignore": -1
        }
        
        points = poids_actions.get(type_interaction, 0)
        
        if points != 0:
            collection = db[UserProfile.Config.collection]
            await collection.update_one(
                {"user_id": user_id},
                {"$inc": {"score_engagement": points}}
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du score d'engagement: {e}")

def _get_missing_fields(profil: UserProfile) -> List[str]:
    """Identifie les champs manquants pour un profil complet"""
    missing = []
    
    if not profil.villes_preferees or len(profil.villes_preferees) == 0:
        missing.append("villes_preferees")
    
    if not profil.secteur_activite or len(profil.secteur_activite) == 0:
        missing.append("secteur_activite")
    
    if not profil.classifications_preferees or len(profil.classifications_preferees) == 0:
        missing.append("classifications_preferees")
    
    if not profil.mots_cles_metier or len(profil.mots_cles_metier) == 0:
        missing.append("mots_cles_metier")
    
    if not profil.budget_min or profil.budget_min <= 0:
        missing.append("budget_min")
    
    if not profil.budget_max or profil.budget_max <= 0:
        missing.append("budget_max")
    
    if not profil.caution_max or profil.caution_max <= 0:
        missing.append("caution_max")
    
    return missing