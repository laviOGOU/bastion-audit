"""
security.py — protections transverses de l'application.

Un site qui vend des tests d'intrusion doit être irréprochable sur sa propre
surface. Ce module porte :

  - les en-têtes de sécurité HTTP (CSP, anti-clickjacking, etc.) ;
  - la protection CSRF de tous les formulaires ;
  - la limitation des tentatives de connexion ;
  - des utilitaires de validation d'entrée.
"""
import hmac
import html
import re
import secrets
import threading
import time
from functools import wraps
from urllib.parse import urlparse

from flask import abort, redirect, request, session, url_for

import config
import db

# ---------------------------------------------------------------------------
# En-têtes de sécurité
# ---------------------------------------------------------------------------
# La politique de contenu n'autorise aucun script externe : tout le JavaScript
# est servi depuis /static. Les styles inline sont limités à ce que les gabarits
# déclarent explicitement via une nonce.
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "object-src 'none'"
)

EN_TETES = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}
# Note : l'en-tête « Server » n'est pas posé ici. Le serveur WSGI écrit le sien
# après le passage dans l'application, ce qui produirait un en-tête en double.
# Il est neutralisé à la source, dans la classe EnteteServeurNeutre de app.py.


def installer_en_tetes(app):
    @app.after_request
    def _appliquer(reponse):
        for cle, valeur in EN_TETES.items():
            reponse.headers.setdefault(cle, valeur)
        # HSTS uniquement en hébergement : en local on est en HTTP, et l'activer
        # casserait l'accès au site sur la machine de développement.
        if config.mode_hebergement():
            reponse.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if request.path.startswith(("/admin", "/espace-client")):
            reponse.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            reponse.headers["Pragma"] = "no-cache"
        return reponse


# ---------------------------------------------------------------------------
# Protection CSRF
# ---------------------------------------------------------------------------
def jeton_csrf() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def verifier_csrf() -> None:
    attendu = session.get("csrf")
    fourni = request.form.get("csrf") or request.headers.get("X-CSRF-Token")
    if not attendu or not fourni or not hmac.compare_digest(attendu, fourni):
        db.journaliser("csrf_refuse", f"{request.method} {request.path}",
                       ip=adresse_ip())
        abort(400, description="Jeton de sécurité invalide ou expiré.")


def proteger_formulaires(app):
    """Vérifie le jeton sur toute requête modifiant l'état.

    Le contrôle s'applique à l'ensemble des routes, administration comprise :
    un formulaire public est une porte d'entrée comme une autre.
    """
    @app.before_request
    def _verifier():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            verifier_csrf()


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
def adresse_ip() -> str:
    # Derrière un hébergeur, l'IP réelle arrive dans X-Forwarded-For.
    transmise = request.headers.get("X-Forwarded-For", "")
    if config.mode_hebergement() and transmise:
        return transmise.split(",")[0].strip()
    return request.remote_addr or "inconnue"


def connexion_autorisee() -> bool:
    return bool(session.get("utilisateur"))


def limite_atteinte() -> bool:
    return db.echecs_recents(adresse_ip(), config.FENETRE_TENTATIVES_MINUTES) \
        >= config.MAX_TENTATIVES_CONNEXION


def connexion_requise(vue):
    """Décorateur : protège l'espace d'administration."""
    @wraps(vue)
    def _enveloppe(*args, **kwargs):
        if not connexion_autorisee():
            # On mémorise la destination pour y revenir après connexion.
            cible = request.full_path if request.method == "GET" else None
            session["apres_connexion"] = cible
            return redirect(url_for("admin_connexion"))
        return vue(*args, **kwargs)
    return _enveloppe


def destination_sure(destination: str | None) -> str | None:
    """N'accepte qu'un chemin interne — jamais une URL absolue (anti-redirection)."""
    if not destination:
        return None
    analysée = urlparse(destination)
    if analysée.scheme or analysée.netloc:
        return None
    if not destination.startswith("/") or destination.startswith("//"):
        return None
    return destination


# ---------------------------------------------------------------------------
# Validation des entrées
# ---------------------------------------------------------------------------
COURRIEL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
BALISES = re.compile(r"<[^>]+>")


def nettoyer(texte: str | None, longueur_max: int = 4000) -> str:
    if not texte:
        return ""
    texte = BALISES.sub("", texte)
    return texte.strip()[:longueur_max]


def valider_demande(formulaire) -> tuple[dict, list[str]]:
    """Valide le formulaire de demande de devis. Renvoie (données, erreurs)."""
    donnees = {
        "organisation": nettoyer(formulaire.get("organisation"), 160),
        "contact_nom": nettoyer(formulaire.get("contact_nom"), 120),
        "contact_email": nettoyer(formulaire.get("contact_email"), 160),
        "contact_tel": nettoyer(formulaire.get("contact_tel"), 40),
        "perimetre": nettoyer(formulaire.get("perimetre"), 80),
        "taille_equipe": nettoyer(formulaire.get("taille_equipe"), 40),
        "message": nettoyer(formulaire.get("message"), 4000),
        "nda_demande": formulaire.get("nda_demande") == "on",
    }
    erreurs = []
    if len(donnees["organisation"]) < 2:
        erreurs.append("Le nom de l'organisation est obligatoire.")
    if len(donnees["contact_nom"]) < 2:
        erreurs.append("Le nom du contact est obligatoire.")
    if not COURRIEL.match(donnees["contact_email"]):
        erreurs.append("L'adresse électronique n'est pas valide.")
    if len(donnees["message"]) < 20:
        erreurs.append("Merci de décrire votre besoin en quelques phrases "
                       "(20 caractères minimum).")
    return donnees, erreurs


def echapper(valeur) -> str:
    return html.escape(str(valeur if valeur is not None else ""))


# ---------------------------------------------------------------------------
# Limitation de débit — en mémoire, par processus
# ---------------------------------------------------------------------------
# Utilisée sur les routes qui déclenchent un appel sortant vers un service
# tiers. Sans limitation, une telle page sert d'amplificateur : quelques octets
# envoyés par l'attaquant provoquent une requête sortante coûteuse, et le quota
# du service tiers peut être épuisé au détriment de tous les visiteurs.
#
# Le compteur vit en mémoire : il se réinitialise au redémarrage, et chaque
# processus a le sien. C'est suffisant pour un déploiement à une instance ; en
# multi-instance, il faut un stockage partagé (Redis ou une table dédiée).
_COMPTEURS: dict[str, list[float]] = {}
_VERROU = threading.Lock()


def limite_debit(cle: str, maximum: int, fenetre_secondes: int) -> bool:
    """Enregistre une requête et renvoie True si la limite est dépassée."""
    maintenant = time.monotonic()
    with _VERROU:
        horodatages = [t for t in _COMPTEURS.get(cle, [])
                       if maintenant - t < fenetre_secondes]
        depasse = len(horodatages) >= maximum
        if not depasse:
            horodatages.append(maintenant)
        _COMPTEURS[cle] = horodatages
        # Purge opportuniste : évite que le dictionnaire grossisse sans fin.
        if len(_COMPTEURS) > 5000:
            for autre in [c for c, v in _COMPTEURS.items()
                          if not v or maintenant - max(v) > fenetre_secondes]:
                _COMPTEURS.pop(autre, None)
    return depasse
