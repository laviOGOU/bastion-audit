"""
config.py — configuration centrale du site BASTION.

Tout se pilote ici. Pour renommer le site, il suffit de changer SITE_NOM :
l'en-tête, les pieds de page et les courriels se mettent à jour partout.
"""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _charger_env() -> None:
    """Charge le fichier .env s'il existe, sans écraser l'environnement réel.

    Une variable déjà présente dans l'environnement — par exemple fournie par la
    plateforme d'hébergement — garde la priorité sur le fichier local. C'est
    volontaire : en production, ce sont les variables du service qui font foi.
    """
    fichier = BASE_DIR / ".env"
    if not fichier.exists():
        return
    try:
        lignes = fichier.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        cle = cle.strip()
        valeur = valeur.strip().strip('"').strip("'")
        if cle and cle not in os.environ:
            os.environ[cle] = valeur


_charger_env()

STORAGE_DIR = Path(os.environ.get("AUDIT_STORAGE_DIR", BASE_DIR / "storage"))
DB_PATH = Path(os.environ.get("AUDIT_DB_PATH", STORAGE_DIR / "bastion.db"))
CLE_SECRETE_FICHIER = STORAGE_DIR / ".secret_key"

# --- Supabase (production) --------------------------------------------------
# Si ces deux variables sont renseignées, l'application utilise Supabase comme
# base de données et n'a plus besoin de SQLite. Sinon elle reste en local.
# La clé reste côté serveur : elle n'est jamais envoyée au navigateur.
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
SUPABASE_KEY = (os.environ.get("SUPABASE_KEY") or "").strip()

# AUDIT_MOTEUR force le moteur, ce qui permet de continuer à développer en local
# alors que les variables Supabase sont déjà renseignées :
#   "sqlite"   → SQLite, quoi qu'il arrive
#   "supabase" → Supabase, et échec explicite si le schéma n'est pas créé
#   absent ou "auto" → Supabase dès que les deux variables sont présentes
_MOTEUR_FORCE = (os.environ.get("AUDIT_MOTEUR") or "auto").strip().lower()
if _MOTEUR_FORCE == "sqlite":
    MOTEUR_SUPABASE = False
elif _MOTEUR_FORCE == "supabase":
    MOTEUR_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
else:
    MOTEUR_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
MOTEUR_FORCE = _MOTEUR_FORCE

# --- Identité du site -------------------------------------------------------
SITE_NOM = "BASTION"
SITE_BASELINE = "Audit & test d'intrusion"
SITE_SLOGAN = "Nous attaquons votre système avant qu'un autre ne le fasse."
SITE_SIGNATURE = "BASTION — Audit, test d'intrusion et conformité"

# --- Coordonnées ------------------------------------------------------------
CONTACT_COURRIEL = "ogouyapilevi@gmail.com"
CONTACT_TELEPHONE = "07 15 41 76 90"
CONTACT_WHATSAPP = "+225 07 15 41 76 90"
# Numéro au format international sans espaces, tel qu'attendu par wa.me
CONTACT_WHATSAPP_LIEN = "https://wa.me/2250715417690"
CONTACT_SIEGE = "Abidjan, Côte d'Ivoire"
CONTACT_VILLE = "Abidjan, Côte d'Ivoire"
CONTACT_HORAIRES = "Lundi – Vendredi, 8h – 18h (GMT)"

# Adresse de contact pour la divulgation responsable (RFC 9116)
SECURITY_TXT_CONTACT = CONTACT_COURRIEL
SECURITY_TXT_EXPIRES = "2027-12-31T23:59:59.000Z"
SECURITY_TXT_LANGUES = "fr, en"
SECURITY_TXT_POLITIQUE = "/divulgation-responsable"

# --- Sécurité ---------------------------------------------------------------
# La clé de session est générée au premier démarrage et conservée dans
# storage/.secret_key — jamais dans le code, jamais dans le dépôt Git.
SESSION_DUREE_MINUTES = 60
MAX_TENTATIVES_CONNEXION = 5          # par adresse IP
FENETRE_TENTATIVES_MINUTES = 15
LONGUEUR_MIN_MOT_DE_PASSE = 12

# Vérifications de dépendance : chaque appel déclenche une requête sortante vers
# l'API OSV. La limite protège le service tiers et évite l'usage amplificateur.
MAX_VERIFICATIONS_DEPENDANCE = 20     # par adresse IP
FENETRE_VERIFICATIONS_MINUTES = 5


def secret_key() -> bytes:
    """Lit la clé de session, ou la crée au premier démarrage."""
    env = os.environ.get("AUDIT_SECRET_KEY")
    if env:
        return env.encode("utf-8")
    CLE_SECRETE_FICHIER.parent.mkdir(parents=True, exist_ok=True)
    if not CLE_SECRETE_FICHIER.exists():
        CLE_SECRETE_FICHIER.write_text(secrets.token_hex(32), encoding="utf-8")
        try:                                   # droits restreints sous Windows
            os.chmod(CLE_SECRETE_FICHIER, 0o600)
        except OSError:
            pass
    return CLE_SECRETE_FICHIER.read_text(encoding="utf-8").strip().encode("utf-8")


def mode_hebergement() -> bool:
    """Vrai si l'application tourne derrière un hébergeur (variable PORT)."""
    return bool(os.environ.get("PORT"))


def adresse_ecoute() -> tuple[str, int]:
    """127.0.0.1 en local, 0.0.0.0 en hébergement."""
    if mode_hebergement():
        return "0.0.0.0", int(os.environ.get("PORT", 8000))
    return "127.0.0.1", int(os.environ.get("AUDIT_PORT", 5002))
