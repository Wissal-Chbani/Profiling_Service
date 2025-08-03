import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import math
from difflib import SequenceMatcher

from models.user_profile import UserProfile, AppelOffre, DelaiPreference, RayonIntervention

@dataclass
class ScoreDetail:
    """Détail du score de recommandation"""
    score_total: float
    score_secteur: float
    score_geographique: float
    score_financier: float
    score_temporel: float
    score_mots_cles: float
    score_classification: float
    raisons: List[str]
    penalites: List[str]

class ScoringService:
    """Service de calcul de score de pertinence pour les appels d'offres"""
    
    def __init__(self):
        # Poids des différents critères (total = 1.0)
        self.poids = {
            'secteur': 0.25,
            'geographique': 0.20,
            'financier': 0.20,
            'temporel': 0.15,
            'mots_cles': 0.15,
            'classification': 0.05
        }
        
        # Seuils de recommandation
        self.seuil_recommandation = 0.6
        self.seuil_haute_pertinence = 0.8
        
    def calculer_score_appel_offre(self, profil: UserProfile, appel_offre: AppelOffre) -> ScoreDetail:
        """Calcule le score de pertinence d'un appel d'offre pour un profil utilisateur"""
        
        scores = {}
        raisons = []
        penalites = []
        
        # 1. Score secteur d'activité
        scores['secteur'] = self._score_secteur(profil, appel_offre, raisons, penalites)
        
        # 2. Score géographique
        scores['geographique'] = self._score_geographique(profil, appel_offre, raisons, penalites)
        
        # 3. Score financier
        scores['financier'] = self._score_financier(profil, appel_offre, raisons, penalites)
        
        # 4. Score temporel
        scores['temporel'] = self._score_temporel(profil, appel_offre, raisons, penalites)
        
        # 5. Score mots-clés métier
        scores['mots_cles'] = self._score_mots_cles(profil, appel_offre, raisons, penalites)
        
        # 6. Score classification
        scores['classification'] = self._score_classification(profil, appel_offre, raisons, penalites)
        
        # Calcul du score total pondéré
        score_total = sum(scores[critere] * self.poids[critere] for critere in scores)
        
        # Application des exclusions (score = 0 si secteur/ville exclu)
        if self._est_exclu(profil, appel_offre):
            score_total = 0.0
            penalites.append("Secteur ou ville exclu par l'utilisateur")
        
        return ScoreDetail(
            score_total=score_total,
            score_secteur=scores['secteur'],
            score_geographique=scores['geographique'],
            score_financier=scores['financier'],
            score_temporel=scores['temporel'],
            score_mots_cles=scores['mots_cles'],
            score_classification=scores['classification'],
            raisons=raisons,
            penalites=penalites
        )
    
    def _score_secteur(self, profil: UserProfile, appel_offre: AppelOffre, raisons: List[str], penalites: List[str]) -> float:
        """Score basé sur la correspondance des secteurs d'activité"""
        if not profil.secteur_activite:
            return 0.5  # Score neutre si pas de préférence
        
        # Correspondance exacte
        if appel_offre.secteur.lower() in [s.lower() for s in profil.secteur_activite]:
            raisons.append(f"Secteur {appel_offre.secteur} correspond à vos activités")
            return 1.0
        
        # Correspondance partielle (similarité de texte)
        max_similarity = 0.0
        for secteur_profil in profil.secteur_activite:
            similarity = SequenceMatcher(None, secteur_profil.lower(), appel_offre.secteur.lower()).ratio()
            max_similarity = max(max_similarity, similarity)
        
        if max_similarity > 0.7:
            raisons.append(f"Secteur {appel_offre.secteur} similaire à vos activités")
            return max_similarity
        elif max_similarity > 0.4:
            return max_similarity
        else:
            penalites.append(f"Secteur {appel_offre.secteur} éloigné de vos activités")
            return 0.1
    
    def _score_geographique(self, profil: UserProfile, appel_offre: AppelOffre, raisons: List[str], penalites: List[str]) -> float:
        """Score basé sur la localisation géographique"""
        ville_appel = appel_offre.ville.lower().strip()
        
        # Correspondance exacte avec villes préférées
        if profil.villes_preferees:
            villes_profil = [v.lower().strip() for v in profil.villes_preferees]
            if ville_appel in villes_profil:
                raisons.append(f"Situé dans votre zone préférée : {appel_offre.ville}")
                return 1.0
        
        # Score selon le rayon d'intervention
        if profil.rayon_intervention == RayonIntervention.NATIONAL:
            raisons.append("Compatible avec votre rayon d'intervention national")
            return 0.8
        elif profil.rayon_intervention == RayonIntervention.REGIONAL:
            # Logique régionale simplifiée pour le Maroc
            if self._meme_region_maroc(profil.villes_preferees, ville_appel):
                raisons.append("Dans votre région d'intervention")
                return 0.9
            else:
                return 0.4
        elif profil.rayon_intervention == RayonIntervention.LOCAL:
            # Retour score faible si pas dans les villes préférées
            penalites.append(f"Ville {appel_offre.ville} hors de votre zone locale")
            return 0.2
        
        return 0.5
    
    def _score_financier(self, profil: UserProfile, appel_offre: AppelOffre, raisons: List[str], penalites: List[str]) -> float:
        """Score basé sur les capacités financières"""
        score = 1.0
        
        # Vérification budget
        if appel_offre.budget and profil.budget_max:
            if appel_offre.budget > profil.budget_max:
                penalites.append(f"Budget {appel_offre.budget:,.0f} MAD supérieur à votre capacité")
                score *= 0.2
            elif profil.budget_min and appel_offre.budget < profil.budget_min:
                penalites.append(f"Budget {appel_offre.budget:,.0f} MAD inférieur à vos attentes")
                score *= 0.7
            else:
                raisons.append(f"Budget {appel_offre.budget:,.0f} MAD compatible")
        
        # Vérification caution
        if appel_offre.caution and profil.caution_max:
            if appel_offre.caution > profil.caution_max:
                penalites.append(f"Caution {appel_offre.caution:,.0f} MAD trop élevée")
                score *= 0.1  # Pénalité forte car c'est bloquant
            else:
                raisons.append(f"Caution {appel_offre.caution:,.0f} MAD acceptable")
        
        return max(score, 0.1)
    
    def _score_temporel(self, profil: UserProfile, appel_offre: AppelOffre, raisons: List[str], penalites: List[str]) -> float:
        """Score basé sur les délais"""
        jours_restants = (appel_offre.date_limite - datetime.now()).days
        
        # Appel d'offre expiré
        if jours_restants < 0:
            penalites.append("Appel d'offre expiré")
            return 0.0
        
        # Score selon préférence délai
        if profil.delai_preference == DelaiPreference.TOUS:
            return 0.8
        elif profil.delai_preference == DelaiPreference.COURT:
            if jours_restants <= 30:
                raisons.append(f"Délai court ({jours_restants} jours) selon vos préférences")
                return 1.0
            else:
                return max(0.3, 1.0 - (jours_restants - 30) / 100)
        elif profil.delai_preference == DelaiPreference.MOYEN:
            if 30 <= jours_restants <= 90:
                raisons.append(f"Délai moyen ({jours_restants} jours) selon vos préférences")
                return 1.0
            else:
                return 0.6
        elif profil.delai_preference == DelaiPreference.LONG:
            if jours_restants > 90:
                raisons.append(f"Délai long ({jours_restants} jours) selon vos préférences")
                return 1.0
            else:
                return 0.7
        
        return 0.5
    
    def _score_mots_cles(self, profil: UserProfile, appel_offre: AppelOffre, raisons: List[str], penalites: List[str]) -> float:
        """Score basé sur les mots-clés métier"""
        if not profil.mots_cles_metier:
            return 0.5
        
        texte_analyse = f"{appel_offre.objet} {appel_offre.texte_analyse or ''}".lower()
        mots_cles_trouves = []
        
        for mot_cle in profil.mots_cles_metier:
            if mot_cle.lower() in texte_analyse:
                mots_cles_trouves.append(mot_cle)
        
        if mots_cles_trouves:
            raisons.append(f"Mots-clés correspondants: {', '.join(mots_cles_trouves)}")
            return min(1.0, len(mots_cles_trouves) / len(profil.mots_cles_metier) * 1.5)
        
        return 0.2
    
    def _score_classification(self, profil: UserProfile, appel_offre: AppelOffre, raisons: List[str], penalites: List[str]) -> float:
        """Score basé sur la classification des appels d'offres"""
        if not profil.classifications_preferees or not appel_offre.classification:
            return 0.5
        
        classification_lower = appel_offre.classification.lower()
        for classif_pref in profil.classifications_preferees:
            if classif_pref.lower() in classification_lower or classification_lower in classif_pref.lower():
                raisons.append(f"Classification {appel_offre.classification} correspond à vos préférences")
                return 1.0
        
        return 0.3
    
    def _est_exclu(self, profil: UserProfile, appel_offre: AppelOffre) -> bool:
        """Vérifie si l'appel d'offre est dans les exclusions"""
        # Secteurs exclus
        if profil.secteurs_exclus:
            for secteur_exclu in profil.secteurs_exclus:
                if secteur_exclu.lower() in appel_offre.secteur.lower():
                    return True
        
        # Villes exclues
        if profil.villes_exclues:
            for ville_exclue in profil.villes_exclues:
                if ville_exclue.lower() in appel_offre.ville.lower():
                    return True
        
        return False
    
    def _meme_region_maroc(self, villes_preferees: List[str], ville_appel: str) -> bool:
        """Logique simplifiée pour déterminer si deux villes sont dans la même région au Maroc"""
        # Mapping régional simplifié
        regions_maroc = {
            'grand_casablanca': ['casablanca', 'mohammedia', 'settat', 'berrechid'],
            'rabat_sale': ['rabat', 'sale', 'temara', 'skhirat'],
            'fes_meknes': ['fes', 'meknes', 'ifrane', 'khenifra'],
            'marrakech': ['marrakech', 'essaouira', 'safi', 'kelaa'],
            'tanger_tetouan': ['tanger', 'tetouan', 'larache', 'chefchaouen'],
            'oriental': ['oujda', 'nador', 'berkane', 'taourirt'],
            'souss_massa': ['agadir', 'tiznit', 'taroudant', 'ouarzazate']
        }
        
        if not villes_preferees:
            return False
        
        ville_appel_lower = ville_appel.lower()
        villes_pref_lower = [v.lower() for v in villes_preferees]
        
        for region, villes in regions_maroc.items():
            if ville_appel_lower in villes:
                # Vérifier si une ville préférée est dans la même région
                for ville_pref in villes_pref_lower:
                    if ville_pref in villes:
                        return True
        
        return False
    
    def recommander_appels_offres(self, profil: UserProfile, appels_offres: List[AppelOffre], 
                                 limite: int = 20) -> List[Tuple[AppelOffre, ScoreDetail]]:
        """Recommande les meilleurs appels d'offres pour un profil donné"""
        resultats = []
        
        for appel_offre in appels_offres:
            score_detail = self.calculer_score_appel_offre(profil, appel_offre)
            
            # Ne recommander que si score au-dessus du seuil
            if score_detail.score_total >= self.seuil_recommandation:
                resultats.append((appel_offre, score_detail))
        
        # Trier par score décroissant
        resultats.sort(key=lambda x: x[1].score_total, reverse=True)
        
        return resultats[:limite]
    
    def categoriser_recommandation(self, score: float) -> str:
        """Catégorise le niveau de recommandation"""
        if score >= self.seuil_haute_pertinence:
            return "Très pertinent"
        elif score >= self.seuil_recommandation:
            return "Pertinent"
        else:
            return "Peu pertinent"