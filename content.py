"""
content.py — tout le contenu éditorial du site, en un seul endroit.

Objectif : que le site puisse être relu et corrigé sans toucher au code des
gabarits. Chaque section correspond à une exigence du cahier des charges.

⚠️ POINT D'HONNÊTETÉ — section CERTIFICATIONS.
Le cahier des charges demandait de « mettre en avant les diplômes des auditeurs
(OSCP, OSEP, CEH, CREST, CISSP) ». Aucune de ces certifications n'est détenue
aujourd'hui. Les afficher serait un mensonge, et dans ce métier précis c'est
aussi une faute grave : un client règle une prestation en croyant acheter
l'expertise que la certification garantit.
La section est donc construite autour du statut réel de chaque certification.
Pour en passer une, il suffit de mettre son "statut" à "obtenue" et de
renseigner la date — rien d'autre à modifier.
"""

# ---------------------------------------------------------------------------
# Positionnement
# ---------------------------------------------------------------------------
ACCROCHE_TITRE = "Nous trouvons ce que les scanners ne voient pas."
ACCROCHE_TEXTE = (
    "BASTION conduit des tests d'intrusion et des audits de sécurité applicative "
    "pour les organisations qui ne peuvent pas se permettre une surprise en "
    "production. Chaque constat est reproductible, chaque preuve est fournie, "
    "et chaque correction est vérifiée."
)

# Arguments courts affichés sous le slogan, sur l'accueil et la page de contact.
ARGUMENTS = [
    ("Autorisation écrite", "Aucun test sans contrat signé"),
    ("Preuve reproductible", "Chaque faille est démontrée"),
    ("Re-test inclus", "Une faille n'est close que vérifiée"),
    ("Confidentialité", "Accord signé avant tout échange"),
]

CHIFFRES_CLEFS = [
    ("100 %", "des constats livrés avec une preuve de concept reproductible"),
    ("72 h", "délai maximum avant transmission de la synthèse exécutive"),
    ("Re-test", "systématique, inclus dans chaque mission"),
    ("OWASP, PTES, NIST", "référentiels appliqués à chaque intervention"),
]

PROMESSES = [
    {
        "titre": "Des constats exploitables, pas des scores",
        "texte": (
            "Un rapport qui liste des vulnérabilités sans dire comment les "
            "reproduire ne sert à rien. Chaque constat indique l'URL, la requête, "
            "le résultat attendu et le résultat obtenu."
        ),
    },
    {
        "titre": "Deux rapports pour deux publics",
        "texte": (
            "Votre direction lit une synthèse de quatre pages, en langage clair, "
            "avec les risques pour l'activité. Vos développeurs reçoivent la "
            "partie technique, avec les preuves et les correctifs attendus."
        ),
    },
    {
        "titre": "La correction est vérifiée",
        "texte": (
            "Une faille n'est pas fermée parce que le code a changé : elle est "
            "fermée quand notre tentative d'exploitation échoue. Le re-test est "
            "inclus, jamais facturé en supplément."
        ),
    },
]

# ---------------------------------------------------------------------------
# 1. Périmètre d'expertise & méthodologies
# ---------------------------------------------------------------------------
PERIMETRES = [
    {
        "code": "WEB",
        "titre": "Applications web",
        "resume": "Le cœur de notre activité. Injections, contrôle d'accès, "
                  "authentification, logique métier.",
        "points": [
            "Injections SQL, NoSQL, LDAP et injections de commandes",
            "Contrôle d'accès défaillant et élévation de privilèges",
            "Falsification de requête (CSRF, SSRF, XXE)",
            "Authentification, gestion de session et de jetons",
            "Logique métier : contournement de paiement, de quotas, de séquencement",
            "Exposition de données sensibles et mauvaise configuration",
        ],
    },
    {
        "code": "API",
        "titre": "API REST et GraphQL",
        "resume": "Là où les défenses sont souvent plus fines — et les erreurs plus "
                  "coûteuses, car les données sont exposées en volume.",
        "points": [
            "Autorisation objet : accès aux ressources d'un autre utilisateur",
            "Énumération et fuite d'information par les erreurs",
            "Absence de limitation de débit et abus de ressources",
            "GraphQL : introspection ouverte, requêtes profondes, alias en boucle",
            "Gestion des jetons, expiration, révocation et portée des droits",
        ],
    },
    {
        "code": "MOBILE",
        "titre": "Applications mobiles iOS et Android",
        "resume": "Analyse du binaire et de ses communications, sur appareil réel "
                  "et en environnement instrumenté.",
        "points": [
            "Stockage local non chiffré et données résiduelles",
            "Épinglage de certificat absent ou contournable",
            "Détection de root et de débogage insuffisante",
            "Secrets embarqués dans le paquet et dans les ressources",
            "Exposition via activités, fournisseurs de contenu et liens profonds",
        ],
    },
    {
        "code": "CLOUD",
        "titre": "Infrastructures cloud — AWS, Azure, GCP",
        "resume": "Revue de configuration et attaque par les chemins de privilèges, "
                  "pas seulement le balayage de conformité.",
        "points": [
            "Identités à privilèges excessifs et chemins d'escalade",
            "Rôles de confiance inter-comptes mal cloisonnés",
            "Stockage exposé publiquement, instantanés et sauvegardes accessibles",
            "Secrets en clair dans les fonctions, les machines virtuelles ou les dépôts",
            "Journalisation absente là où elle serait nécessaire",
        ],
    },
    {
        "code": "RÉSEAU",
        "titre": "Réseaux et annuaire Active Directory",
        "resume": "Du point d'entrée jusqu'au contrôle total du domaine, avec "
                  "documentation de chaque étape.",
        "points": [
            "Cartographie et segmentation depuis un poste compromis",
            "Chemins d'attaque Kerberos et abus de délégation",
            "Contrôleurs de domaine et comptes de service",
            "Protocoles d'administration exposés (SMB, RDP, WinRM)",
            "Mouvement latéral et preuve d'impact sans exfiltration de données",
        ],
    },
]

REFERENTIELS = [
    ("OWASP Top 10", "Classification de référence des risques applicatifs web. "
                     "Structure la cotation de nos constats."),
    ("OWASP ASVS", "Standard de vérification. Sert de grille de profondeur : "
                   "chaque niveau visé est annoncé dans le devis."),
    ("PTES", "Penetration Testing Execution Standard. Notre enchaînement de "
             "phases, de la prise de contact à la restitution."),
    ("NIST SP 800-115", "Guide technique des tests d'intrusion. Cadre nos "
                        "méthodes de collecte et de preuve."),
    ("OSSTMM", "Méthodologie ouverte de mesure de la sécurité. Nous en tirons "
               "la mesure d'impact plutôt que la seule présence d'une faille."),
    ("MITRE ATT&CK", "Référentiel des techniques adverses. Employé pour décrire "
                     "les scénarios d'attaque en langage commun."),
    ("CVSS v3.1 / v4.0", "Système de cotation des vulnérabilités, toujours "
                         "accompagné d'une cotation métier."),
]

PHASES = [
    ("01", "Cadrage", "Définition écrite du périmètre, des adresses visées, des "
                      "fenêtres d'intervention et des exclusions. Signature du "
                      "contrat et de l'accord de confidentialité.", "2 à 5 jours"),
    ("02", "Reconnaissance", "Cartographie de la surface exposée : sous-domaines, "
                             "services, technologies, versions, enregistrements "
                             "publics. Aucune agression à ce stade.", "1 à 3 jours"),
    ("03", "Analyse", "Recherche de vulnérabilités par revue de configuration, "
                      "fuzzing ciblé et analyse du comportement de l'application.", "3 à 10 jours"),
    ("04", "Exploitation", "Consolidation : transformation des vulnérabilités en "
                           "scénarios d'attaque réels, avec mesure de l'impact "
                           "réel sur les données et les accès.", "2 à 8 jours"),
    ("05", "Restitution", "Rapport à deux niveaux, séance de restitution orale, "
                          "et remise de la synthèse exécutive sous 72 heures.", "2 à 3 jours"),
    ("06", "Re-test", "Vérification de chaque correction. Une vulnérabilité n'est "
                      "close que lorsque notre exploitation échoue.", "1 à 3 jours"),
]

# ---------------------------------------------------------------------------
# 2. Preuve de conformité & accréditations
# ---------------------------------------------------------------------------
# statut : "obtenue" | "en_cours" | "visee"
CERTIFICATIONS = [
    {
        "sigle": "OSCP",
        "nom": "Offensive Security Certified Professional",
        "organisme": "OffSec",
        "apport": "Exploitation pratique et rédaction de rapport sous contrainte de temps.",
        "statut": "visee",
        "echeance": "2027",
    },
    {
        "sigle": "CEH",
        "nom": "Certified Ethical Hacker",
        "organisme": "EC-Council",
        "apport": "Fondamentaux de la reconnaissance et des techniques offensives.",
        "statut": "en_cours",
        "echeance": "2026",
    },
    {
        "sigle": "eWPTX",
        "nom": "Web Application Penetration Tester eXtreme",
        "organisme": "INE Security",
        "apport": "Spécialisation sur les applications web complexes.",
        "statut": "visee",
        "echeance": "2027",
    },
    {
        "sigle": "ISO 27001 LI",
        "nom": "Lead Implementer — ISO/IEC 27001",
        "organisme": "PECB",
        "apport": "Mise en place d'un système de management de la sécurité.",
        "statut": "visee",
        "echeance": "2027",
    },
    {
        "sigle": "OSEP",
        "nom": "Offensive Security Experienced Penetration Tester",
        "organisme": "OffSec",
        "apport": "Contournement de défenses et évasion d'environnement.",
        "statut": "visee",
        "echeance": "2028",
    },
    {
        "sigle": "CISSP",
        "nom": "Certified Information Systems Security Professional",
        "organisme": "ISC²",
        "apport": "Vision gouvernance, architecture et gestion du risque.",
        "statut": "visee",
        "echeance": "2028",
    },
]

MENTION_HONNETETE_TITRE = "Ce que nous ne revendiquons pas"
MENTION_HONNETETE = (
    "Aucune certification de la liste ci-dessus n'est aujourd'hui détenue par "
    "BASTION, et nous l'écrivons noir sur blanc. Chaque statut indiqué est le "
    "statut réel. Nous ne nous présentons pas non plus comme un organisme "
    "d'attestation : nous ne délivrons aucune certification de conformité, et "
    "nos rapports ne remplacent pas l'avis d'un auditeur accrédité. "
    "Dans un métier où la confiance est le seul actif, commencer par une "
    "affirmation vérifiable nous paraît plus solide que commencer par un logo."
)

CONFORMITE = [
    {
        "referentiel": "RGPD",
        "apport": "Test d'intrusion orienté données personnelles : repérage des "
                  "traitements exposés, des transferts non protégés et des accès "
                  "non cloisonnés. Utile avant une analyse d'impact.",
        "livrable": "Cartographie des données personnelles exposées et constats classés",
    },
    {
        "referentiel": "ISO/IEC 27001",
        "apport": "Vérification technique des mesures attendues par l'annexe A : "
                  "contrôle d'accès, chiffrement, journalisation, gestion des "
                  "vulnérabilités techniques.",
        "livrable": "Constats rattachés aux mesures concernées, avec éléments de preuve",
    },
    {
        "referentiel": "PCI-DSS",
        "apport": "Revue du périmètre de données de carte : flux, stockage, "
                  "tokenisation, et tests applicatifs sur les composants qui "
                  "touchent au paiement.",
        "livrable": "Constats par exigence, et identification de toute donnée de carte stockée",
    },
    {
        "referentiel": "SOC 2",
        "apport": "Test des contrôles techniques liés à la sécurité, à la "
                  "disponibilité et à la confidentialité, sur les composants "
                  "en périmètre.",
        "livrable": "Résultats de test et éléments de preuve exploitables par votre auditeur",
    },
    {
        "referentiel": "NIS 2",
        "apport": "Benchmark de vos pratiques de gestion des vulnérabilités et de "
                  "réponse aux incidents, avec priorisation des écarts.",
        "livrable": "Écarts classés et plan d'action hiérarchisé",
    },
]

MODELE_TRAVAIL = [
    {
        "titre": "Ce que nous faisons",
        "couleur": "positif",
        "points": [
            "Tests avec autorisation écrite et périmètre borné",
            "Preuves de concept reproductibles et non destructrices",
            "Rapports remis à deux niveaux, exécutif et technique",
            "Re-test de chaque correction, inclus dans la mission",
            "Notification immédiate en cas de découverte critique",
        ],
    },
    {
        "titre": "Ce que nous ne faisons pas",
        "couleur": "negatif",
        "points": [
            "Aucun test sans contrat signé et autorisation écrite du client",
            "Aucune délivrance de certificat de conformité ou d'attestation",
            "Aucune exfiltration de données au-delà du nécessaire à la preuve",
            "Aucun test sur un système qui ne vous appartient pas",
            "Aucun accès conservé après la fin de la mission",
        ],
    },
]

# ---------------------------------------------------------------------------
# 3. Livrables
# ---------------------------------------------------------------------------
LIVRABLES = [
    {
        "titre": "Synthèse exécutive",
        "public": "Direction, DSI, comité des risques",
        "format": "4 à 6 pages",
        "contenu": [
            "Niveau de risque global et évolution depuis la mission précédente",
            "Les trois scénarios d'attaque les plus dangereux, racontés en clair",
            "Impact sur l'activité : arrêt de service, fuite, perte financière, image",
            "Décisions attendues, avec effort estimé et ordre de priorité",
        ],
    },
    {
        "titre": "Rapport technique",
        "public": "Développeurs, équipes d'exploitation",
        "format": "Variable, un constat par fiche",
        "contenu": [
            "Description de la vulnérabilité et localisation exacte",
            "Étapes de reproduction numérotées, avec requêtes et réponses",
            "Impact démontré, preuve de concept à l'appui",
            "Correctif attendu, exemple de code corrigé quand c'est possible",
            "Références : OWASP, CWE, CVSS et criticité métier",
        ],
    },
    {
        "titre": "Suivi des corrections",
        "public": "Le responsable sécurité, en continu",
        "format": "Tableau de bord en ligne",
        "contenu": [
            "État de chaque vulnérabilité : ouverte, en correction, corrigée, acceptée",
            "Responsable et échéance assignés à chaque constat",
            "Demande de contre-visite en un clic",
            "Historique complet, horodaté, exportable",
        ],
    },
    {
        "titre": "Attestation de re-test",
        "public": "Auditeurs, clients, assureurs",
        "format": "Document signé",
        "contenu": [
            "Liste des vulnérabilités effectivement fermées, avec méthode de vérification",
            "Liste des vulnérabilités résiduelles et des risques acceptés",
            "Date de la vérification et limites du périmètre testé",
        ],
    },
]

# ---------------------------------------------------------------------------
# 4. Transparence éthique & légale
# ---------------------------------------------------------------------------
ETAPES_CONFIDENTIALITE = [
    ("Vous nous écrivez", "Aucun engagement, aucune donnée technique requise à ce stade."),
    ("Sous 24 h", "Nous répondons et proposons un créneau d'échange de 30 minutes."),
    ("Appel de cadrage", "Nous écoutons le besoin et proposons un périmètre adapté. "
                         "Aucune obligation."),
    ("NDA en amont", "Sur demande, l'accord de confidentialité est signé AVANT "
                     "que vous ne nous communiquiez la moindre information technique."),
    ("Devis sous 72 h", "Périmètre, méthodes, référentiels visés, durée, prix ferme."),
]

ENGAGEMENTS_ETHIQUES = [
    ("Autorisation écrite obligatoire",
     "Aucune ligne de test n'est envoyée avant réception du contrat signé et de "
     "l'autorisation du propriétaire du système. Nous refusons toute demande "
     "visant un système tiers, quel que soit le motif invoqué."),
    ("Minimisation des données",
     "Nous ne copions aucune donnée métier au-delà de ce qui prouve la faille. "
     "Quand une preuve nécessite l'accès à des données réelles, nous floutons les "
     "données personnelles dans le rapport."),
    ("Confidentialité sans limite de durée",
     "Le secret couvre l'existence de la mission, le contenu des rapports et "
     "toute information découverte. Il ne s'éteint pas à la fin du contrat."),
    ("Notification immédiate des critiques",
     "Une vulnérabilité critique exploitable est signalée au contact technique "
     "dans les heures qui suivent sa découverte, sans attendre la livraison du rapport."),
    ("Restitution du périmètre",
     "Tous les accès accordés sont révoqués et tous les éléments temporaires "
     "supprimés à la fin de la mission, sur confirmation écrite."),
]

DIVULGATION = {
    "titre": "Divulgation responsable",
    "intro": (
        "Vous pensez avoir découvert une vulnérabilité sur l'un de nos systèmes "
        "ou sur un service que nous opérons ? Merci. Nous traitons chaque message, "
        "et nous ne poursuivrons pas les chercheurs qui respectent les règles "
        "ci-dessous."
    ),
    "regles": [
        "Ne testez que nos propres systèmes, jamais ceux de nos clients.",
        "Ne consultez, ne modifiez ni ne supprimez aucune donnée.",
        "Ne perturbez pas la disponibilité du service.",
        "Ne divulguez publiquement la vulnérabilité qu'après notre accord, ou "
        "90 jours après notre premier échange.",
        "Accordez-nous un délai raisonnable de correction avant toute publication.",
    ],
    "notre_engagement": [
        "Nous accusons réception sous 3 jours ouvrés.",
        "Nous vous informons de l'avancement de la correction.",
        "Nous vous créditons dans nos remerciements, sauf si vous préférez rester anonyme.",
        "Nous ne déposons aucune plainte pour les tests conformes à ces règles.",
    ],
}

# ---------------------------------------------------------------------------
# Références du métier — la veille qui nourrit notre méthode
# ---------------------------------------------------------------------------
REFERENCES_METIER = [
    ("Astra Security", "getastra.com", "PTaaS — parcours client fluide, suivi de "
                                       "conformité en temps réel, intégration CI/CD."),
    ("Cobalt", "cobalt.io", "Pentest à la demande — réactivité et gestion "
                            "centralisée des vulnérabilités."),
    ("Bishop Fox", "bishopfox.com", "Audit offensif — outils open source et "
                                    "publications de recherche."),
    ("HackerOne", "hackerone.com", "Bug bounty — gestion de volume et preuve sociale."),
    ("OffSec", "offsec.com", "Autorité technique — formation offensive et "
                             "recherche de vulnérabilités."),
]

# ---------------------------------------------------------------------------
# Formules commerciales
# ---------------------------------------------------------------------------
FORMULES = [
    {
        "nom": "Audit express",
        "cible": "Application web unique, périmètre réduit",
        "delai": "5 jours ouvrés",
        "contenu": [
            "Périmètre jusqu'à 5 fonctionnalités majeures",
            "Analyse automatisée et vérification manuelle des points critiques",
            "Rapport à deux niveaux",
            "Une séance de restitution d'une heure",
        ],
    },
    {
        "nom": "Audit complet",
        "cible": "Application web ou API, périmètre étendu",
        "delai": "10 à 15 jours ouvrés",
        "contenu": [
            "Périmètre étendu, authentifié sur plusieurs rôles",
            "Exploitation des vulnérabilités et mesure d'impact",
            "Re-test inclus après corrections",
            "Attestation de re-test signée",
        ],
        "recommande": True,
    },
    {
        "nom": "Programme continu",
        "cible": "Plusieurs applications, amélioration continue",
        "delai": "Engagement annuel",
        "contenu": [
            "Revue trimestrielle, périmètre évolutif",
            "Portail de suivi en ligne, accessible en permanence",
            "Re-tests illimités dans l'année",
            "Canal de contact direct pour les questions urgentes",
        ],
    },
]
