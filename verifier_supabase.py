"""
verifier_supabase.py — diagnostic de la base de données Supabase.

Répond à trois questions, dans cet ordre :
  1. Les variables SUPABASE_URL et SUPABASE_KEY sont-elles définies ?
  2. Le projet répond-il, et la clé est-elle acceptée ?
  3. Les huit tables du schéma existent-elles, et sont-elles accessibles ?

Usage :
    .venv/Scripts/python.exe verifier_supabase.py
"""
import sys

import config

try:
    import db_supabase
except Exception as e:                                   # noqa: BLE001
    print(f"  Import impossible de db_supabase : {type(e).__name__}: {e}")
    sys.exit(1)


def main() -> int:
    print("=" * 74)
    print("  DIAGNOSTIC SUPABASE")
    print("=" * 74)

    print("\n  1. Variables d'environnement")
    print(f"     SUPABASE_URL : {'définie (' + str(len(config.SUPABASE_URL)) + ' caractères)' if config.SUPABASE_URL else 'ABSENTE'}")
    print(f"     SUPABASE_KEY : {'définie (' + str(len(config.SUPABASE_KEY)) + ' caractères)' if config.SUPABASE_KEY else 'ABSENTE'}")
    if not config.MOTEUR_SUPABASE:
        print("\n  → L'application reste sur SQLite : les deux variables doivent")
        print("    être renseignées pour basculer sur Supabase.")
        return 1
    print(f"     Moteur actif : {config.SUPABASE_URL}")

    print("\n  2. Réponse du projet et validité de la clé")
    try:
        rapport = db_supabase.verifier_connexion()
    except db_supabase.ErreurBase as e:
        print(f"     ÉCHEC : {e}")
        return 1

    joignables, manquantes, refusees = [], [], []
    for table, resultat in rapport["tables"].items():
        if isinstance(resultat, int):
            joignables.append((table, resultat))
        elif "n'existe pas" in str(resultat):
            manquantes.append(table)
        else:
            refusees.append((table, str(resultat)[:100]))

    if joignables or manquantes:
        print("     Le projet répond et l'API REST est accessible.")

    print("\n  3. État des huit tables")
    if joignables:
        for table, total in joignables:
            print(f"     [OK]      {table:<28} {total} ligne(s)")
    if manquantes:
        print()
        for table in manquantes:
            print(f"     [ABSENTE] {table}")

    if refusees:
        print()
        for table, message in refusees:
            print(f"     [REFUS]   {table}")
            print(f"               {message}")

    print()
    print("=" * 74)
    if manquantes:
        print("  ACTION REQUISE")
        print("=" * 74)
        print("  Les tables ci-dessus n'existent pas encore. Il faut créer le schéma,")
        print("  une seule fois :")
        print()
        print("    1. Ouvrir https://supabase.com/dashboard et sélectionner le projet")
        print("    2. Menu de gauche → SQL Editor → New query")
        print("    3. Coller l'intégralité du fichier supabase_schema.sql")
        print("    4. Cliquer sur Run")
        print("    5. Relancer ce script : il doit afficher huit tables à 0 ligne")
        print("=" * 74)
        return 2

    if refusees:
        print("  La clé n'a pas les droits nécessaires.")
        print("  Cause la plus probable : le contrôle d'accès par ligne (RLS) est actif")
        print("  sans politique pour le rôle utilisé. Utilisez la clé service_role,")
        print("  ou décommentez le bloc « anon » en fin de supabase_schema.sql.")
        print("=" * 74)
        return 3

    print("  TOUT EST PRÊT")
    print("=" * 74)
    print("  L'application basculera sur Supabase au prochain démarrage.")
    print(f"  {sum(t for _, t in joignables)} ligne(s) au total dans les huit tables.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
