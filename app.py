"""
app.py — application Flask du site BASTION.

Deux espaces distincts :
  - le site public : positionnement, périmètre, conformité, livrables, éthique,
    demande de devis, divulgation responsable ;
  - l'espace d'administration, accessible uniquement après connexion, qui porte
    la gestion des demandes, des clients, des missions et des vulnérabilités.
"""
import os
import secrets
from datetime import datetime

from flask import (Flask, abort, flash, make_response, redirect, render_template,
                   request, send_from_directory, session, url_for)
from werkzeug.serving import WSGIRequestHandler
from werkzeug.security import check_password_hash, generate_password_hash

import config
import content
import db
import security
from providers import osv

BASE = os.path.dirname(os.path.abspath(__file__))

# Empreinte factice, utilisée pour égaliser le temps de réponse.
#
# Sans elle, la vérification du mot de passe (scrypt, volontairement lente)
# n'est exécutée que si l'identifiant existe : un compte inexistant répond en
# quelques dizaines de millisecondes, un compte réel en plusieurs centaines.
# Cet écart permet d'énumérer les comptes valides sans jamais connaître un mot
# de passe. En vérifiant toujours une empreinte, même lorsque l'utilisateur
# n'existe pas, on obtient un temps de réponse constant.
_EMPREINTE_FACTICE = generate_password_hash(
    "empreinte-factice-destinee-a-egaliser-le-temps-de-reponse")


class EnteteServeurNeutre(WSGIRequestHandler):
    """Masque la version du serveur et de l'interpréteur.

    Poser l'en-tête depuis l'application ne suffit pas : le serveur de
    développement Werkzeug écrit le sien (« Werkzeug/3.1.8 Python/3.14.7 »)
    au moment d'envoyer la réponse, donc après le passage dans l'application.
    Une version exacte de cadre applicatif désigne directement les
    vulnérabilités publiques à tenter : on la neutralise ici, à la source.
    """

    def version_string(self) -> str:
        return "BASTION"

    def server_version(self) -> str:
        return "BASTION"

    def sys_version(self) -> str:
        return ""


def creer_application() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=config.secret_key(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=config.mode_hebergement(),
        PERMANENT_SESSION_LIFETIME=config.SESSION_DUREE_MINUTES * 60,
        MAX_CONTENT_LENGTH=256 * 1024,
        JSON_SORT_KEYS=False,
    )

    db.initialiser_si_necessaire(app)
    security.installer_en_tetes(app)
    security.proteger_formulaires(app)
    preparer_comptes(app)

    # --- Contexte commun à tous les gabarits --------------------------------
    @app.context_processor
    def _contexte():
        return {
            "site": config,
            "c": content,
            "csrf": security.jeton_csrf,
            "utilisateur": session.get("utilisateur"),
            "annee": datetime.now().year,
            "maintenant": datetime.now(),
            "severites_libelle": db.SEVERITES_LIBELLE,
            "statuts_vuln_libelle": db.STATUTS_VULN_LIBELLE,
            "statuts_demande_libelle": db.STATUTS_DEMANDE_LIBELLE,
        }

    # --- Pages publiques ----------------------------------------------------
    @app.route("/")
    def accueil():
        stats = db.statistiques()
        return render_template("index.html", stats=stats)

    @app.route("/expertise")
    def expertise():
        return render_template("expertise.html")

    @app.route("/conformite")
    def conformite():
        return render_template("conformite.html")

    @app.route("/livrables")
    def livrables():
        return render_template("livrables.html")

    @app.route("/ethique")
    def ethique():
        return render_template("ethique.html")

    @app.route("/divulgation-responsable")
    def divulgation():
        return render_template("divulgation.html")

    @app.route("/ptass")
    def ptass():
        """Démonstration publique du portail de suivi (données fictives)."""
        return render_template(
            "ptass.html",
            vulns=db.vulnerabilites(),
            stats=db.statistiques(),
            missions=db.missions(),
        )

    @app.route("/verifier-dependance")
    def verifier_dependance():
        """Outil public : recherche de vulnérabilités connues via l'API OSV."""
        paquet = security.nettoyer(request.args.get("paquet"), 120)
        ecosysteme = security.nettoyer(request.args.get("ecosysteme"), 40) or "npm"
        version = security.nettoyer(request.args.get("version"), 60)

        resultat = None
        erreur = None
        limite = False

        if paquet:
            # Chaque vérification déclenche une requête sortante vers OSV. Sans
            # limitation, la page sert d'amplificateur et peut épuiser le quota
            # du service tiers au détriment des autres visiteurs.
            if security.limite_debit(
                    f"osv:{security.adresse_ip()}",
                    config.MAX_VERIFICATIONS_DEPENDANCE,
                    config.FENETRE_VERIFICATIONS_MINUTES * 60):
                limite = True
                erreur = (f"Trop de vérifications en peu de temps. Cette limite "
                          f"protège le service public que nous interrogeons : "
                          f"réessayez dans quelques minutes.")
                db.journaliser("verification_limitee", f"{ecosysteme}:{paquet}",
                               ip=security.adresse_ip())
            else:
                try:
                    resultat = osv.interroger(paquet, ecosysteme, version)
                    db.journaliser("verification_dependance",
                                   f"{ecosysteme}:{paquet}@{version or '*'} "
                                   f"→ {resultat['total']} avis",
                                   ip=security.adresse_ip())
                except osv.ErreurOSV as e:
                    erreur = str(e)

        page = render_template("verifier.html", ecosystemes=osv.ECOSYSTEMES,
                               paquet=paquet, ecosysteme=ecosysteme,
                               version=version, resultat=resultat, erreur=erreur,
                               limite=limite)
        return (page, 429) if limite else page

    @app.route("/contact")
    def contact():
        return render_template("contact.html", erreurs=[], donnees={})

    @app.route("/contact", methods=["POST"])
    def contact_envoi():
        donnees, erreurs = security.valider_demande(request.form)
        if erreurs:
            return render_template("contact.html", erreurs=erreurs, donnees=donnees), 400
        identifiant = db.creer_demande(
            donnees["organisation"], donnees["contact_nom"], donnees["contact_email"],
            donnees["contact_tel"], donnees["perimetre"], donnees["taille_equipe"],
            donnees["message"], donnees["nda_demande"],
        )
        db.journaliser("demande_recue",
                       f"#{identifiant} {donnees['organisation']}",
                       ip=security.adresse_ip())
        return redirect(url_for("contact_recu", demande=identifiant))

    @app.route("/contact/recu/<int:demande>")
    def contact_recu(demande):
        return render_template("contact_recu.html", demande=demande)

    # --- Fichiers techniques -------------------------------------------------
    @app.route("/security.txt")
    @app.route("/.well-known/security.txt")
    def security_txt():
        contenu = (
            f"# Politique de divulgation responsable — {config.SITE_NOM}\n"
            f"# Norme : RFC 9116\n"
            f"Contact: mailto:{config.SECURITY_TXT_CONTACT}\n"
            f"Expires: {config.SECURITY_TXT_EXPIRES}\n"
            f"Language: {config.SECURITY_TXT_LANGUES}\n"
            f"Canonical: https://{request.host}/.well-known/security.txt\n"
            f"Policy: https://{request.host}{config.SECURITY_TXT_POLITIQUE}\n"
            f"Preferred-Languages: {config.SECURITY_TXT_LANGUES}\n"
            f"# Nous accusons réception sous 3 jours ouvrés et ne poursuivons pas\n"
            f"# les chercheurs qui respectent notre politique.\n"
        )
        reponse = make_response(contenu)
        reponse.headers["Content-Type"] = "text/plain; charset=utf-8"
        return reponse

    @app.route("/robots.txt")
    def robots():
        contenu = ("User-agent: *\n"
                   "Disallow: /admin\n"
                   "Disallow: /espace-client\n\n"
                   f"Sitemap: https://{request.host}/sitemap.xml\n")
        return make_response(contenu, 200, {"Content-Type": "text/plain; charset=utf-8"})

    @app.route("/sitemap.xml")
    def sitemap():
        pages = ["/", "/expertise", "/conformite", "/livrables", "/ethique",
                 "/ptass", "/contact", "/divulgation-responsable"]
        urls = "".join(
            f"<url><loc>https://{request.host}{p}</loc>"
            f"<changefreq>monthly</changefreq></url>" for p in pages)
        xml = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
               f"{urls}</urlset>")
        return make_response(xml, 200, {"Content-Type": "application/xml"})

    @app.route("/rapport-exemple")
    def rapport_exemple():
        """Téléchargement du rapport d'exemple anonymisé."""
        dossier = os.path.join(BASE, "static", "rapport")
        nom = "BASTION-rapport-exemple-anonymise.docx"
        if not os.path.exists(os.path.join(dossier, nom)):
            abort(404)
        db.journaliser("rapport_telecharge", nom, ip=security.adresse_ip())
        return send_from_directory(dossier, nom, as_attachment=True)

    # --- Espace d'administration --------------------------------------------
    @app.route("/admin/connexion", methods=["GET", "POST"])
    def admin_connexion():
        if security.connexion_autorisee():
            return redirect(url_for("admin_tableau_de_bord"))
        erreur = None
        if request.method == "POST":
            if security.limite_atteinte():
                erreur = (f"Trop de tentatives. Réessayez dans "
                          f"{config.FENETRE_TENTATIVES_MINUTES} minutes.")
                db.journaliser("connexion_bloquee", "limite atteinte",
                               ip=security.adresse_ip())
            else:
                identifiant = security.nettoyer(request.form.get("identifiant"), 80)
                mot_de_passe = request.form.get("mot_de_passe") or ""
                ligne = db.utilisateur(identifiant)

                # On vérifie une empreinte dans tous les cas de figure : celle de
                # l'utilisateur s'il existe, une empreinte factice sinon. Le temps
                # de réponse ne révèle donc pas si le compte existe.
                empreinte = ligne["hash_mdp"] if ligne else _EMPREINTE_FACTICE
                mot_de_passe_valide = check_password_hash(empreinte, mot_de_passe)

                if ligne and mot_de_passe_valide:
                    session.clear()
                    session["utilisateur"] = identifiant
                    session.permanent = True
                    db.enregistrer_tentative(security.adresse_ip(), identifiant, True)
                    db.maj_dernier_acces(identifiant)
                    db.journaliser("connexion_reussie", identifiant,
                                   utilisateur=identifiant, ip=security.adresse_ip())
                    cible = security.destination_sure(session.get("apres_connexion"))
                    return redirect(cible or url_for("admin_tableau_de_bord"))
                db.enregistrer_tentative(security.adresse_ip(), identifiant, False)
                db.journaliser("connexion_echouee", identifiant,
                               ip=security.adresse_ip())
                erreur = "Identifiant ou mot de passe incorrect."
        return render_template("admin/connexion.html", erreur=erreur), \
            (401 if erreur and request.method == "POST" else 200)

    @app.route("/admin/deconnexion")
    def admin_deconnexion():
        utilisateur = session.get("utilisateur")
        if utilisateur:
            db.journaliser("deconnexion", utilisateur, utilisateur=utilisateur,
                           ip=security.adresse_ip())
        session.clear()
        return redirect(url_for("accueil"))

    @app.route("/admin/")
    @security.connexion_requise
    def admin_tableau_de_bord():
        return render_template(
            "admin/tableau_de_bord.html",
            stats=db.statistiques(),
            dernieres=db.demandes()[:6],
            retests=db.retests_demandes(),
            vulns=db.vulnerabilites()[:8],
        )

    @app.route("/admin/demandes")
    @security.connexion_requise
    def admin_demandes():
        statut = request.args.get("statut")
        if statut and statut not in db.STATUTS_DEMANDE:
            statut = None
        return render_template("admin/demandes.html",
                               lignes=db.demandes(statut), filtre=statut)

    @app.route("/admin/demandes/<int:demande_id>", methods=["GET", "POST"])
    @security.connexion_requise
    def admin_demande_detail(demande_id):
        lignes = [d for d in db.demandes() if d["id"] == demande_id]
        if not lignes:
            abort(404)
        if request.method == "POST":
            statut = request.form.get("statut")
            if statut in db.STATUTS_DEMANDE:
                db.maj_statut_demande(demande_id, statut,
                                      security.nettoyer(request.form.get("notes")))
                db.journaliser("demande_maj", f"#{demande_id} -> {statut}",
                               utilisateur=session.get("utilisateur"),
                               ip=security.adresse_ip())
                flash("Demande mise à jour.", "succes")
            return redirect(url_for("admin_demande_detail", demande_id=demande_id))
        return render_template("admin/demande_detail.html", demande=lignes[0])

    @app.route("/admin/clients")
    @security.connexion_requise
    def admin_clients():
        return render_template("admin/clients.html", lignes=db.clients())

    @app.route("/admin/missions")
    @security.connexion_requise
    def admin_missions():
        return render_template("admin/missions.html", lignes=db.missions())

    @app.route("/admin/missions/<int:mission_id>")
    @security.connexion_requise
    def admin_mission_detail(mission_id):
        ligne = db.mission(mission_id)
        if not ligne:
            abort(404)
        return render_template("admin/mission_detail.html", mission=ligne,
                               vulns=db.vulnerabilites(mission_id=mission_id))

    @app.route("/admin/vulnerabilites")
    @security.connexion_requise
    def admin_vulnerabilites():
        severite = request.args.get("severite")
        statut = request.args.get("statut")
        if severite not in db.SEVERITES:
            severite = None
        if statut not in db.STATUTS_VULN:
            statut = None
        return render_template("admin/vulnerabilites.html",
                               lignes=db.vulnerabilites(severite=severite, statut=statut),
                               filtre_severite=severite, filtre_statut=statut)

    @app.route("/admin/vulnerabilites/<int:vuln_id>", methods=["GET", "POST"])
    @security.connexion_requise
    def admin_vuln_detail(vuln_id):
        ligne = db.vulnerabilite(vuln_id)
        if not ligne:
            abort(404)
        if request.method == "POST":
            action = request.form.get("action")
            if action == "statut":
                statut = request.form.get("statut")
                if statut in db.STATUTS_VULN:
                    db.maj_statut_vuln(vuln_id, statut)
                    db.journaliser("vuln_statut", f"#{vuln_id} -> {statut}",
                                   utilisateur=session.get("utilisateur"),
                                   ip=security.adresse_ip())
                    flash("Statut mis à jour.", "succes")
            elif action == "retest":
                db.demander_retest(vuln_id)
                db.journaliser("retest_demande", f"vuln #{vuln_id}",
                               utilisateur=session.get("utilisateur"),
                               ip=security.adresse_ip())
                flash("Contre-visite demandée.", "succes")
            return redirect(url_for("admin_vuln_detail", vuln_id=vuln_id))
        return render_template("admin/vulnerabilite_detail.html", v=ligne,
                               retests=db.retests(vuln_id))

    @app.route("/admin/retests", methods=["GET", "POST"])
    @security.connexion_requise
    def admin_retests():
        if request.method == "POST":
            try:
                retest_id = int(request.form.get("retest_id", 0))
            except ValueError:
                retest_id = 0
            resultat = security.nettoyer(request.form.get("resultat"), 600)
            corrigee = request.form.get("corrigee") == "on"
            if retest_id and resultat:
                db.valider_retest(retest_id, resultat, corrigee)
                db.journaliser("retest_valide", f"#{retest_id}", 
                               utilisateur=session.get("utilisateur"),
                               ip=security.adresse_ip())
                flash("Contre-visite enregistrée.", "succes")
            return redirect(url_for("admin_retests"))
        return render_template("admin/retests.html",
                               en_attente=db.retests_demandes(),
                               historique=db.retests())

    @app.route("/admin/journal")
    @security.connexion_requise
    def admin_journal():
        return render_template("admin/journal.html", lignes=db.journal_recent(120))

    @app.route("/admin/parametres", methods=["GET", "POST"])
    @security.connexion_requise
    def admin_parametres():
        erreur = None
        if request.method == "POST":
            actuel = request.form.get("actuel") or ""
            nouveau = request.form.get("nouveau") or ""
            confirmation = request.form.get("confirmation") or ""
            identifiant = session.get("utilisateur")
            ligne = db.utilisateur(identifiant)
            if not ligne or not check_password_hash(ligne["hash_mdp"], actuel):
                erreur = "Le mot de passe actuel est incorrect."
            elif len(nouveau) < config.LONGUEUR_MIN_MOT_DE_PASSE:
                erreur = (f"Le nouveau mot de passe doit contenir au moins "
                          f"{config.LONGUEUR_MIN_MOT_DE_PASSE} caractères.")
            elif nouveau != confirmation:
                erreur = "Les deux saisies ne correspondent pas."
            else:
                db.maj_mot_de_passe(identifiant, generate_password_hash(nouveau))
                db.journaliser("mot_de_passe_change", identifiant,
                               utilisateur=identifiant, ip=security.adresse_ip())
                flash("Mot de passe modifié.", "succes")
                return redirect(url_for("admin_parametres"))
        return render_template("admin/parametres.html", erreur=erreur), \
            (400 if erreur else 200)

    # --- Gestion des erreurs -------------------------------------------------
    @app.errorhandler(400)
    def e_400(e):
        return render_template("erreur.html", code=400,
                               titre="Requête refusée",
                               message=str(getattr(e, "description",
                                                   "Requête invalide."))), 400

    @app.errorhandler(403)
    def e_403(_):
        return render_template("erreur.html", code=403, titre="Accès refusé",
                               message="Vous n'avez pas les droits nécessaires."), 403

    @app.errorhandler(404)
    def e_404(_):
        return render_template("erreur.html", code=404, titre="Page introuvable",
                               message="Cette adresse n'existe pas ou a été déplacée."), 404

    @app.errorhandler(500)
    def e_500(_):
        return render_template("erreur.html", code=500,
                               titre="Erreur interne",
                               message="Une erreur est survenue. Elle a été "
                                       "enregistrée."), 500

    return app


def preparer_comptes(app) -> None:
    """Crée le compte d'administration au premier démarrage."""
    if db.utilisateur("admin"):
        return
    mot_de_passe = secrets.token_urlsafe(15)
    db.creer_utilisateur("admin", generate_password_hash(mot_de_passe))
    chemin = os.path.join(config.STORAGE_DIR, "credentials.txt")
    os.makedirs(config.STORAGE_DIR, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("Espace d'administration BASTION\n")
        f.write("=" * 46 + "\n\n")
        f.write("  Adresse    : http://127.0.0.1:%s/admin/connexion\n"
                % (os.environ.get("AUDIT_PORT", 5002)))
        f.write("  Identifiant: admin\n")
        f.write("  Mot de passe: %s\n\n" % mot_de_passe)
        f.write("Changez ce mot de passe à la première connexion\n"
                "(Admin > Paramètres). Ce fichier n'est jamais publié.\n")
    db.journaliser("compte_admin_cree", "identifiant admin")
    print("\n  Un compte d'administration a été créé.")
    print("  Identifiants enregistrés dans : %s\n" % chemin)


application = creer_application()

if __name__ == "__main__":
    hote, port = config.adresse_ecoute()
    mode = "hébergement" if config.mode_hebergement() else "local"
    print("=" * 62)
    print(f"  {config.SITE_NOM} — {config.SITE_BASELINE}")
    print("=" * 62)
    print(f"  Mode      : {mode}")
    print(f"  Site      : http://{hote if hote != '0.0.0.0' else '127.0.0.1'}:{port}")
    print(f"  Admin     : http://{hote if hote != '0.0.0.0' else '127.0.0.1'}:{port}/admin/")
    print(f"  Base      : {db.description_moteur()}")
    print("=" * 62 + "\n")
    application.run(host=hote, port=port, debug=False,
                    request_handler=EnteteServeurNeutre)
