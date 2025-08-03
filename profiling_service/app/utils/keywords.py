import re
from typing import List, Dict, Set
from collections import defaultdict

class KeywordExtractor:
    """Classe pour extraire et suggérer des mots-clés métier"""
    
    def __init__(self):
        # Base de données des mots-clés par secteur d'activité au Maroc
        self.keywords_by_sector = {
            "informatique": [
                "développement web", "application mobile", "base de données", "cybersécurité",
                "infrastructure réseau", "cloud computing", "intelligence artificielle", "blockchain",
                "ERP", "CRM", "système d'information", "maintenance informatique",
                "formation informatique", "audit informatique", "hébergement web",
                "logiciel de gestion", "e-commerce", "digitalisation", "transformation digitale"
            ],
            "bâtiment": [
                "construction", "rénovation", "génie civil", "architecture", "maçonnerie",
                "plomberie", "électricité", "climatisation", "isolation thermique",
                "étanchéité", "carrelage", "peinture", "menuiserie", "charpente",
                "terrassement", "assainissement", "voirie", "béton armé", "infrastructure"
            ],
            "transport": [
                "transport routier", "logistique", "livraison", "déménagement",
                "transport de marchandises", "transport de personnes", "affrètement",
                "entreposage", "supply chain", "douane", "transit", "fret",
                "transport international", "messagerie", "distribution"
            ],
            "santé": [
                "équipement médical", "fournitures médicales", "imagerie médicale",
                "laboratoire", "pharmacie", "dispositifs médicaux", "stérilisation",
                "ambulance", "télémédecine", "dossier médical électronique",
                "maintenance médicale", "formation médicale", "hygiène hospitalière"
            ],
            "éducation": [
                "formation professionnelle", "e-learning", "équipement scolaire",
                "mobilier scolaire", "fournitures scolaires", "laboratoire pédagogique",
                "bibliothèque", "cantine scolaire", "transport scolaire",
                "cours particuliers", "certification", "formation continue"
            ],
            "agriculture": [
                "machinisme agricole", "irrigation", "semences", "engrais", "pesticides",
                "élevage", "arboriculture", "maraîchage", "céréaliculture",
                "transformation agroalimentaire", "certification bio", "conseil agricole",
                "vétérinaire", "équipement agricole"
            ],
            "énergie": [
                "énergie solaire", "énergie éolienne", "électricité", "gaz naturel",
                "pétrole", "efficacité énergétique", "audit énergétique",
                "installation électrique", "maintenance énergétique", "smart grid",
                "biomasse", "géothermie", "hydrogène vert"
            ],
            "tourisme": [
                "hôtellerie", "restauration", "agence de voyage", "guide touristique",
                "transport touristique", "animation", "événementiel", "traiteur",
                "réceptif", "écotourisme", "tourisme culturel", "hébergement"
            ],
            "industrie": [
                "production industrielle", "maintenance industrielle", "contrôle qualité",
                "automation", "robotique", "mécanique de précision", "usinage",
                "soudure", "assemblage", "packaging", "logistique industrielle",
                "sécurité industrielle", "environnement industriel"
            ],
            "finance": [
                "comptabilité", "audit financier", "conseil fiscal", "banque",
                "assurance", "crédit", "investissement", "gestion de patrimoine",
                "expertise comptable", "commissariat aux comptes", "financement",
                "microfinance", "trésorerie"
            ],
            "communication": [
                "marketing digital", "publicité", "communication digitale", "réseaux sociaux",
                "création graphique", "impression", "événementiel", "relations presse",
                "stratégie de communication", "brand content", "web marketing",
                "référencement SEO", "community management"
            ],
            "environnement": [
                "traitement des eaux", "gestion des déchets", "recyclage",
                "dépollution", "étude d'impact", "énergies renouvelables",
                "développement durable", "ISO 14001", "économie circulaire",
                "biodiversité", "changement climatique"
            ],
            "sécurité": [
                "sécurité privée", "surveillance", "gardiennage", "système d'alarme",
                "vidéosurveillance", "contrôle d'accès", "sécurité incendie",
                "sécurité informatique", "audit sécurité", "formation sécurité",
                "transport de fonds", "protection rapprochée"
            ],
            "textile": [
                "confection", "broderie", "impression textile", "maroquinerie",
                "chaussure", "mode", "design textile", "teinture", "tissage",
                "tricotage", "accessoires", "prêt-à-porter", "export textile"
            ],
            "conseil": [
                "conseil en management", "formation professionnelle", "audit organisationnel",
                "accompagnement", "coaching", "stratégie d'entreprise", "ressources humaines",
                "optimisation des processus", "conduite du changement", "certification",
                "normalisation", "évaluation"
            ]
        }
        
        # Synonymes et variantes
        self.synonymes = {
            "développement web": ["dev web", "création web", "site web", "application web"],
            "intelligence artificielle": ["IA", "AI", "machine learning", "deep learning"],
            "cybersécurité": ["sécurité informatique", "sécurité IT", "protection données"],
            "infrastructure réseau": ["réseau informatique", "administration réseau"],
            "génie civil": ["travaux publics", "BTP", "construction civile"],
            "transport routier": ["transport terrestre", "routage"],
            "énergie solaire": ["photovoltaïque", "solaire PV", "panneaux solaires"],
            "marketing digital": ["marketing numérique", "webmarketing", "digital marketing"]
        }
        
        # Mots-clés génériques utiles
        self.mots_cles_generiques = [
            "fourniture", "installation", "maintenance", "formation", "conseil",
            "audit", "certification", "contrôle", "gestion", "développement",
            "création", "conception", "réalisation", "livraison", "support",
            "assistance", "expertise", "étude", "analyse", "optimisation"
        ]
    
    def get_keywords_by_sector(self, secteur: str) -> List[str]:
        """Retourne les mots-clés suggérés pour un secteur donné"""
        secteur_lower = secteur.lower().strip()
        
        # Recherche exacte
        if secteur_lower in self.keywords_by_sector:
            return self.keywords_by_sector[secteur_lower]
        
        # Recherche partielle
        for sector_key, keywords in self.keywords_by_sector.items():
            if secteur_lower in sector_key or sector_key in secteur_lower:
                return keywords
        
        # Recherche dans les mots-clés eux-mêmes
        mots_cles_correspondants = []
        for keywords in self.keywords_by_sector.values():
            for keyword in keywords:
                if secteur_lower in keyword.lower():
                    mots_cles_correspondants.append(keyword)
        
        if mots_cles_correspondants:
            return list(set(mots_cles_correspondants))
        
        # Retourner des mots-clés génériques si aucune correspondance
        return self.mots_cles_generiques[:10]
    
    def extract_keywords_from_text(self, texte: str, min_length: int = 3) -> List[str]:
        """Extrait des mots-clés potentiels d'un texte"""
        if not texte:
            return []
        
        # Nettoyer le texte
        texte_clean = self._clean_text(texte)
        
        # Extraire les mots significatifs
        mots = re.findall(r'\b[a-zA-ZàâäéèêëïîôöùûüÿñçÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÑÇ]{' + str(min_length) + r',}\b', texte_clean)
        
        # Filtrer les mots non significatifs
        mots_significatifs = []
        mots_vides = self._get_stop_words()
        
        for mot in mots:
            if mot.lower() not in mots_vides and len(mot) >= min_length:
                mots_significatifs.append(mot.lower())
        
        # Compter les occurrences et garder les plus fréquents
        compteur = defaultdict(int)
        for mot in mots_significatifs:
            compteur[mot] += 1
        
        # Trier par fréquence et garder les 20 premiers
        mots_tries = sorted(compteur.items(), key=lambda x: x[1], reverse=True)
        return [mot for mot, freq in mots_tries[:20]]
    
    def match_keywords_with_sectors(self, mots_cles: List[str]) -> Dict[str, float]:
        """Calcule la correspondance entre des mots-clés et les secteurs"""
        scores_secteurs = defaultdict(float)
        
        for mot_cle in mots_cles:
            mot_cle_lower = mot_cle.lower()
            
            for secteur, keywords in self.keywords_by_sector.items():
                for keyword in keywords:
                    # Correspondance exacte
                    if mot_cle_lower == keyword.lower():
                        scores_secteurs[secteur] += 1.0
                    # Correspondance partielle
                    elif mot_cle_lower in keyword.lower() or keyword.lower() in mot_cle_lower:
                        scores_secteurs[secteur] += 0.5
                
                # Vérifier les synonymes
                for terme_principal, synonymes in self.synonymes.items():
                    if terme_principal in keywords:
                        for synonyme in synonymes:
                            if mot_cle_lower == synonyme.lower():
                                scores_secteurs[secteur] += 0.8
        
        # Normaliser les scores
        if scores_secteurs:
            max_score = max(scores_secteurs.values())
            scores_secteurs = {k: v/max_score for k, v in scores_secteurs.items()}
        
        return dict(scores_secteurs)
    
    def suggest_related_keywords(self, mot_cle: str, limite: int = 10) -> List[str]:
        """Suggère des mots-clés liés à un mot-clé donné"""
        suggestions = set()
        mot_cle_lower = mot_cle.lower()
        
        # Rechercher dans toutes les listes de mots-clés
        for keywords in self.keywords_by_sector.values():
            for keyword in keywords:
                # Mots-clés contenant le terme recherché
                if mot_cle_lower in keyword.lower() and keyword.lower() != mot_cle_lower:
                    suggestions.add(keyword)
                
                # Mots-clés partageant des mots communs
                mots_recherche = set(mot_cle_lower.split())
                mots_keyword = set(keyword.lower().split())
                if mots_recherche.intersection(mots_keyword) and len(mots_keyword) > 1:
                    suggestions.add(keyword)
        
        # Ajouter les synonymes
        for terme_principal, synonymes in self.synonymes.items():
            if mot_cle_lower == terme_principal.lower():
                suggestions.update(synonymes)
            elif mot_cle_lower in [s.lower() for s in synonymes]:
                suggestions.add(terme_principal)
                suggestions.update([s for s in synonymes if s.lower() != mot_cle_lower])
        
        return list(suggestions)[:limite]
    
    def _clean_text(self, texte: str) -> str:
        """Nettoie un texte pour l'extraction de mots-clés"""
        # Supprimer les caractères spéciaux sauf espaces et tirets
        texte = re.sub(r'[^\w\s\-àâäéèêëïîôöùûüÿñçÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÑÇ]', ' ', texte)
        # Supprimer les espaces multiples
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()
    
    def _get_stop_words(self) -> Set[str]:
        """Retourne la liste des mots vides en français et arabe translittéré"""
        return {
            # Français
            "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "mais",
            "donc", "or", "ni", "car", "que", "qui", "quoi", "dont", "où", "ce",
            "se", "sa", "son", "ses", "leur", "leurs", "nous", "vous", "ils", "elles",
            "je", "tu", "il", "elle", "on", "dans", "sur", "avec", "par", "pour",
            "sans", "sous", "vers", "chez", "entre", "jusque", "depuis", "pendant",
            "avant", "après", "très", "plus", "moins", "aussi", "tout", "tous",
            "toute", "toutes", "autre", "autres", "même", "mêmes", "tel", "telle",
            "comme", "comment", "quand", "pourquoi", "combien", "est", "sont", "être",
            "avoir", "faire", "dire", "aller", "voir", "savoir", "pouvoir", "vouloir",
            "devoir", "falloir", "venir", "prendre", "donner", "mettre", "partir",
            "sortir", "passer", "rester", "tenir", "porter", "suivre", "vivre", "mourir",
            
            # Mots techniques courants
            "selon", "concernant", "relative", "relatif", "conformément", "cadre",
            "objet", "référence", "numéro", "date", "délai", "montant", "prix",
            "coût", "budget", "offre", "demande", "appel", "marché", "public",
            "cahier", "charges", "technique", "administratif", "financier",
            
            # Arabe translittéré courant
            "al", "el", "wa", "fi", "min", "ila", "an", "ma", "la", "li", "bi"
        }
    
    def get_all_sectors(self) -> List[str]:
        """Retourne la liste de tous les secteurs disponibles"""
        return list(self.keywords_by_sector.keys())
    
    def get_sector_keywords_count(self) -> Dict[str, int]:
        """Retourne le nombre de mots-clés par secteur"""
        return {secteur: len(keywords) for secteur, keywords in self.keywords_by_sector.items()}