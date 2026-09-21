"""
db.py — sélection du moteur de base de données et point d'entrée unique.

Deux moteurs, une seule interface :

    db_sqlite.py     fichier local, aucune configuration — développement
    db_supabase.py   PostgreSQL hébergé — production

Le choix se fait au démarrage, sur la seule présence des variables
SUPABASE_URL et SUPABASE_KEY :

    les deux définies  →  Supabase
    sinon              →  SQLite

Aucun gabarit, aucune route, aucun script n'a besoin de savoir lequel est actif :
tous importent `db` et appellent les mêmes fonctions. Ce qui doit changer en
production se limite donc à des variables d'environnement, jamais au code.

Les constantes de libellé (SEVERITES, STATUTS_VULN…) sont également exposées ici,
car les gabarits s'en servent.
"""
import os

import config

if config.MOTEUR_SUPABASE:
    from db_supabase import (          # noqa: F401
        SEVERITES, SEVERITES_LIBELLE, STATUTS_VULN, STATUTS_VULN_LIBELLE,
        STATUTS_DEMANDE, STATUTS_DEMANDE_LIBELLE, ErreurBase,
        clients, connect, creer_client, creer_demande, creer_mission,
        creer_utilisateur, creer_vulnerabilite, demander_retest, demandes,
        echecs_recents, enregistrer_tentative, initialiser, journal_recent,
        journaliser, maj_dernier_acces, maj_mot_de_passe, maj_statut_demande,
        maj_statut_vuln, mission, missions, purger_tentatives, retests,
        retests_demandes, statistiques, utilisateur, valider_retest,
        verifier_connexion, vulnerabilite, vulnerabilites,
    )
    MOTEUR = "supabase"
else:
    from db_sqlite import (            # noqa: F401
        SEVERITES, SEVERITES_LIBELLE, STATUTS_VULN, STATUTS_VULN_LIBELLE,
        STATUTS_DEMANDE, STATUTS_DEMANDE_LIBELLE,
        clients, connect, creer_client, creer_demande, creer_mission,
        creer_utilisateur, creer_vulnerabilite, demander_retest, demandes,
        echecs_recents, enregistrer_tentative, initialiser, journal_recent,
        journaliser, maj_dernier_acces, maj_mot_de_passe, maj_statut_demande,
        maj_statut_vuln, mission, missions, purger_tentatives, retests,
        retests_demandes, statistiques, utilisateur, valider_retest,
        vulnerabilite, vulnerabilites,
    )
    MOTEUR = "sqlite"

    class ErreurBase(Exception):
        """Le moteur SQLite ne lève pas d'erreur de connexion distante."""

    def verifier_connexion() -> dict:
        return {"moteur": "sqlite", "chemin": str(config.DB_PATH)}


def description_moteur() -> str:
    """Résumé affiché au démarrage et sur la page Paramètres."""
    if MOTEUR == "supabase":
        return f"Supabase — {config.SUPABASE_URL}"
    return f"SQLite — {config.DB_PATH}"


def initialiser_si_necessaire(app) -> None:
    """Prépare le moteur, avec un message d'erreur exploitable en cas d'échec.

    Si le schéma Supabase est absent, l'application ne doit pas démarrer en
    silence avec un moteur inutilisable : elle doit le dire clairement, avec
    l'action à effectuer.
    """
    try:
        initialiser()
    except ErreurBase as e:
        print("\n" + "=" * 70)
        print("  ERREUR DE BASE DE DONNÉES")
        print("=" * 70)
        print(f"  {e}")
        print("=" * 70 + "\n")
        raise


__all__ = [
    "MOTEUR", "ErreurBase", "description_moteur", "initialiser_si_necessaire",
    "SEVERITES", "SEVERITES_LIBELLE", "STATUTS_VULN", "STATUTS_VULN_LIBELLE",
    "STATUTS_DEMANDE", "STATUTS_DEMANDE_LIBELLE",
    "connect", "initialiser", "verifier_connexion",
    "journaliser", "journal_recent",
    "creer_utilisateur", "utilisateur", "maj_mot_de_passe", "maj_dernier_acces",
    "enregistrer_tentative", "echecs_recents", "purger_tentatives",
    "creer_demande", "demandes", "maj_statut_demande",
    "clients", "creer_client", "missions", "mission", "creer_mission",
    "vulnerabilites", "vulnerabilite", "creer_vulnerabilite", "maj_statut_vuln",
    "demander_retest", "retests", "retests_demandes", "valider_retest",
    "statistiques",
]
