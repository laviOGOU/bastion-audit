"""
db_sqlite.py — moteur de base de données SQLite (développement et local).

Schéma pensé pour le portail PTaaS : un client, des missions, des
vulnérabilités, des demandes de re-test, et un journal de traçabilité.

Toutes les requêtes sont paramétrées. Aucune concaténation de chaîne SQL.

Ce module est le moteur utilisé par défaut. En production, si les variables
SUPABASE_URL et SUPABASE_KEY sont définies, c'est db_supabase.py qui prend le
relais — voir db.py, qui fait le choix au démarrage.
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import config

SEVERITES = ["critique", "eleve", "moyen", "faible", "info"]
SEVERITES_LIBELLE = {
    "critique": "Critique", "eleve": "Élevé", "moyen": "Moyen",
    "faible": "Faible", "info": "Informationnel",
}
STATUTS_VULN = ["ouverte", "en_correction", "corrigee", "acceptee"]
STATUTS_VULN_LIBELLE = {
    "ouverte": "Ouverte", "en_correction": "En correction",
    "corrigee": "Corrigée", "acceptee": "Risque accepté",
}
STATUTS_DEMANDE = ["nouveau", "qualifie", "devis_envoye", "gagne", "perdu"]
STATUTS_DEMANDE_LIBELLE = {
    "nouveau": "Nouveau", "qualifie": "Qualifié", "devis_envoye": "Devis envoyé",
    "gagne": "Gagné", "perdu": "Perdu",
}

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS utilisateurs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiant   TEXT UNIQUE NOT NULL,
    hash_mdp      TEXT NOT NULL,
    cree_le       TEXT NOT NULL,
    dernier_acces TEXT
);

CREATE TABLE IF NOT EXISTS tentatives (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ip          TEXT NOT NULL,
    identifiant TEXT,
    horodatage  TEXT NOT NULL,
    succes      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tentatives ON tentatives(ip, horodatage);

CREATE TABLE IF NOT EXISTS demandes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    cree_le        TEXT NOT NULL,
    organisation   TEXT NOT NULL,
    contact_nom    TEXT NOT NULL,
    contact_email  TEXT NOT NULL,
    contact_tel    TEXT,
    perimetre      TEXT,
    taille_equipe  TEXT,
    message        TEXT,
    nda_demande    INTEGER DEFAULT 0,
    statut         TEXT NOT NULL DEFAULT 'nouveau',
    notes          TEXT
);

CREATE TABLE IF NOT EXISTS clients (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nom       TEXT NOT NULL,
    secteur   TEXT,
    contact   TEXT,
    cree_le   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS missions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id     INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    reference     TEXT UNIQUE NOT NULL,
    perimetre     TEXT,
    referentiel   TEXT,
    date_debut    TEXT,
    date_fin      TEXT,
    statut        TEXT NOT NULL DEFAULT 'en_cours',
    cree_le       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vulnerabilites (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id     INTEGER REFERENCES missions(id) ON DELETE CASCADE,
    titre          TEXT NOT NULL,
    severite       TEXT NOT NULL,
    cvss           REAL,
    cwe            TEXT,
    categorie      TEXT,
    description    TEXT,
    impact         TEXT,
    preuve         TEXT,
    remediation    TEXT,
    statut         TEXT NOT NULL DEFAULT 'ouverte',
    responsable    TEXT,
    date_constat   TEXT NOT NULL,
    date_echeance  TEXT,
    date_correction TEXT
);

CREATE TABLE IF NOT EXISTS retests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    vuln_id     INTEGER REFERENCES vulnerabilites(id) ON DELETE CASCADE,
    demande_le  TEXT NOT NULL,
    realise_le  TEXT,
    resultat    TEXT
);

CREATE TABLE IF NOT EXISTS journal (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    horodatage TEXT NOT NULL,
    utilisateur TEXT,
    action     TEXT NOT NULL,
    detail     TEXT,
    ip         TEXT
);
"""


def _maintenant() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connect() -> sqlite3.Connection:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialiser() -> None:
    """Crée le schéma si nécessaire. Idempotent."""
    with connect() as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Journal de traçabilité
# ---------------------------------------------------------------------------
def journaliser(action: str, detail: str = "", utilisateur: str | None = None,
                ip: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO journal (horodatage, utilisateur, action, detail, ip) "
            "VALUES (?, ?, ?, ?, ?)",
            (_maintenant(), utilisateur, action, detail, ip),
        )


def journal_recent(limite: int = 60) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM journal ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()


# ---------------------------------------------------------------------------
# Utilisateurs de l'espace admin
# ---------------------------------------------------------------------------
def creer_utilisateur(identifiant: str, hash_mdp: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO utilisateurs (identifiant, hash_mdp, cree_le) VALUES (?, ?, ?)",
            (identifiant, hash_mdp, _maintenant()),
        )


def utilisateur(identifiant: str) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM utilisateurs WHERE identifiant = ?", (identifiant,)
        ).fetchone()


def maj_mot_de_passe(identifiant: str, hash_mdp: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE utilisateurs SET hash_mdp = ? WHERE identifiant = ?",
            (hash_mdp, identifiant),
        )


def maj_dernier_acces(identifiant: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE utilisateurs SET dernier_acces = ? WHERE identifiant = ?",
            (_maintenant(), identifiant),
        )


# ---------------------------------------------------------------------------
# Anti-force brute
# ---------------------------------------------------------------------------
def enregistrer_tentative(ip: str, identifiant: str, succes: bool) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO tentatives (ip, identifiant, horodatage, succes) "
            "VALUES (?, ?, ?, ?)",
            (ip, identifiant, _maintenant(), 1 if succes else 0),
        )


def echecs_recents(ip: str, fenetre_minutes: int) -> int:
    limite = (datetime.now() - timedelta(minutes=fenetre_minutes)).strftime(
        "%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        ligne = conn.execute(
            "SELECT COUNT(*) AS n FROM tentatives "
            "WHERE ip = ? AND succes = 0 AND horodatage > ?",
            (ip, limite),
        ).fetchone()
    return ligne["n"] if ligne else 0


def purger_tentatives(jours: int = 7) -> None:
    limite = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        conn.execute("DELETE FROM tentatives WHERE horodatage < ?", (limite,))


# ---------------------------------------------------------------------------
# Demandes de devis
# ---------------------------------------------------------------------------
def creer_demande(organisation, contact_nom, contact_email, contact_tel,
                  perimetre, taille_equipe, message, nda_demande) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO demandes (cree_le, organisation, contact_nom, contact_email, "
            "contact_tel, perimetre, taille_equipe, message, nda_demande) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_maintenant(), organisation, contact_nom, contact_email, contact_tel,
             perimetre, taille_equipe, message, 1 if nda_demande else 0),
        )
        return int(cur.lastrowid)


def demandes(statut: str | None = None) -> list[sqlite3.Row]:
    with connect() as conn:
        if statut:
            return conn.execute(
                "SELECT * FROM demandes WHERE statut = ? ORDER BY id DESC", (statut,)
            ).fetchall()
        return conn.execute("SELECT * FROM demandes ORDER BY id DESC").fetchall()


def maj_statut_demande(demande_id: int, statut: str, notes: str | None = None) -> None:
    with connect() as conn:
        if notes is None:
            conn.execute("UPDATE demandes SET statut = ? WHERE id = ?",
                         (statut, demande_id))
        else:
            conn.execute("UPDATE demandes SET statut = ?, notes = ? WHERE id = ?",
                         (statut, notes, demande_id))


# ---------------------------------------------------------------------------
# Clients et missions
# ---------------------------------------------------------------------------
def clients() -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM missions m WHERE m.client_id = c.id) "
            "AS nb_missions FROM clients c ORDER BY c.nom"
        ).fetchall()


def creer_client(nom: str, secteur: str, contact: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO clients (nom, secteur, contact, cree_le) VALUES (?, ?, ?, ?)",
            (nom, secteur, contact, _maintenant()),
        )
        return int(cur.lastrowid)


def missions(client_id: int | None = None) -> list[sqlite3.Row]:
    requete = (
        "SELECT m.*, c.nom AS client_nom, "
        "(SELECT COUNT(*) FROM vulnerabilites v WHERE v.mission_id = m.id) AS nb_vulns, "
        "(SELECT COUNT(*) FROM vulnerabilites v WHERE v.mission_id = m.id "
        " AND v.statut = 'corrigee') AS nb_corrigees "
        "FROM missions m LEFT JOIN clients c ON c.id = m.client_id "
    )
    with connect() as conn:
        if client_id:
            return conn.execute(
                requete + "WHERE m.client_id = ? ORDER BY m.id DESC", (client_id,)
            ).fetchall()
        return conn.execute(requete + "ORDER BY m.id DESC").fetchall()


def mission(mission_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(
            "SELECT m.*, c.nom AS client_nom FROM missions m "
            "LEFT JOIN clients c ON c.id = m.client_id WHERE m.id = ?",
            (mission_id,),
        ).fetchone()


def creer_mission(client_id, reference, perimetre, referentiel,
                  date_debut, date_fin, statut="en_cours") -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO missions (client_id, reference, perimetre, referentiel, "
            "date_debut, date_fin, statut, cree_le) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (client_id, reference, perimetre, referentiel, date_debut, date_fin,
             statut, _maintenant()),
        )
        return int(cur.lastrowid)


# ---------------------------------------------------------------------------
# Vulnérabilités
# ---------------------------------------------------------------------------
def vulnerabilites(mission_id: int | None = None, severite: str | None = None,
                   statut: str | None = None) -> list[sqlite3.Row]:
    requete = (
        "SELECT v.*, m.reference AS mission_ref, c.nom AS client_nom "
        "FROM vulnerabilites v "
        "LEFT JOIN missions m ON m.id = v.mission_id "
        "LEFT JOIN clients c ON c.id = m.client_id WHERE 1 = 1"
    )
    params: list = []
    if mission_id:
        requete += " AND v.mission_id = ?"
        params.append(mission_id)
    if severite:
        requete += " AND v.severite = ?"
        params.append(severite)
    if statut:
        requete += " AND v.statut = ?"
        params.append(statut)
    ordre = ("ORDER BY CASE v.severite WHEN 'critique' THEN 0 WHEN 'eleve' THEN 1 "
             "WHEN 'moyen' THEN 2 WHEN 'faible' THEN 3 ELSE 4 END, v.id DESC")
    with connect() as conn:
        return conn.execute(requete + " " + ordre, params).fetchall()


def vulnerabilite(vuln_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(
            "SELECT v.*, m.reference AS mission_ref, c.nom AS client_nom "
            "FROM vulnerabilites v LEFT JOIN missions m ON m.id = v.mission_id "
            "LEFT JOIN clients c ON c.id = m.client_id WHERE v.id = ?",
            (vuln_id,),
        ).fetchone()


def creer_vulnerabilite(mission_id, titre, severite, cvss, cwe, categorie,
                        description, impact, preuve, remediation, responsable,
                        date_echeance) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO vulnerabilites (mission_id, titre, severite, cvss, cwe, "
            "categorie, description, impact, preuve, remediation, responsable, "
            "date_constat, date_echeance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mission_id, titre, severite, cvss, cwe, categorie, description,
             impact, preuve, remediation, responsable, _maintenant(), date_echeance),
        )
        return int(cur.lastrowid)


def maj_statut_vuln(vuln_id: int, statut: str) -> None:
    with connect() as conn:
        if statut == "corrigee":
            conn.execute(
                "UPDATE vulnerabilites SET statut = ?, date_correction = ? WHERE id = ?",
                (statut, _maintenant(), vuln_id),
            )
        else:
            conn.execute("UPDATE vulnerabilites SET statut = ? WHERE id = ?",
                         (statut, vuln_id))


def demander_retest(vuln_id: int) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO retests (vuln_id, demande_le) VALUES (?, ?)",
            (vuln_id, _maintenant()),
        )


def retests(vuln_id: int | None = None) -> list[sqlite3.Row]:
    with connect() as conn:
        if vuln_id:
            return conn.execute(
                "SELECT * FROM retests WHERE vuln_id = ? ORDER BY id DESC", (vuln_id,)
            ).fetchall()
        return conn.execute(
            "SELECT r.*, v.titre AS vuln_titre FROM retests r "
            "LEFT JOIN vulnerabilites v ON v.id = r.vuln_id ORDER BY r.id DESC"
        ).fetchall()


def retests_demandes() -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT r.*, v.titre AS vuln_titre, v.severite AS vuln_severite, "
            "v.id AS vuln_id FROM retests r "
            "LEFT JOIN vulnerabilites v ON v.id = r.vuln_id "
            "WHERE r.realise_le IS NULL ORDER BY r.id DESC"
        ).fetchall()


def valider_retest(retest_id: int, resultat: str, corrigee: bool) -> None:
    with connect() as conn:
        ligne = conn.execute("SELECT vuln_id FROM retests WHERE id = ?",
                             (retest_id,)).fetchone()
        conn.execute(
            "UPDATE retests SET realise_le = ?, resultat = ? WHERE id = ?",
            (_maintenant(), resultat, retest_id),
        )
        if ligne and corrigee:
            conn.execute(
                "UPDATE vulnerabilites SET statut = 'corrigee', date_correction = ? "
                "WHERE id = ?", (_maintenant(), ligne["vuln_id"]),
            )


# ---------------------------------------------------------------------------
# Statistiques du tableau de bord
# ---------------------------------------------------------------------------
def statistiques() -> dict:
    with connect() as conn:
        def un(sql, params=()):
            ligne = conn.execute(sql, params).fetchone()
            return ligne[0] if ligne else 0

        total_vulns = un("SELECT COUNT(*) FROM vulnerabilites")
        corrigees = un("SELECT COUNT(*) FROM vulnerabilites WHERE statut = 'corrigee'")
        par_severite = {
            s: un("SELECT COUNT(*) FROM vulnerabilites WHERE severite = ?", (s,))
            for s in SEVERITES
        }
        ouverts = {
            s: un("SELECT COUNT(*) FROM vulnerabilites WHERE severite = ? "
                  "AND statut NOT IN ('corrigee','acceptee')", (s,))
            for s in SEVERITES
        }
        return {
            "demandes_nouvelles": un("SELECT COUNT(*) FROM demandes WHERE statut = 'nouveau'"),
            "demandes_total": un("SELECT COUNT(*) FROM demandes"),
            "clients": un("SELECT COUNT(*) FROM clients"),
            "missions_actives": un("SELECT COUNT(*) FROM missions WHERE statut = 'en_cours'"),
            "missions_total": un("SELECT COUNT(*) FROM missions"),
            "vulns_total": total_vulns,
            "vulns_corrigees": corrigees,
            "vulns_ouvertes": un("SELECT COUNT(*) FROM vulnerabilites "
                                 "WHERE statut NOT IN ('corrigee','acceptee')"),
            "retests_en_attente": un("SELECT COUNT(*) FROM retests WHERE realise_le IS NULL"),
            "taux_correction": round(100 * corrigees / total_vulns) if total_vulns else 0,
            "par_severite": par_severite,
            "ouvertes_par_severite": ouverts,
        }


# Le moteur SQLite expose exactement l'interface attendue par db.py, qui choisit
# l'implémentation au démarrage selon la configuration disponible.
__all__ = [
    "SEVERITES", "SEVERITES_LIBELLE", "STATUTS_VULN", "STATUTS_VULN_LIBELLE",
    "STATUTS_DEMANDE", "STATUTS_DEMANDE_LIBELLE", "MOTEUR",
    "connect", "initialiser", "journaliser", "journal_recent",
    "creer_utilisateur", "utilisateur", "maj_mot_de_passe", "maj_dernier_acces",
    "enregistrer_tentative", "echecs_recents", "purger_tentatives",
    "creer_demande", "demandes", "maj_statut_demande",
    "clients", "creer_client", "missions", "mission", "creer_mission",
    "vulnerabilites", "vulnerabilite", "creer_vulnerabilite", "maj_statut_vuln",
    "demander_retest", "retests", "retests_demandes", "valider_retest",
    "statistiques",
]

MOTEUR = "sqlite"
