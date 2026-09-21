"""Test de bout en bout de toutes les routes de BASTION."""
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5002"

jar = http.cookiejar.CookieJar()
ouvreur = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


class SansRedirection(urllib.request.HTTPRedirectHandler):
    """Permet de lire un code 302 brut : urllib suivrait la redirection sinon,
    et l'on verrait seulement la page d'arrivée en 200."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


ouvreur_brut = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(jar), SansRedirection())


def appel_brut(chemin):
    """Comme `appel`, mais sans suivre les redirections."""
    requete = urllib.request.Request(BASE + chemin, method="GET")
    requete.add_header("User-Agent", "TestBASTION/1.0")
    try:
        with ouvreur_brut.open(requete, timeout=20) as reponse:
            return reponse.status, dict(reponse.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)


def appel(chemin, methode="GET", donnees=None, entetes=None):
    url = BASE + chemin
    corps = None
    if donnees is not None:
        corps = urllib.parse.urlencode(donnees).encode("utf-8")
    requete = urllib.request.Request(url, data=corps, method=methode)
    requete.add_header("User-Agent", "TestBASTION/1.0")
    for cle, valeur in (entetes or {}).items():
        requete.add_header(cle, valeur)
    if corps is not None:
        requete.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with ouvreur.open(requete, timeout=20) as reponse:
            return reponse.status, dict(reponse.headers), reponse.read().decode(
                "utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def csrf(html):
    m = re.search(r'name="csrf"\s+value="([^"]+)"', html)
    return m.group(1) if m else None


resultats = []


def verifier(nom, condition, detail=""):
    resultats.append((nom, condition, detail))
    marque = "OK  " if condition else "ECHEC"
    print(f"  [{marque}] {nom}" + (f"  — {detail}" if detail and not condition else ""))


print("=" * 74)
print("  PAGES PUBLIQUES")
print("=" * 74)
pages = [
    ("/", "BASTION", "accueil"),
    ("/expertise", "Référentiels de contrôle", "expertise et méthodologies"),
    ("/conformite", "Ce que nous ne revendiquons pas", "conformité et certifications"),
    ("/livrables", "PTaaS", "livrables et rapports"),
    ("/ethique", "engagement", "transparence éthique"),
    ("/divulgation-responsable", "security.txt", "divulgation responsable"),
    ("/ptass", "Données de démonstration", "portail de suivi"),
    ("/contact", "Demande de devis", "formulaire de contact"),
]
for chemin, attendu, libelle in pages:
    code, entetes, corps = appel(chemin)
    verifier(f"GET {chemin:<26} → {code}",
             code == 200 and attendu.lower() in corps.lower(),
             f"attendu 200 + « {attendu} »")

print()
print("=" * 74)
print("  FICHIERS TECHNIQUES")
print("=" * 74)
code, entetes, corps = appel("/.well-known/security.txt")
verifier("/.well-known/security.txt → 200 + text/plain",
         code == 200 and "text/plain" in entetes.get("Content-Type", ""),
         entetes.get("Content-Type", ""))
verifier("security.txt contient un Contact et un Expires",
         "Contact: mailto:" in corps and "Expires:" in corps)

code, _, corps = appel("/security.txt")
verifier("/security.txt (alias) → 200", code == 200)

code, _, corps = appel("/robots.txt")
verifier("robots.txt interdit /admin", code == 200 and "Disallow: /admin" in corps)

code, _, corps = appel("/sitemap.xml")
verifier("sitemap.xml bien formé", code == 200 and "<urlset" in corps)

code, entetes, corps = appel("/rapport-exemple")
verifier("rapport-exemple se télécharge",
         code == 200 and "wordprocessingml" in entetes.get("Content-Type", ""),
         entetes.get("Content-Type", ""))

print()
print("=" * 74)
print("  EN-TÊTES DE SÉCURITÉ")
print("=" * 74)
code, entetes, _ = appel("/")
for entete, attendu in (
    ("Content-Security-Policy", "default-src 'self'"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "strict-origin"),
    ("Permissions-Policy", "camera=()"),
    ("Cross-Origin-Opener-Policy", "same-origin"),
):
    verifier(f"{entete}", attendu in entetes.get(entete, ""),
             entetes.get(entete, "ABSENT"))

print()
print("=" * 74)
print("  PROTECTION CSRF")
print("=" * 74)
code, _, corps = appel("/contact", "POST", {
    "organisation": "Test sans jeton", "contact_nom": "Test",
    "contact_email": "test@exemple.ci", "message": "Ceci est un test."})
verifier("POST sans jeton CSRF rejeté (400)", code == 400, f"code reçu {code}")

code, _, html = appel("/contact")
jeton = csrf(html)
verifier("jeton CSRF présent dans le formulaire", bool(jeton))

code, _, corps = appel("/contact", "POST", {
    "csrf": jeton, "organisation": "Test sans jeton",
    "contact_nom": "Test", "contact_email": "pas-un-courriel",
    "message": "Ceci est un test suffisamment long."})
verifier("courriel invalide rejeté (400)", code == 400, f"code reçu {code}")

code, _, corps = appel("/contact", "POST", {
    "csrf": jeton, "organisation": "Test de bout en bout",
    "contact_nom": "Vérification automatisée", "contact_email": "test@exemple.ci",
    "contact_tel": "+225 00 00 00 00", "perimetre": "Applications web",
    "taille_equipe": "1 à 5 personnes",
    "message": "Demande créée par le test automatisé de bout en bout. "
               "Ce message dépasse vingt caractères.", "nda_demande": "on"})
verifier("demande valide acceptée (redirection)", code == 200 and "bien arrivé" in corps,
         f"code reçu {code}")

print()
print("=" * 74)
print("  ESPACE D'ADMINISTRATION")
print("=" * 74)
code, entetes = appel_brut("/admin/")
verifier("/admin/ redirige vers la connexion (302 brut)",
         code == 302 and "connexion" in entetes.get("Location", ""),
         f"code reçu {code}, destination {entetes.get('Location', '—')}")

code, _, html = appel("/admin/connexion")
verifier("/admin/connexion accessible", code == 200 and "Administration" in html)

jeton = csrf(html)
code, _, corps = appel("/admin/connexion", "POST", {
    "csrf": jeton, "identifiant": "admin", "mot_de_passe": "mauvais-mot-de-passe"})
verifier("mot de passe erroné rejeté (401)", code == 401, f"code reçu {code}")

# Mot de passe réel, lu depuis le fichier d'identifiants.
m = re.search(r"Mot de passe\s*:\s*(\S+)", open("storage/credentials.txt",
                                             encoding="utf-8").read())
mot_de_passe = m.group(1) if m else None
verifier("identifiants initiaux présents dans storage/credentials.txt", bool(mot_de_passe))

code, _, html = appel("/admin/connexion")
jeton = csrf(html)
code, _, corps = appel("/admin/connexion", "POST", {
    "csrf": jeton, "identifiant": "admin", "mot_de_passe": mot_de_passe})
verifier("connexion réussie et redirection", code == 200 and "Tableau de bord" in corps,
         f"code reçu {code}")

for chemin, attendu, libelle in (
    ("/admin/", "Tableau de bord", "tableau de bord"),
    ("/admin/demandes", "Demandes de devis", "liste des demandes"),
    ("/admin/clients", "Groupe Trans-Commerce", "liste des clients"),
    ("/admin/missions", "AUD-2026-001", "liste des missions"),
    ("/admin/missions/1", "Vulnérabilités de cette mission", "détail d'une mission"),
    ("/admin/vulnerabilites", "Injection SQL", "liste des vulnérabilités"),
    ("/admin/vulnerabilites/1", "Preuve de concept", "fiche de vulnérabilité"),
    ("/admin/retests", "En attente de re-test", "contre-visites"),
    ("/admin/journal", "Journal de traçabilité", "journal"),
    ("/admin/parametres", "Changer le mot de passe", "paramètres"),
):
    code, _, corps = appel(chemin)
    verifier(f"GET {chemin:<28} → {code}",
             code == 200 and attendu.lower() in corps.lower(),
             f"attendu 200 + « {attendu} »")

# Filtres
code, _, corps = appel("/admin/vulnerabilites?severite=critique")
verifier("filtre par sévérité (critique)", code == 200 and "Injection SQL" in corps)
code, _, corps = appel("/admin/vulnerabilites?severite=nimportequoi")
verifier("sévérité invalide ignorée sans erreur", code == 200)
code, _, corps = appel("/admin/demandes?statut=gagne")
verifier("filtre par statut de demande", code == 200)

# Les contrôles 404 ci-dessous exigent une session ouverte : ils sont donc
# exécutés ici, avant la déconnexion du bloc suivant.
for chemin in ("/admin/vulnerabilites/99999", "/admin/missions/99999",
               "/admin/demandes/99999"):
    code, _, _ = appel(chemin)
    verifier(f"GET {chemin:<28} → 404 (session ouverte)", code == 404,
             f"code reçu {code}")

print()
print("=" * 74)
print("  DÉCONNEXION ET PAGES D'ERREUR")
print("=" * 74)
code, _, _ = appel("/admin/deconnexion")
verifier("déconnexion redirige", code == 200)

code, _, corps = appel("/admin/")
verifier("accès admin refusé après déconnexion", "Administration" in corps)

code, _, corps = appel("/page-qui-nexiste-pas")
verifier("page 404 personnalisée", code == 404 and "introuvable" in corps.lower())

code, _, corps = appel("/admin/vulnerabilites/1")
verifier("fiche de vulnérabilité protégée après déconnexion",
         "Administration" in corps and "Preuve de concept" not in corps,
         "la fiche ne doit pas être servie sans session")

print()
print("=" * 74)
reussis = sum(1 for _, ok, _ in resultats if ok)
total = len(resultats)
print(f"  RÉSULTAT : {reussis}/{total} vérifications réussies")
if reussis < total:
    print("\n  ÉCHECS :")
    for nom, ok, detail in resultats:
        if not ok:
            print(f"    - {nom}  ({detail})")
print("=" * 74)
