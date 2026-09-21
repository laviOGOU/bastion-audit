"""
providers/osv.py — interrogation de l'API OSV (Open Source Vulnerabilities).

OSV est la base de référence des vulnérabilités de bibliothèques open source,
agrégée par Google à partir de GitHub Advisory, PyPA, RustSec, Go et d'autres
sources. Elle est publique, gratuite, sans clé d'API.

Usage sur le site : la page « Vérifier une dépendance » permet à un visiteur de
savoir si la version d'une bibliothèque qu'il utilise est concernée par des
vulnérabilités connues. C'est exactement le contrôle que nous appliquons pendant
un audit sur le constat « composant vulnérable ».

Documentation : https://google.github.io/osv.dev/api/
"""
import json
import urllib.error
import urllib.request

API = "https://api.osv.dev/v1/query"
DELAI = 20

ECOSYSTEMES = [
    ("npm", "npm — JavaScript et Node.js"),
    ("PyPI", "PyPI — Python"),
    ("Maven", "Maven — Java"),
    ("Go", "Go modules"),
    ("crates.io", "crates.io — Rust"),
    ("NuGet", ".NET et NuGet"),
    ("Packagist", "Packagist — PHP"),
    ("RubyGems", "RubyGems — Ruby"),
    ("Pub", "Pub — Dart et Flutter"),
    ("Hex", "Hex — Elixir"),
]

# Niveaux de gravité que l'on rencontre dans les avis OSV, du plus grave au
# moins grave. Sert à classer les résultats dans le rapport.
ORDRE_GRAVITE = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "MEDIUM": 2,
                 "LOW": 3, "UNKNOWN": 4}

LIBELLE_GRAVITE = {"CRITICAL": "Critique", "HIGH": "Élevé", "MODERATE": "Moyen",
                   "MEDIUM": "Moyen", "LOW": "Faible", "UNKNOWN": "Non évalué"}

# Correspondance vers les classes CSS du site.
CLASSE_GRAVITE = {"CRITICAL": "sev-critique", "HIGH": "sev-eleve",
                  "MODERATE": "sev-moyen", "MEDIUM": "sev-moyen",
                  "LOW": "sev-faible", "UNKNOWN": "sev-info"}


class ErreurOSV(Exception):
    """Erreur d'interrogation de l'API, à afficher telle quelle à l'utilisateur."""


def _gravite(vulnerabilite: dict) -> str:
    """Déduit la gravité : base de données d'origine, puis score CVSS."""
    specifique = vulnerabilite.get("database_specific") or {}
    valeur = (specifique.get("severity") or "").upper()
    if valeur in ORDRE_GRAVITE:
        return valeur

    for entree in vulnerabilite.get("severity") or []:
        score = entree.get("score", "")
        # Les scores CVSS v3 sont renvoyés sous forme de vecteur ; on lit le
        # nombre quand il est présent, sinon on retombe sur le vecteur.
        if isinstance(score, str) and score.startswith("CVSS:"):
            vecteur = score
            if "/C:H" in vecteur or "/I:H" in vecteur:
                return "HIGH"
            if "/C:L" in vecteur or "/I:L" in vecteur:
                return "LOW"
    return "UNKNOWN"


def _version_corrigee(vulnerabilite: dict) -> str | None:
    """Première version corrigée publiée, si l'avis en indique une."""
    for affecte in vulnerabilite.get("affected") or []:
        for plage in affecte.get("ranges") or []:
            for evenement in plage.get("events") or []:
                if "fixed" in evenement:
                    return evenement["fixed"]
    return None


def _reference(vulnerabilite: dict) -> str | None:
    for reference in vulnerabilite.get("references") or []:
        if reference.get("type") in ("ADVISORY", "WEB", "ARTICLE"):
            return reference.get("url")
    for reference in vulnerabilite.get("references") or []:
        return reference.get("url")
    return None


def interroger(paquet: str, ecosysteme: str, version: str | None = None) -> dict:
    """
    Interroge OSV pour un paquet donné.

    Renvoie {"paquet", "ecosysteme", "version", "vulnerabilites": [...], "total"}.
    Lève ErreurOSV si l'API est injoignable ou répond une erreur.
    """
    paquet = (paquet or "").strip()
    ecosysteme = (ecosysteme or "").strip()
    version = (version or "").strip() or None

    if not paquet:
        raise ErreurOSV("Le nom du paquet est obligatoire.")
    if ecosysteme not in dict(ECOSYSTEMES):
        raise ErreurOSV(f"Écosystème non reconnu : {ecosysteme}")

    charge = {"package": {"name": paquet, "ecosystem": ecosysteme}}
    if version:
        charge["version"] = version

    requete = urllib.request.Request(
        API, data=json.dumps(charge).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": "BASTION-Audit/1.0 (verification de dependance)"})

    try:
        with urllib.request.urlopen(requete, timeout=DELAI) as reponse:
            donnees = json.load(reponse)
    except urllib.error.HTTPError as e:
        if e.code == 400:
            raise ErreurOSV("Requête refusée par l'API : vérifiez le nom du paquet "
                            "et l'écosystème sélectionné.") from e
        raise ErreurOSV(f"L'API OSV a répondu une erreur {e.code}.") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErreurOSV("L'API OSV est injoignable pour le moment. "
                        "Cette vérification dépend d'un service externe : "
                        "réessayez dans quelques instants.") from e
    except json.JSONDecodeError as e:
        raise ErreurOSV("Réponse illisible de l'API OSV.") from e

    resultats = []
    for brute in donnees.get("vulns") or []:
        gravite = _gravite(brute)
        resultats.append({
            "id": brute.get("id", "sans identifiant"),
            "alias": (brute.get("aliases") or [None])[0],
            "resume": brute.get("summary") or brute.get("details", "")[:220],
            "gravite": gravite,
            "gravite_libelle": LIBELLE_GRAVITE.get(gravite, "Non évalué"),
            "gravite_classe": CLASSE_GRAVITE.get(gravite, "sev-info"),
            "version_corrigee": _version_corrigee(brute),
            "publiee": (brute.get("published") or "")[:10],
            "reference": _reference(brute),
        })

    resultats.sort(key=lambda v: ORDRE_GRAVITE.get(v["gravite"], 4))

    return {
        "paquet": paquet,
        "ecosysteme": ecosysteme,
        "version": version,
        "vulnerabilites": resultats,
        "total": len(resultats),
        "critiques": sum(1 for v in resultats
                         if v["gravite"] in ("CRITICAL", "HIGH")),
    }
