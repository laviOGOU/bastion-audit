"""
seed.py — jeu de données de démonstration.

Remplit la base avec des clients, des missions et des vulnérabilités FICTIFS,
afin que le portail de suivi et l'espace d'administration soient lisibles dès
le premier lancement.

Aucune donnée réelle n'est créée ici. Les noms d'organisations sont inventés.

Usage :
    .venv/Scripts/python.exe seed.py           # ajoute si la base est vide
    .venv/Scripts/python.exe seed.py --force   # efface et recrée
"""
import sys
from datetime import datetime, timedelta

# Ce script est un outil de developpement : il manipule le fichier
# SQLite avec du SQL brut, donc il vise ce moteur explicitement.
import db_sqlite as db

MAINTENANT = datetime.now()


def j(delta: int) -> str:
    return (MAINTENANT + timedelta(days=delta)).strftime("%Y-%m-%d %H:%M:%S")


CLIENTS = [
    ("Groupe Trans-Commerce", "Distribution et commerce en ligne",
     "Direction des systèmes d'information"),
    ("Banque Atlantique du Sud", "Services financiers",
     "Responsable sécurité des systèmes d'information"),
    ("Clinique Sainte-Croix", "Santé", "Direction administrative"),
]

MISSIONS = [
    (1, "AUD-2026-001", "Web — portail client et tunnel de commande",
     "OWASP Top 10, ASVS niveau 2", -42, -8, "livre"),
    (2, "AUD-2026-002", "API REST et application mobile",
     "OWASP API Top 10, PTES", -26, 4, "en_cours"),
    (3, "AUD-2026-003", "Infrastructure cloud et messagerie",
     "NIST SP 800-115, ISO/IEC 27001 annexe A", -11, 18, "en_cours"),
]

# (mission_id, titre, sévérité, cvss, cwe, categorie, description, impact,
#  preuve, remediation, responsable, échéance_jours, statut, correction_jours)
VULNERABILITES = [
    (1, "Injection SQL dans le paramètre de recherche du catalogue", "critique", 9.1,
     "CWE-89", "A03:2021 — Injection",
     "Le paramètre « recherche » de l'endpoint public /catalogue est concaténé "
     "directement dans la requête SQL. Un guillemet non échappé permet de "
     "modifier la clause WHERE et d'extraire des données d'autres tables.",
     "Extraction complète de la base utilisateurs par un visiteur non "
     "authentifié, sans trace dans les journaux applicatifs.",
     "GET /catalogue?recherche=x%27%20UNION%20SELECT%20null,email,hash_mdp"
     "%20FROM%20utilisateurs--%20\n"
     "→ 412 lignes supplémentaires renvoyées, dont des adresses "
     "électroniques et des empreintes de mots de passe.",
     "Requêtes paramétrées sur tous les points d'entrée du catalogue. "
     "Validation en liste blanche des colonnes triables. Restriction des "
     "droits du compte de base au strict nécessaire.",
     "Équipe Backend", -15, "corrigee", -30),

    (1, "Contrôle d'accès horizontal sur les factures", "critique", 8.6,
     "CWE-639", "A01:2021 — Contrôle d'accès défaillant",
     "L'endpoint /api/v1/factures/{id} ne vérifie pas que la facture appartient "
     "à l'utilisateur authentifié. Un identifiant séquentiel suffit à lire les "
     "factures d'autres clients.",
     "Divulgation de données commerciales et personnelles entre clients. "
     "Atteinte directe au RGPD.",
     "GET /api/v1/factures/10441  (jeton du compte A)\n"
     "→ 200 OK, facture du compte B : montant, coordonnées, historique d'achat.",
     "Contrôle de propriété côté serveur sur chaque ressource (jamais côté "
     "client). Remplacement des identifiants séquentiels par des UUID. "
     "Journalisation des accès refusés.",
     "Équipe Backend", -22, "corrigee", -35),

    (2, "Absence de limitation de débit sur l'authentification", "eleve", 7.5,
     "CWE-307", "A07:2021 — Défaillance d'identification",
     "L'endpoint d'authentification accepte un nombre illimité de tentatives "
     "sans ralentissement, verrouillage ni défi.",
     "Attaque par force brute ou par bourrage d'identifiants à grande échelle. "
     "Compromission de comptes à mot de passe faible.",
     "1 000 tentatives en 4 minutes depuis une même adresse IP\n"
     "→ aucune limitation, aucun verrouillage, aucun blocage.",
     "Limitation de débit par IP et par compte. Ralentissement progressif. "
     "Verrouillage temporaire après échecs répétés. Authentification à deux "
     "facteurs pour les comptes sensibles.",
     "Équipe Plateforme", 6, "en_correction", None),

    (2, "Jeton de session non invalidé à la déconnexion", "eleve", 7.1,
     "CWE-613", "A07:2021 — Défaillance d'identification",
     "Le jeton JWT reste valide après la déconnexion : il n'existe ni liste de "
     "révocation, ni durée de vie courte, ni contrôle de version.",
     "Un jeton intercepté reste exploitable jusqu'à son expiration, même après "
     "que l'utilisateur a fermé sa session.",
     "Déconnexion, puis réutilisation du même jeton\n"
     "→ 200 OK sur /api/v1/profil, session toujours active.",
     "Durée de vie courte des jetons d'accès, jeton de rafraîchissement "
     "révocable, et invalidation côté serveur à la déconnexion.",
     "Équipe Backend", 6, "en_correction", None),

    (2, "Autorisation objet absente sur l'API mobile", "eleve", 8.1,
     "CWE-284", "API01:2023 — Autorisation au niveau objet",
     "Les endpoints /api/v2/dossiers/{id} valident le rôle mais pas la "
     "propriété de l'objet. Un compte de niveau standard atteint des dossiers "
     "d'un autre service.",
     "Fuite de dossiers entre services. Rupture du cloisonnement prévu par "
     "l'organisation.",
     "GET /api/v2/dossiers/8830 (compte standard, service A)\n"
     "→ 200 OK, dossier du service B, pièces jointes incluses.",
     "Contrôle de propriété sur chaque objet, dérivé du jeton et non d'un "
     "paramètre. Tests automatisés d'autorisation dans la chaîne d'intégration.",
     "Équipe Mobile", 9, "ouverte", None),

    (1, "En-têtes de sécurité et politique de contenu absents", "moyen", 5.4,
     "CWE-693", "A05:2021 — Mauvaise configuration",
     "Aucun en-tête Content-Security-Policy, X-Content-Type-Options ou "
     "X-Frame-Options. Le site est encadrable dans une iframe tierce.",
     "Facilitation d'attaques par détournement de clic et contournement des "
     "protections navigateur.",
     "Réponse HTTP du portail\n"
     "→ aucun en-tête de sécurité présent dans la réponse.",
     "Politique de contenu restrictive, X-Frame-Options DENY, "
     "X-Content-Type-Options nosniff, Referrer-Policy, HSTS.",
     "Équipe Frontend", -3, "corrigee", -12),

    (3, "Espace de stockage cloud exposé publiquement", "eleve", 8.8,
     "CWE-732", "A05:2021 — Mauvaise configuration",
     "Un compartiment de stockage d'objets autorise la lecture anonyme. Il "
     "contient des sauvegardes de base de données et des exports de facturation.",
     "Téléchargement de l'intégralité des sauvegardes par toute personne "
     "connaissant l'adresse du compartiment.",
     "GET https://stockage.exemple-clinique.ci/sauvegardes/2026-08/\n"
     "→ 200 OK, 14 fichiers .sql et .csv accessibles sans authentification.",
     "Retrait de l'accès public. Chiffrement côté serveur. Journalisation des "
     "accès. Rotation des sauvegardes exposées et revue des identifiants "
     "qu'elles contenaient.",
     "Équipe Infrastructure", 2, "en_correction", None),

    (3, "Compte de service disposant de privilèges de domaine", "critique", 9.4,
     "CWE-250", "A01:2021 — Contrôle d'accès défaillant",
     "Un compte de service utilisé par un logiciel métier appartient au groupe "
     "des administrateurs de domaine. Son mot de passe n'a pas été changé depuis "
     "plus de trois ans et figure en clair dans un script planifié.",
     "Élévation de privilèges jusqu'au contrôle total de l'annuaire, depuis le "
     "serveur applicatif métier.",
     "Extraction du mot de passe depuis la tâche planifiée, puis ouverture de "
     "session sur un contrôleur de domaine\n"
     "→ accès administrateur confirmé, sans alerte.",
     "Retrait du compte des groupes privilégiés. Mot de passe dédié, long, "
     "renouvelé. Suppression des secrets en clair. Comptes de service gérés par "
     "l'annuaire. Surveillance des ajouts aux groupes sensibles.",
     "Équipe Infrastructure", 2, "ouverte", None),

    (3, "Protocole d'administration exposé sur le réseau interne", "eleve", 7.8,
     "CWE-306", "A05:2021 — Mauvaise configuration",
     "Le protocole de bureau à distance est accessible depuis l'ensemble du "
     "réseau interne, y compris le réseau invités, avec authentification par mot "
     "de passe seul.",
     "Point d'appui pour un mouvement latéral après compromission d'un poste "
     "invité.",
     "Connexion au port d'administration depuis le réseau invités\n"
     "→ invitation d'authentification affichée, aucun filtrage réseau.",
     "Segmentation réseau, accès restreint aux postes d'administration, "
     "authentification renforcée et journalisation des connexions.",
     "Équipe Réseau", 4, "ouverte", None),

    (2, "Messages d'erreur révélant la pile technique", "moyen", 5.3,
     "CWE-209", "A05:2021 — Mauvaise configuration",
     "Les erreurs applicatives renvoient la trace complète, incluant les "
     "chemins de fichiers, les versions de bibliothèques et les requêtes SQL.",
     "Facilitation de la reconnaissance : un attaquant cartographie la pile "
     "technique et cible les versions vulnérables connues.",
     "GET /api/v2/rapports/abc\n"
     "→ trace complète : chemins, version du cadre applicatif, requête SQL.",
     "Gestion d'erreurs centralisée renvoyant un identifiant de corrélation. "
     "Journalisation détaillée côté serveur uniquement. Désactivation du mode "
     "débogage en production.",
     "Équipe Backend", 12, "ouverte", None),

    (1, "Bannière de version obsolète (composant frontal)", "moyen", 5.9,
     "CWE-1104", "A06:2021 — Composants vulnérables",
     "La bibliothèque d'interface utilisée en production est en retard de "
     "quatre versions mineures et cumule trois vulnérabilités connues.",
     "Exploitation de vulnérabilités publiques documentées, y compris des "
     "attaques par script intersite stockées.",
     "En-tête de réponse et empreinte du fichier livré\n"
     "→ version identifiée comme vulnérable dans la base publique.",
     "Mise à jour de la bibliothèque, mise en place d'une surveillance des "
     "dépendances et d'un contrôle automatique à chaque livraison.",
     "Équipe Frontend", 14, "ouverte", None),

    (3, "Journalisation insuffisante des accès administratifs", "moyen", 4.8,
     "CWE-778", "A09:2021 — Défaillance de journalisation",
     "Les connexions aux interfaces d'administration ne sont pas journalisées, "
     "et les journaux existants ne sont pas protégés en écriture.",
     "Impossibilité de détecter ou de reconstituer une compromission. "
     "Absence d'éléments de preuve en cas d'incident.",
     "Connexion réussie à l'interface d'administration depuis une adresse "
     "inconnue\n→ aucune entrée dans les journaux.",
     "Journalisation de tous les accès et actions d'administration, "
     "horodatage, conservation centralisée et protection contre l'altération.",
     "Équipe Infrastructure", 16, "ouverte", None),

    (1, "Divulgation d'information par l'en-tête de réponse serveur", "faible", 3.1,
     "CWE-200", "A05:2021 — Mauvaise configuration",
     "Les en-têtes de réponse exposent le serveur applicatif, sa version exacte "
     "et le système d'exploitation sous-jacent.",
     "Aide à la reconnaissance. Impact limité sans vulnérabilité associée.",
     "Réponse HTTP\n→ en-têtes révélant le serveur, la version et le système.",
     "Masquage des en-têtes de version au niveau du serveur frontal.",
     "Équipe Frontend", 20, "acceptee", None),

    (2, "Politique de mot de passe insuffisante", "faible", 3.7,
     "CWE-521", "A07:2021 — Défaillance d'identification",
     "La politique accepte six caractères sans contrôle contre les mots de "
     "passe les plus répandus.",
     "Facilitation des attaques par dictionnaire sur des comptes réels.",
     "Création d'un compte avec le mot de passe « 123456 »\n→ accepté.",
     "Longueur minimale de douze caractères, contrôle contre une liste de mots "
     "de passe compromis, et recommandation de phrases de passe.",
     "Équipe Plateforme", 18, "ouverte", None),
]

RETESTES = [
    (1, -30, -27, "Exploitation rejouée après correction : échec. Les requêtes "
                  "paramétrées sont effectives et le compte de base n'a plus "
                  "accès qu'aux tables nécessaires."),
    (2, -35, -31, "Contrôle de propriété vérifié sur six identifiants distincts "
                  "appartenant à d'autres comptes : tous refusés avec un code 404, "
                  "sans divulgation d'information."),
]


def effacer(conn) -> None:
    for table in ("retests", "vulnerabilites", "missions", "clients", "demandes",
                  "journal"):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN "
                 "('retests','vulnerabilites','missions','clients','demandes','journal')")


def main() -> int:
    force = "--force" in sys.argv
    db.initialiser()

    with db.connect() as conn:
        existant = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        if existant and not force:
            print(f"  La base contient déjà {existant} client(s).")
            print("  Relancez avec --force pour tout effacer et recréer.")
            return 0
        if force:
            effacer(conn)
            print("  Données existantes effacées.")

    ids_clients = []
    for nom, secteur, contact in CLIENTS:
        ids_clients.append(db.creer_client(nom, secteur, contact))
    print(f"  {len(ids_clients)} clients créés.")

    ids_missions = []
    for indice_client, reference, perimetre, referentiel, debut, fin, statut in MISSIONS:
        ids_missions.append(db.creer_mission(
            ids_clients[indice_client - 1], reference, perimetre, referentiel,
            j(debut), j(fin), statut))
    print(f"  {len(ids_missions)} missions créées.")

    for (mission_id, titre, severite, cvss, cwe, categorie, description, impact,
         preuve, remediation, responsable, echeance, statut, correction) in VULNERABILITES:
        with db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO vulnerabilites (mission_id, titre, severite, cvss, cwe, "
                "categorie, description, impact, preuve, remediation, responsable, "
                "statut, date_constat, date_echeance, date_correction) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ids_missions[mission_id - 1], titre, severite, cvss, cwe, categorie,
                 description, impact, preuve, remediation, responsable, statut,
                 j(-35), j(echeance), j(correction) if correction else None),
            )
            identifiant = cur.lastrowid
            if statut == "corrigee":
                conn.execute(
                    "INSERT INTO retests (vuln_id, demande_le, realise_le, resultat) "
                    "VALUES (?, ?, ?, ?)",
                    (identifiant, j(-32), j(-29),
                     "Exploitation rejouée : échec, correctif confirmé."),
                )
    print(f"  {len(VULNERABILITES)} vulnérabilités créées.")

    with db.connect() as conn:
        for vuln_id, demande, realise, resultat in RETESTES:
            conn.execute("DELETE FROM retests WHERE vuln_id = ?", (vuln_id,))
            conn.execute(
                "INSERT INTO retests (vuln_id, demande_le, realise_le, resultat) "
                "VALUES (?, ?, ?, ?)", (vuln_id, j(demande), j(realise), resultat))

        # Une contre-visite en attente, pour que la file ne soit pas vide.
        conn.execute(
            "INSERT INTO retests (vuln_id, demande_le) VALUES (?, ?)",
            (4, j(-2)),
        )

    # Deux demandes de devis, pour que l'espace d'administration soit lisible.
    db.creer_demande(
        "Coopérative Agricole du Nord", "Awa Traoré", "a.traore@exemple-coop.ci",
        "+225 07 00 00 00 01", "Applications web", "6 à 20 personnes",
        "Nous préparons la mise en ligne d'un portail de commande pour nos "
        "adhérents et souhaitons un test avant l'ouverture au public. "
        "Échéance souhaitée : fin du trimestre.", True)
    db.creer_demande(
        "Assurances Lagune", "Konan Yao", "k.yao@exemple-assur.ci",
        "+225 07 00 00 00 02", "API REST et GraphQL", "21 à 100 personnes",
        "Notre API partenaire doit être auditée dans le cadre d'une exigence "
        "contractuelle. Nous avons besoin d'un rapport utilisable par notre "
        "auditeur externe.", False)

    db.journaliser("jeu_de_donnees", "seed.py — données de démonstration")
    stats = db.statistiques()
    print(f"  {stats['demandes_total']} demandes créées.")
    print()
    print(f"  Total : {stats['vulns_total']} vulnérabilités, "
          f"{stats['vulns_corrigees']} corrigées "
          f"({stats['taux_correction']} %), "
          f"{stats['retests_en_attente']} contre-visite(s) en attente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
