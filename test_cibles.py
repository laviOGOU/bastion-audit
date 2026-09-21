"""Vérification ciblée des deux points signalés, sans suivi automatique
des redirections et avec une session authentifiée."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5002"


class SansRedirection(urllib.request.HTTPRedirectHandler):
    """Empêche urllib de suivre les redirections : on veut voir le code brut."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def ouvreur(suivre=True, jar=None):
    jar = jar or http.cookiejar.CookieJar()
    gestionnaires = [urllib.request.HTTPCookieProcessor(jar)]
    if not suivre:
        gestionnaires.append(SansRedirection())
    return urllib.request.build_opener(*gestionnaires), jar


def appel(opener, chemin, methode="GET", donnees=None):
    corps = urllib.parse.urlencode(donnees).encode() if donnees else None
    requete = urllib.request.Request(BASE + chemin, data=corps, method=methode)
    if corps:
        requete.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with opener.open(requete, timeout=20) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


print("=" * 74)
print("  1. /admin/ sans session — code BRUT attendu : 302")
print("=" * 74)
op, _ = ouvreur(suivre=False)
code, entetes, _ = appel(op, "/admin/")
print(f"  Code reçu      : {code}")
print(f"  Destination    : {entetes.get('Location', '—')}")
print(f"  Verdict        : {'OK' if code == 302 and 'connexion' in entetes.get('Location', '') else 'ECHEC'}")
print()
print("  → le 200 précédent venait du suivi automatique de la redirection")
print("    par urllib jusqu'à la page de connexion. Comportement correct.")

print()
print("=" * 74)
print("  2. Vulnérabilité inexistante, session AUTHENTIFIÉE — attendu 404")
print("=" * 74)
op, jar = ouvreur(suivre=True)
code, _, html = appel(op, "/admin/connexion")
jeton = re.search(r'name="csrf"\s+value="([^"]+)"', html).group(1)
mot_de_passe = re.search(r"Mot de passe\s*:\s*(\S+)",
                         open("storage/credentials.txt", encoding="utf-8").read()).group(1)
code, _, _ = appel(op, "/admin/connexion", "POST", {
    "csrf": jeton, "identifiant": "admin", "mot_de_passe": mot_de_passe})
print(f"  Connexion      : code {code}")

for chemin, attendu in (("/admin/vulnerabilites/99999", 404),
                        ("/admin/missions/99999", 404),
                        ("/admin/demandes/99999", 404),
                        ("/admin/vulnerabilites/1", 200)):
    code, _, corps = appel(op, chemin)
    verdict = "OK" if code == attendu else "ECHEC"
    print(f"  [{verdict}] GET {chemin:<30} → {code} (attendu {attendu})")

print()
print("=" * 74)
print("  3. Anonymisation : aucune donnée réelle dans les réponses publiques")
print("=" * 74)
op2, _ = ouvreur()
code, _, corps = appel(op2, "/ptass")
fuites = []
for motif, etiquette in (
    ("password", "mot « password »"), ("hash_mdp", "nom de colonne interne"),
    ("storage/", "chemin de fichier interne"), ("sqlite", "mention de la base"),
    ("credentials", "fichier d'identifiants"), ("Traceback", "trace d'exception"),
):
    if motif.lower() in corps.lower():
        fuites.append(etiquette)
print(f"  Recherche de fuites sur /ptass : {fuites if fuites else 'aucune'}")
print(f"  Verdict : {'OK' if not fuites else 'ECHEC'}")
print("=" * 74)
