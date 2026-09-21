"""
shots.py — captures d'écran du site BASTION via Chrome headless et CDP.

Deux pièges rencontrés sur ce poste, tous deux traités ici :
  - Chrome lancé depuis le terminal attend indéfiniment sur l'entrée
    standard : il faut stdin=DEVNULL ;
  - les identifiants de message CDP ne doivent pas reposer sur id(), que
    Python réutilise après libération : on utilise un compteur strictement
    croissant, sinon les réponses se désynchronisent et le script se bloque.

Usage : .venv/Scripts/python.exe -u shots.py
"""
import asyncio
import base64
import json
import os
import re
import subprocess
import urllib.request

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT_DEBUG = 9225
BASE = "http://127.0.0.1:5002"
PROFIL = os.path.join(os.environ["LOCALAPPDATA"], "Temp", "chrome_bastion")
DOSSIER = "captures"
LARGEUR, HAUTEUR = 1440, 900

PAGES = [
    ("01_accueil", "/", 3.5),
    ("02_expertise", "/expertise", 2.0),
    ("03_conformite", "/conformite", 2.0),
    ("04_livrables", "/livrables", 2.0),
    ("05_ethique", "/ethique", 2.0),
    ("06_divulgation", "/divulgation-responsable", 2.0),
    ("07_ptass", "/ptass", 2.0),
    ("08_contact", "/contact", 1.8),
    ("09_connexion_admin", "/admin/connexion", 1.5),
    ("09b_verifier_dependance", "/verifier-dependance", 1.8),
    ("09c_verifier_resultat",
     "/verifier-dependance?ecosysteme=npm&paquet=lodash&version=4.17.11", 6.0),
]

PAGES_ADMIN = [
    ("10_admin_tableau_de_bord", "/admin/", 1.8),
    ("11_admin_vulnerabilites", "/admin/vulnerabilites", 1.8),
    ("12_admin_fiche_vulnerabilite", "/admin/vulnerabilites/1", 1.8),
    ("13_admin_retests", "/admin/retests", 1.8),
    ("14_admin_demandes", "/admin/demandes", 1.8),
    ("15_admin_journal", "/admin/journal", 1.8),
]


class CDP:
    """Petit client CDP : compteur d'identifiants strict et lecture fiable."""

    def __init__(self, ws):
        self.ws = ws
        self.compteur = 0

    async def appeler(self, methode, delai=25, **params):
        self.compteur += 1
        identifiant = self.compteur
        await self.ws.send(json.dumps(
            {"id": identifiant, "method": methode, "params": params}))
        while True:
            brut = await asyncio.wait_for(self.ws.recv(), timeout=delai)
            message = json.loads(brut)
            if message.get("id") == identifiant:
                if "error" in message:
                    raise RuntimeError(f"{methode} : {message['error']}")
                return message.get("result", {})
            # Sinon : événement ou réponse tardive, on l'ignore.

    async def evaluer(self, expression, delai=25):
        resultat = await self.appeler(
            "Runtime.evaluate", delai=delai, expression=expression,
            awaitPromise=True, returnByValue=True)
        return resultat.get("result", {}).get("value")


async def attendre_debug():
    for _ in range(50):
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{PORT_DEBUG}/json/version", timeout=2) as r:
                json.load(r)
                return True
        except Exception:
            await asyncio.sleep(0.4)
    raise RuntimeError("Chrome n'a pas ouvert le port de débogage")


def lancer_chrome():
    os.makedirs(PROFIL, exist_ok=True)
    return subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={PORT_DEBUG}",
         f"--user-data-dir={PROFIL}", f"--window-size={LARGEUR},{HAUTEUR}",
         "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
         "--disable-gpu", "--disable-extensions", "--disable-background-networking",
         "--force-device-scale-factor=1", "about:blank"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


async def capturer(cdp, nom, chemin, attente):
    await cdp.appeler("Page.navigate", url=BASE + chemin)
    await asyncio.sleep(attente)
    # Attend la fin du chargement des polices distantes.
    await cdp.evaluer("document.fonts ? document.fonts.ready.then(() => 1) : 1")
    await asyncio.sleep(0.3)
    hauteur = await cdp.evaluer(
        "Math.min(document.documentElement.scrollHeight, 6000)")
    resultat = await cdp.appeler("Page.captureScreenshot", delai=40,
                                 format="png", captureBeyondViewport=True)
    donnees = resultat.get("data")
    if not donnees:
        print(f"  ECHEC  {nom} — aucune image", flush=True)
        return False
    chemin_complet = os.path.join(DOSSIER, nom + ".png")
    with open(chemin_complet, "wb") as f:
        f.write(base64.b64decode(donnees))
    titre = await cdp.evaluer("document.title")
    print(f"  OK  {nom:<26} {os.path.getsize(chemin_complet)//1024:>5} Ko "
          f"(page {int(hauteur or 0)} px)  {str(titre)[:44]}", flush=True)
    return True


async def main():
    os.makedirs(DOSSIER, exist_ok=True)
    chrome = lancer_chrome()
    try:
        await attendre_debug()
        print("  Chrome connecté.", flush=True)
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT_DEBUG}/json/list") as r:
            cibles = json.load(r)
        ws_url = next(c["webSocketDebuggerUrl"] for c in cibles
                      if c["type"] == "page")

        async with websockets.connect(ws_url, max_size=100 * 1024 * 1024,
                                      open_timeout=20) as ws:
            cdp = CDP(ws)
            await cdp.appeler("Page.enable")
            await cdp.appeler("Runtime.enable")
            # Chrome headless déclare par défaut « prefers-reduced-motion:
            # reduce », ce qui désactive légitimement l'animation du fond.
            # On force la préférence contraire pour capturer la version animée.
            await cdp.appeler(
                "Emulation.setEmulatedMedia",
                features=[{"name": "prefers-reduced-motion",
                           "value": "no-preference"}])
            reduit = await cdp.evaluer(
                "window.matchMedia('(prefers-reduced-motion: reduce)').matches")
            print(f"\n  prefers-reduced-motion: reduce → {reduit}", flush=True)
            await cdp.appeler("Emulation.setDeviceMetricsOverride",
                              width=LARGEUR, height=HAUTEUR, deviceScaleFactor=1,
                              mobile=False)

            print("\n  PAGES PUBLIQUES", flush=True)
            for nom, chemin, attente in PAGES:
                await capturer(cdp, nom, chemin, attente)

            print("\n  CONNEXION ADMINISTRATION", flush=True)
            await cdp.appeler("Page.navigate", url=BASE + "/admin/connexion")
            await asyncio.sleep(1.5)
            mot_de_passe = re.search(
                r"Mot de passe\s*:\s*(\S+)",
                open("storage/credentials.txt", encoding="utf-8").read()).group(1)
            code = await cdp.evaluer(f"""
                (async () => {{
                  const r = await fetch('/admin/connexion', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: new URLSearchParams({{
                      csrf: document.querySelector('input[name=csrf]').value,
                      identifiant: 'admin',
                      mot_de_passe: {json.dumps(mot_de_passe)}
                    }})
                  }});
                  return r.status;
                }})()
            """, delai=40)
            print(f"  Connexion : code {code}", flush=True)

            print("\n  ESPACE D'ADMINISTRATION", flush=True)
            for nom, chemin, attente in PAGES_ADMIN:
                await capturer(cdp, nom, chemin, attente)
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=10)
        except Exception:
            chrome.kill()

    images = sorted(f for f in os.listdir(DOSSIER) if f.endswith(".png"))
    print(f"\n  {len(images)} capture(s) écrite(s) dans {DOSSIER}/", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
