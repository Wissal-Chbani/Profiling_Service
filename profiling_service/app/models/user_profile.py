from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TailleEntreprise(str, Enum):
    TPE = "tpe"  # Très Petite Entreprise
    PME = "pme"  # Petite et Moyenne Entreprise 
    GE = "ge"    # Grande Entreprise

class RayonIntervention(str, Enum):
    LOCAL = "local"
    REGIONAL = "regional" 
    NATIONAL = "national"
    INTERNATIONAL = "international"

class DelaiPreference(str, Enum):
    COURT = "court"      # < 30 jours
    MOYEN = "moyen"      # 30-90 jours
    LONG = "long"        # > 90 jours
    TOUS = "tous"

class UserProfile(BaseModel):
    """Modèle de profil utilisateur pour le système de recommandation"""
    
    # Identifiants
    user_id: str = Field(..., description="ID unique de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    
    # Informations entreprise
    nom_entreprise: str = Field(..., description="Nom de l'entreprise")
    secteur_activite: List[str] = Field(default=[], description="Secteurs d'activité principaux")
    taille_entreprise: TailleEntreprise = Field(..., description="Taille de l'entreprise")
    
    # Préférences géographiques
    villes_preferees: List[str] = Field(default=[], description="Villes d'intervention préférées")
    rayon_intervention: RayonIntervention = Field(default=RayonIntervention.REGIONAL)
    
    # Capacités financières
    budget_min: Optional[float] = Field(None, description="Budget minimum souhaité (MAD)")
    budget_max: Optional[float] = Field(None, description="Budget maximum possible (MAD)")
    caution_max: Optional[float] = Field(None, description="Caution maximum supportable (MAD)")
    
    # Préférences temporelles
    delai_preference: DelaiPreference = Field(default=DelaiPreference.TOUS)
    
    # Mots-clés et compétences
    mots_cles_metier: List[str] = Field(default=[], description="Mots-clés métier/compétences")
    classifications_preferees: List[str] = Field(default=[], description="Classifications d'appels d'offres préférées")
    
    # Exclusions
    secteurs_exclus: List[str] = Field(default=[], description="Secteurs à éviter")
    villes_exclues: List[str] = Field(default=[], description="Villes à éviter")
    
    # Paramètres de notification
    notifications_actives: bool = Field(default=True)
    frequence_notifications: str = Field(default="quotidienne")  # quotidienne, hebdomadaire
    
    # Métadonnées
    profil_complete: bool = Field(default=False, description="Profil complété par l'utilisateur")
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    date_modification: datetime = Field(default_factory=datetime.utcnow)
    
    # Scoring et apprentissage
    historique_interactions: List[Dict[str, Any]] = Field(default=[], description="Historique des interactions pour l'apprentissage")
    score_engagement: float = Field(default=0.0, description="Score d'engagement de l'utilisateur")
    
    class Config:
        # Configuration pour MongoDB
        collection = "user_profiles"
        schema_extra = {
            "example": {
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
                "mots_cles_metier": ["développement web", "infrastructure réseau", "cybersécurité"],
                "classifications_preferees": ["services informatiques", "fournitures IT"],
                "profil_complete": True
            }
        }

class AppelOffre(BaseModel):
    """Modèle pour les appels d'offres (pour référence dans le scoring)"""
    
    numero: str
    ordre: Optional[str] = None
    reference: str
    organisme: str
    objet: str
    caution: Optional[float] = None
    budget: Optional[float] = None
    ville: str
    date_limite: datetime
    heure: Optional[str] = None
    lots: Optional[List[str]] = None
    classification: Optional[str] = None
    texte_analyse: Optional[str] = None
    secteur: str
    
    # Champs calculés pour le scoring
    score_pertinence: Optional[float] = Field(default=0.0)
    raisons_recommandation: List[str] = Field(default=[])
    
    class Config:
        collection = "appels_offres"

class InteractionUser(BaseModel):
    """Modèle pour tracker les interactions utilisateur"""
    
    user_id: str
    appel_offre_id: str
    type_interaction: str  # "vue", "clic", "favori", "candidature", "ignore"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duree_consultation: Optional[int] = None  # en secondes
    feedback: Optional[str] = None  # "pertinent", "non_pertinent"
    
    class Config:
        collection = "interactions_users"