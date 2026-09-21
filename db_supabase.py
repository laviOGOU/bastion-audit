"""
db_supabase.py — moteur de base de données Supabase (production).

Même interface que db_sqlite.py : db.py choisit l'un ou l'autre au démarrage
selon la présence de SUPABASE_URL et SUPABASE_KEY dans l'environnement. Aucun
gabarit, aucune route n'a besoin de savoir quel moteur est actif.

Fonctionnement technique : Supabase expose PostgreSQL par une API REST générée
automatiquement (PostgREST), et non par un protocole SQL. Toutes les opérations
passent donc par des requêtes HTTP :

    lecture   GET    /rest/v1/<table>?<filtres>&select=*
    insertion POST   /rest/v1/<table>          (en-tête Prefer: return=representation)
    mise à jour PATCH /rest/v1/<table>?id=eq.<n>
    suppression DELETE /rest/v1/<table>?<filtres>
    comptage  GET    /rest/v1/<table>?select=id  avec Prefer: count=exact

L'en-tête de réponse « Content-Range » porte le compte exact demandé, sans
transférer les lignes — c'est la méthode prévue par PostgREST pour compter.

Aucune dépendance supplémentaire : urllib de la bibliothèque standard suffit.

⚠️  La clé utilisée reste sur le serveur. Elle ne doit jamais être envoyée au
navigateur. Si RLS est actif sans politique pour le rôle « anon » — la
configuration recommandée — il faut la clé « service_role ».
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import config

MOTEUR = "supabase"

# Les libellés sont identiques quel que soit le moteur : ils servent aux gabarits.
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

# Préfixe des tables : le projet Supabase peut héberger d'autres applications.
P = "bastion_"
DELAI = 25

TABLES = [P + nom for nom in (
    "utilisateurs", "tentatives", "demandes", "clients", "missions",
    "vulnerabilites", "retests", "journal")]


class ErreurBase(Exception):
    """Erreur de communication avec Supabase, explicite pour l'administrateur."""


def _url() -> str:
    return (config.SUPABASE_URL or "").rstrip("/")


def _entetes(extra: dict | None = None) -> dict:
    entetes = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "BASTION/1.0",
    }
    entetes.update(extra or {})
    return entetes


def _appeler(methode: str, table: str, *, params: dict | None = None,
             corps=None, entetes: dict | None = None,
             avec_compte: bool = False) -> tuple[int, dict, object]:
    """Exécute une requête PostgREST. Renvoie (code, en-têtes, données)."""
    if not (_url() and config.SUPABASE_KEY):
        raise ErreurBase("SUPABASE_URL ou SUPABASE_KEY n'est pas défini.")

    requete_url = f"{_url()}/rest/v1/{table}"
    if params:
        requete_url += "?" + urllib.parse.urlencode(params, safe=".*,")

    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    complement = dict(entetes or {})
    if avec_compte:
        complement["Prefer"] = "count=exact"
        complement["Range-Unit"] = "items"
        complement["Range"] = "0-0"

    try:
        requete = urllib.request.Request(requete_url, data=donnees,
                                         method=methode,
                                         headers=_entetes(complement))
        with urllib.request.urlopen(requete, timeout=DELAI) as reponse:
            brut = reponse.read().decode("utf-8", "replace")
            return reponse.status, dict(reponse.headers), (json.loads(brut) if brut else None)
    except urllib.error.HTTPError as e:
        corps_erreur = e.read().decode("utf-8", "replace")
        # Message lisible : le cas le plus fréquent est la table absente, qui
        # signifie que le script supabase_schema.sql n'a pas encore été exécuté.
        if e.code == 404 or "does not exist" in corps_erreur:
            raise ErreurBase(
                f"La table « {table} » n'existe pas dans le projet Supabase. "
                f"Exécutez supabase_schema.sql dans l'éditeur SQL du projet."
            ) from e
        if e.code in (401, 403):
            raise ErreurBase(
                f"Accès refusé à « {table} » ({e.code}). Vérifiez la clé utilisée : "
                f"si RLS est actif sans politique pour le rôle anon, il faut la clé "
                f"service_role. Détail : {corps_erreur[:200]}"
            ) from e
        raise ErreurBase(
            f"Supabase a répondu {e.code} sur « {table} ». Détail : {corps_erreur[:300]}"
        ) from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErreurBase(f"Supabase est injoignable : {type(e).__name__}.") from e


def _compter(table: str, filtres: dict | None = None) -> int:
    """Compte exact via l'en-tête Content-Range, sans transférer les lignes."""
    params = {"select": "id", **(filtres or {})}
    _, entetes, _ = _appeler("GET", table, params=params, avec_compte=True)
    plage = entetes.get("Content-Range") or entetes.get("content-range") or ""
    if "/" in plage:
        total = plage.rsplit("/", 1)[-1].strip()
        if total.isdigit():
            return int(total)
    return 0


def _lignes(table: str, filtres: dict | None = None, ordre: str | None = None,
            limite: int | None = None) -> list[dict]:
    params = {"select": "*"}
    params.update(filtres or {})
    if ordre:
        params["order"] = ordre
    if limite:
        params["limit"] = limite
    _, _, donnees = _appeler("GET", table, params=params)
    return donnees or []


def _une(table: str, filtres: dict) -> dict | None:
    lignes = _lignes(table, filtres, limite=1)
    return lignes[0] if lignes else None


def _inserer(table: str, valeurs: dict) -> int:
    _, _, donnees = _appeler("POST", table, corps=valeurs,
                             entetes={"Prefer": "return=representation"})
    if isinstance(donnees, list) and donnees:
        return int(donnees[0]["id"])
    return 0


def _maj(table: str, filtres: dict, valeurs: dict) -> None:
    _appeler("PATCH", table, params=filtres, corps=valeurs)


def _supprimer(table: str, filtres: dict) -> None:
    _appeler("DELETE", table, params=filtres)


def _maintenant() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _tri_severite(lignes: list[dict]) -> list[dict]:
    """PostgREST ne sait pas trier sur une sévérité personnalisée : on trie ici,
    du plus grave au moins grave, puis du plus récent au plus ancien."""
    def cle(ligne):
        severite = ligne.get("severite") or "info"
        rang = SEVERITES.index(severite) if severite in SEVERITES else len(SEVERITES)
        return (rang, -int(ligne.get("id") or 0))
    return sorted(lignes, key=cle)


# ---------------------------------------------------------------------------
# Initialisation et diagnostic
# ---------------------------------------------------------------------------
def connect():
    """Sans objet pour ce moteur : conservé pour que le code appelant reste
    identique. Renvoie None."""
    return None


def initialiser() -> None:
    """Vérifie que le schéma existe et échoue avec un message actionnable sinon.

    Aucune création de table n'est tentée : l'API REST de Supabase ne permet pas
    d'exécuter du DDL, et c'est volontaire. Le schéma se crée une fois, à la
    main, en collant supabase_schema.sql dans l'éditeur SQL du projet.
    """
    absentes = []
    for table in TABLES:
        try:
            _compter(table)
        except ErreurBase:
            absentes.append(table)
    if absentes:
        raise ErreurBase(
            "Tables manquantes dans Supabase : " + ", ".join(absentes) + ". "
            "Ouvrez le tableau de bord Supabase → SQL Editor, collez le contenu "
            "de supabase_schema.sql et exécutez-le."
        )


def verifier_connexion() -> dict:
    """Diagnostic utilisé par les scripts de vérification."""
    rapport = {"url": _url(), "tables": {}}
    for table in TABLES:
        try:
            rapport["tables"][table] = _compter(table)
        except ErreurBase as e:
            rapport["tables"][table] = f"ERREUR : {e}"
    return rapport


# ---------------------------------------------------------------------------
# Journal de traçabilité
# ---------------------------------------------------------------------------
def journaliser(action: str, detail: str = "", utilisateur: str | None = None,
                ip: str | None = None) -> None:
    _inserer(P + "journal", {
        "horodatage": _maintenant(), "utilisateur": utilisateur,
        "action": action, "detail": detail or "", "ip": ip,
    })


def journal_recent(limite: int = 60) -> list[dict]:
    return _lignes(P + "journal", ordre="horodatage.desc,id.desc", limite=limite)


# ---------------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------------
def creer_utilisateur(identifiant: str, hash_mdp: str) -> None:
    _inserer(P + "utilisateurs",
             {"identifiant": identifiant, "hash_mdp": hash_mdp, "cree_le": _maintenant()})


def utilisateur(identifiant: str) -> dict | None:
    return _une(P + "utilisateurs", {"identifiant": f"eq.{identifiant}"})


def maj_mot_de_passe(identifiant: str, hash_mdp: str) -> None:
    _maj(P + "utilisateurs", {"identifiant": f"eq.{identifiant}"},
         {"hash_mdp": hash_mdp})


def maj_dernier_acces(identifiant: str) -> None:
    _maj(P + "utilisateurs", {"identifiant": f"eq.{identifiant}"},
         {"dernier_acces": _maintenant()})


# ---------------------------------------------------------------------------
# Anti-force brute
# ---------------------------------------------------------------------------
def enregistrer_tentative(ip: str, identifiant: str, succes: bool) -> None:
    _inserer(P + "tentatives", {
        "ip": ip or "inconnue", "identifiant": identifiant,
        "horodatage": _maintenant(), "succes": 1 if succes else 0,
    })


def echecs_recents(ip: str, fenetre_minutes: int) -> int:
    limite = (datetime.now() - timedelta(minutes=fenetre_minutes)).strftime(
        "%Y-%m-%d %H:%M:%S")
    return _compter(P + "tentatives", {
        "ip": f"eq.{ip or 'inconnue'}", "succes": "eq.0",
        "horodatage": f"gt.{limite}",
    })


def purger_tentatives(jours: int = 7) -> None:
    limite = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d %H:%M:%S")
    _supprimer(P + "tentatives", {"horodatage": f"lt.{limite}"})


# ---------------------------------------------------------------------------
# Demandes de devis
# ---------------------------------------------------------------------------
def creer_demande(organisation, contact_nom, contact_email, contact_tel,
                  perimetre, taille_equipe, message, nda_demande) -> int:
    return _inserer(P + "demandes", {
        "cree_le": _maintenant(), "organisation": organisation,
        "contact_nom": contact_nom, "contact_email": contact_email,
        "contact_tel": contact_tel, "perimetre": perimetre,
        "taille_equipe": taille_equipe, "message": message,
        "nda_demande": 1 if nda_demande else 0, "statut": "nouveau", "notes": None,
    })


def demandes(statut: str | None = None) -> list[dict]:
    filtres = {"statut": f"eq.{statut}"} if statut else None
    return _lignes(P + "demandes", filtres, ordre="id.desc")


def maj_statut_demande(demande_id: int, statut: str, notes: str | None = None) -> None:
    valeurs = {"statut": statut}
    if notes is not None:
        valeurs["notes"] = notes
    _maj(P + "demandes", {"id": f"eq.{demande_id}"}, valeurs)


# ---------------------------------------------------------------------------
# Clients et missions
# ---------------------------------------------------------------------------
def clients() -> list[dict]:
    lignes = _lignes(P + "clients", ordre="nom.asc")
    missions_par_client: dict[int, int] = {}
    for m in _lignes(P + "missions", {"select": "client_id"}):
        cle = m.get("client_id")
        if cle is not None:
            missions_par_client[cle] = missions_par_client.get(cle, 0) + 1
    for ligne in lignes:
        ligne["nb_missions"] = missions_par_client.get(ligne["id"], 0)
    return lignes


def creer_client(nom: str, secteur: str, contact: str) -> int:
    return _inserer(P + "clients", {
        "nom": nom, "secteur": secteur, "contact": contact, "cree_le": _maintenant()})


def mission(mission_id: int) -> dict | None:
    ligne = _une(P + "missions", {"id": f"eq.{mission_id}"})
    if ligne and ligne.get("client_id"):
        client = _une(P + "clients", {"id": f"eq.{ligne['client_id']}"})
        ligne["client_nom"] = client["nom"] if client else None
    return ligne


def missions(client_id: int | None = None) -> list[dict]:
    filtres = {"client_id": f"eq.{client_id}"} if client_id else None
    lignes = _lignes(P + "missions", filtres, ordre="id.desc")
    clients_par_id = {c["id"]: c["nom"] for c in _lignes(P + "clients",
                                                         {"select": "id,nom"})}
    compte = {}
    corrigees = {}
    for v in _lignes(P + "vulnerabilites", {"select": "mission_id,statut"}):
        cle = v.get("mission_id")
        if cle is None:
            continue
        compte[cle] = compte.get(cle, 0) + 1
        if v.get("statut") == "corrigee":
            corrigees[cle] = corrigees.get(cle, 0) + 1
    for ligne in lignes:
        ligne["client_nom"] = clients_par_id.get(ligne.get("client_id"))
        ligne["nb_vulns"] = compte.get(ligne["id"], 0)
        ligne["nb_corrigees"] = corrigees.get(ligne["id"], 0)
    return lignes


def creer_mission(client_id, reference, perimetre, referentiel,
                  date_debut, date_fin, statut="en_cours") -> int:
    return _inserer(P + "missions", {
        "client_id": client_id, "reference": reference, "perimetre": perimetre,
        "referentiel": referentiel, "date_debut": date_debut, "date_fin": date_fin,
        "statut": statut, "cree_le": _maintenant(),
    })


# ---------------------------------------------------------------------------
# Vulnérabilités
# ---------------------------------------------------------------------------
def vulnerabilites(mission_id: int | None = None, severite: str | None = None,
                   statut: str | None = None) -> list[dict]:
    filtres = {}
    if mission_id:
        filtres["mission_id"] = f"eq.{mission_id}"
    if severite:
        filtres["severite"] = f"eq.{severite}"
    if statut:
        filtres["statut"] = f"eq.{statut}"
    lignes = _lignes(P + "vulnerabilites", filtres or None)
    _enrichir(lignes)
    return _tri_severite(lignes)


def vulnerabilite(vuln_id: int) -> dict | None:
    ligne = _une(P + "vulnerabilites", {"id": f"eq.{vuln_id}"})
    if ligne:
        _enrichir([ligne])
    return ligne


def _enrichir(lignes: list[dict]) -> None:
    """Ajoute la référence de mission et le nom du client, comme le fait la
    jointure de la version SQLite."""
    if not lignes:
        return
    missions_par_id = {m["id"]: m for m in _lignes(P + "missions")}
    clients_par_id = {c["id"]: c["nom"] for c in _lignes(P + "clients")}
    for ligne in lignes:
        m = missions_par_id.get(ligne.get("mission_id"))
        ligne["mission_ref"] = m["reference"] if m else None
        ligne["client_nom"] = clients_par_id.get(m["client_id"]) if m else None


def creer_vulnerabilite(mission_id, titre, severite, cvss, cwe, categorie,
                        description, impact, preuve, remediation, responsable,
                        date_echeance) -> int:
    return _inserer(P + "vulnerabilites", {
        "mission_id": mission_id, "titre": titre, "severite": severite,
        "cvss": cvss, "cwe": cwe, "categorie": categorie,
        "description": description, "impact": impact, "preuve": preuve,
        "remediation": remediation, "responsable": responsable,
        "statut": "ouverte", "date_constat": _maintenant(),
        "date_echeance": date_echeance,
    })


def maj_statut_vuln(vuln_id: int, statut: str) -> None:
    valeurs = {"statut": statut}
    if statut == "corrigee":
        valeurs["date_correction"] = _maintenant()
    _maj(P + "vulnerabilites", {"id": f"eq.{vuln_id}"}, valeurs)


def demander_retest(vuln_id: int) -> None:
    _inserer(P + "retests", {"vuln_id": vuln_id, "demande_le": _maintenant()})


def retests(vuln_id: int | None = None) -> list[dict]:
    filtres = {"vuln_id": f"eq.{vuln_id}"} if vuln_id else None
    lignes = _lignes(P + "retests", filtres, ordre="id.desc")
    titres = {v["id"]: v["titre"] for v in _lignes(P + "vulnerabilites",
                                                  {"select": "id,titre"})}
    for ligne in lignes:
        ligne["vuln_titre"] = titres.get(ligne.get("vuln_id"))
    return lignes


def retests_demandes() -> list[dict]:
    lignes = _lignes(P + "retests", {"realise_le": "is.null"}, ordre="id.desc")
    vulns = {v["id"]: v for v in _lignes(P + "vulnerabilites",
                                         {"select": "id,titre,severite"})}
    for ligne in lignes:
        v = vulns.get(ligne.get("vuln_id")) or {}
        ligne["vuln_titre"] = v.get("titre")
        ligne["vuln_severite"] = v.get("severite")
        ligne["vuln_id"] = ligne.get("vuln_id")
    return lignes


def valider_retest(retest_id: int, resultat: str, corrigee: bool) -> None:
    ligne = _une(P + "retests", {"id": f"eq.{retest_id}"})
    _maj(P + "retests", {"id": f"eq.{retest_id}"},
         {"realise_le": _maintenant(), "resultat": resultat})
    if ligne and corrigee and ligne.get("vuln_id"):
        maj_statut_vuln(ligne["vuln_id"], "corrigee")


# ---------------------------------------------------------------------------
# Statistiques
# ---------------------------------------------------------------------------
def statistiques() -> dict:
    par_severite = {}
    ouvertes_par_severite = {}
    for severite in SEVERITES:
        par_severite[severite] = _compter(P + "vulnerabilites",
                                          {"severite": f"eq.{severite}"})
        # PostgREST accepte la négation : statut=not.in.(corrigee,acceptee)
        ouvertes_par_severite[severite] = _compter(
            P + "vulnerabilites",
            {"severite": f"eq.{severite}", "statut": "not.in.(corrigee,acceptee)"},
        )

    total_vulns = _compter(P + "vulnerabilites")
    corrigees = _compter(P + "vulnerabilites", {"statut": "eq.corrigee"})
    ouvertes = _compter(P + "vulnerabilites",
                        {"statut": "not.in.(corrigee,acceptee)"})

    return {
        "demandes_nouvelles": _compter(P + "demandes", {"statut": "eq.nouveau"}),
        "demandes_total": _compter(P + "demandes"),
        "clients": _compter(P + "clients"),
        "missions_actives": _compter(P + "missions", {"statut": "eq.en_cours"}),
        "missions_total": _compter(P + "missions"),
        "vulns_total": total_vulns,
        "vulns_corrigees": corrigees,
        "vulns_ouvertes": ouvertes,
        "retests_en_attente": _compter(P + "retests", {"realise_le": "is.null"}),
        "taux_correction": round(100 * corrigees / total_vulns) if total_vulns else 0,
        "par_severite": par_severite,
        "ouvertes_par_severite": ouvertes_par_severite,
    }


__all__ = [
    "SEVERITES", "SEVERITES_LIBELLE", "STATUTS_VULN", "STATUTS_VULN_LIBELLE",
    "STATUTS_DEMANDE", "STATUTS_DEMANDE_LIBELLE", "MOTEUR", "ErreurBase",
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
