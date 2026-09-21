"""
reinitialiser_acces.py — régénère le mot de passe d'administration.

Utile dans deux cas :
  - le fichier storage/credentials.txt a été supprimé ou perdu ;
  - vous êtes bloqué dehors parce que la limitation de tentatives a verrouillé
    votre propre adresse IP.

Le script écrit un nouveau mot de passe aléatoire dans
storage/credentials.txt et remet à zéro le compteur de tentatives.

Usage :
    .venv/Scripts/python.exe reinitialiser_acces.py
    .venv/Scripts/python.exe reinitialiser_acces.py --mot-de-passe "ma phrase de passe"
"""
import os
import secrets
import sys

from werkzeug.security import generate_password_hash

import config
# Ce script est un outil de developpement : il manipule le fichier
# SQLite avec du SQL brut, donc il vise ce moteur explicitement.
import db_sqlite as db


def main() -> int:
    db.initialiser()

    mot_de_passe = None
    if "--mot-de-passe" in sys.argv:
        index = sys.argv.index("--mot-de-passe") + 1
        if index < len(sys.argv):
            mot_de_passe = sys.argv[index]
    if mot_de_passe is not None and len(mot_de_passe) < config.LONGUEUR_MIN_MOT_DE_PASSE:
        print(f"  Refusé : le mot de passe doit contenir au moins "
              f"{config.LONGUEUR_MIN_MOT_DE_PASSE} caractères.")
        return 1
    if mot_de_passe is None:
        mot_de_passe = secrets.token_urlsafe(15)

    avec_le_compte = db.utilisateur("admin")
    if avec_le_compte:
        db.maj_mot_de_passe("admin", generate_password_hash(mot_de_passe))
        action = "mot de passe régénéré"
    else:
        db.creer_utilisateur("admin", generate_password_hash(mot_de_passe))
        action = "compte admin recréé"

    with db.connect() as conn:
        bloquees = conn.execute("DELETE FROM tentatives").rowcount

    chemin = os.path.join(config.STORAGE_DIR, "credentials.txt")
    os.makedirs(config.STORAGE_DIR, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("Espace d'administration BASTION\n")
        f.write("=" * 46 + "\n\n")
        f.write("  Adresse      : http://127.0.0.1:%s/admin/connexion\n"
                % (os.environ.get("AUDIT_PORT", 5002)))
        f.write("  Identifiant  : admin\n")
        f.write("  Mot de passe : %s\n\n" % mot_de_passe)
        f.write("Changez ce mot de passe à la première connexion\n")
        f.write("(Admin > Paramètres), puis supprimez ce fichier.\n")
        f.write("Ce fichier n'est jamais publié : storage/ est ignoré par Git.\n")

    db.journaliser("acces_reinitialise", action)
    print(f"  {action.capitalize()}.")
    print(f"  {bloquees} tentative(s) de connexion oubliée(s) : "
          f"le verrouillage est levé.")
    print(f"  Identifiants écrits dans : {chemin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
