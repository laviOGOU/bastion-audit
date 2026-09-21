"""
generate_rapport.py — produit le rapport d'exemple anonymisé (fichier Word).

Ce document est le livrable de démonstration téléchargeable depuis la page
« Livrables ». Il montre la structure en deux niveaux exigée par le cahier des
charges : une synthèse exécutive pour les décideurs, une partie technique avec
preuves de concept et remédiations pour les développeurs.

Toutes les données sont fictives : organisation, adresses, identifiants et
extraits de réponses. Le document est explicitement marqué comme anonymisé.

Usage :
    .venv/Scripts/python.exe generate_rapport.py
"""
import os
from datetime import date, datetime

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SORTIE = os.path.join("static", "rapport", "BASTION-rapport-exemple-anonymise.docx")

VERT = RGBColor(0x0B, 0x6B, 0x4F)
GRIS = RGBColor(0x50, 0x5A, 0x55)
ROUGE = RGBColor(0xB4, 0x23, 0x18)
ORANGE = RGBColor(0xB5, 0x6A, 0x0B)

TITRE = "Rapport de test d'intrusion — exemple anonymisé"
CLIENT = "Exemple-Client (organisation fictive)"
REFERENCE = "AUD-2026-XXX"
PERIODE = "du 3 au 14 mars 2026"
VERSION = "1.0 — exemple de démonstration"


def ombrer(cellule, couleur_hex: str) -> None:
    """Applique un fond gris clair à une cellule de tableau."""
    fond = OxmlElement("w:shd")
    fond.set(qn("w:val"), "clear")
    fond.set(qn("w:fill"), couleur_hex)
    cellule._tc.get_or_add_tcPr().append(fond)


def style_base(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)
    for nom, taille, couleur in (("Heading 1", 17, VERT), ("Heading 2", 13, VERT),
                                 ("Heading 3", 11.5, RGBColor(0x1A, 0x1A, 0x1A))):
        st = doc.styles[nom]
        st.font.name = "Calibri"
        st.font.size = Pt(taille)
        st.font.color.rgb = couleur
        st.font.bold = True


def h(doc, texte, niveau=1):
    return doc.add_heading(texte, level=niveau)


def p(doc, texte, gras=False, italique=False, couleur=None, taille=None):
    paragraphe = doc.add_paragraph()
    run = paragraphe.add_run(texte)
    run.bold = gras
    run.italic = italique
    if couleur:
        run.font.color.rgb = couleur
    if taille:
        run.font.size = Pt(taille)
    return paragraphe


def puce(doc, texte, gras_avant=""):
    paragraphe = doc.add_paragraph(style="List Bullet")
    if gras_avant:
        paragraphe.add_run(gras_avant).bold = True
    paragraphe.add_run(texte)
    return paragraphe


def bloc_code(doc, texte):
    """Bloc monospace encadré, pour les preuves de concept."""
    tableau = doc.add_table(rows=1, cols=1)
    tableau.style = "Table Grid"
    cellule = tableau.rows[0].cells[0]
    ombrer(cellule, "F4F6F5")
    cellule.paragraphs[0].text = ""
    for i, ligne in enumerate(texte.split("\n")):
        paragraphe = cellule.paragraphs[0] if i == 0 else cellule.add_paragraph()
        run = paragraphe.add_run(ligne)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        paragraphe.paragraph_format.space_after = Pt(0)
        paragraphe.paragraph_format.space_before = Pt(0)
    doc.add_paragraph()
    return tableau


def tableau_findings(doc, lignes):
    tableau = doc.add_table(rows=1, cols=6)
    tableau.style = "Table Grid"
    tableau.alignment = WD_TABLE_ALIGNMENT.CENTER
    entetes = ["Réf.", "Constat", "Sévérité", "CVSS", "Impact", "Statut"]
    for i, titre in enumerate(entetes):
        cellule = tableau.rows[0].cells[i]
        cellule.text = ""
        run = cellule.paragraphs[0].add_run(titre)
        run.bold = True
        run.font.size = Pt(8.5)
        ombrer(cellule, "E8EDEB")
    for ligne in lignes:
        cellules = tableau.add_row().cells
        for i, valeur in enumerate(ligne):
            cellules[i].text = ""
            run = cellules[i].paragraphs[0].add_run(str(valeur))
            run.font.size = Pt(8.5)
    return tableau


def fiche(doc, reference, titre, severite, cvss, cwe, categorie, statut,
          description, reproduction, impact, correctif, verification):
    h(doc, f"{reference} — {titre}", 2)

    tableau = doc.add_table(rows=1, cols=4)
    tableau.style = "Table Grid"
    meta = [("Sévérité", severite), ("Score CVSS", cvss),
            ("Classification", cwe), ("Statut", statut)]
    for i, (cle, valeur) in enumerate(meta):
        cellule = tableau.rows[0].cells[i]
        cellule.text = ""
        run = cellule.paragraphs[0].add_run(f"{cle}\n")
        run.font.size = Pt(7.5)
        run.font.color.rgb = GRIS
        run2 = cellule.paragraphs[0].add_run(valeur)
        run2.font.size = Pt(9)
        run2.bold = True
    doc.add_paragraph()

    p(doc, categorie, italique=True, couleur=GRIS, taille=9)
    h(doc, "Description", 3)
    p(doc, description, taille=10)
    h(doc, "Reproduction", 3)
    bloc_code(doc, reproduction)
    h(doc, "Impact démontré", 3)
    p(doc, impact, taille=10)
    h(doc, "Correctif attendu", 3)
    p(doc, correctif, taille=10)
    h(doc, "Vérification", 3)
    p(doc, verification, taille=10, italique=True)


def construire() -> None:
    doc = Document()
    style_base(doc)

    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Cm(2.2)
    section.left_margin = section.right_margin = Cm(2.2)

    # ---------------------------------------------------------------- Couverture
    p(doc, "BASTION", gras=True, couleur=VERT, taille=22)
    p(doc, "Audit & test d'intrusion", couleur=GRIS, taille=11)
    doc.add_paragraph()
    doc.add_paragraph()
    titre = doc.add_paragraph()
    run = titre.add_run(TITRE)
    run.bold = True
    run.font.size = Pt(26)
    run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
    p(doc, "Document de démonstration — données entièrement fictives",
      italique=True, couleur=ROUGE, taille=11)

    doc.add_paragraph()
    informations = doc.add_table(rows=0, cols=2)
    informations.style = "Table Grid"
    for cle, valeur in (
        ("Organisation auditée", CLIENT),
        ("Référence de mission", REFERENCE),
        ("Période d'intervention", PERIODE),
        ("Référentiels appliqués", "OWASP Top 10, OWASP ASVS niveau 2, PTES, NIST SP 800-115"),
        ("Périmètre", "Portail client, tunnel de commande, API publique (v1 et v2)"),
        ("Version du document", VERSION),
        ("Date d'émission", date.today().strftime("%d/%m/%Y")),
        ("Classification", "Confidentiel — diffusion restreinte"),
    ):
        cellules = informations.add_row().cells
        cellules[0].text = ""
        run = cellules[0].paragraphs[0].add_run(cle)
        run.bold = True
        run.font.size = Pt(9)
        ombrer(cellules[0], "F4F6F5")
        cellules[1].text = ""
        cellules[1].paragraphs[0].add_run(valeur).font.size = Pt(9)

    doc.add_paragraph()
    p(doc, "Avertissement", gras=True, taille=10)
    p(doc, "Ce document est un exemple de démonstration. L'organisation, les "
           "adresses, les identifiants, les extraits de requêtes et de réponses "
           "sont entièrement fictifs et ont été construits pour illustrer la "
           "structure d'un rapport réel. Il est publiquement téléchargeable et ne "
           "correspond à aucune mission effectuée.", taille=9.5, couleur=GRIS)

    doc.add_page_break()

    # ------------------------------------------------------- Synthèse exécutive
    h(doc, "1. Synthèse exécutive", 1)
    p(doc, "Ce document s'adresse à la direction et au comité des risques. La "
           "partie technique, destinée aux équipes de développement, commence "
           "au chapitre 4.")

    h(doc, "1.1 Niveau de risque global", 2)
    p(doc, "Le niveau de risque global de l'application auditée est jugé "
           "ÉLEVÉ. Deux vulnérabilités critiques permettent à une personne non "
           "authentifiée d'extraire des données utilisateurs, et le cloisonnement "
           "entre clients n'est pas assuré sur plusieurs points d'entrée.",
      taille=10)

    tableau = doc.add_table(rows=1, cols=4)
    tableau.style = "Table Grid"
    for i, titre_col in enumerate(["Niveau", "Nombre", "Délai de correction recommandé",
                                   "Exposition"]):
        cellule = tableau.rows[0].cells[i]
        cellule.text = ""
        run = cellule.paragraphs[0].add_run(titre_col)
        run.bold = True
        run.font.size = Pt(9)
        ombrer(cellule, "E8EDEB")
    for niveau, nombre, delai, exposition in (
        ("Critique", "2", "7 jours", "Données exposées à un visiteur anonyme"),
        ("Élevé", "3", "30 jours", "Compromission de comptes et cloisonnement rompu"),
        ("Moyen", "2", "90 jours", "Facilitation d'attaques, reconnaissance"),
        ("Faible", "1", "Au prochain cycle", "Impact limité sans faille associée"),
    ):
        cellules = tableau.add_row().cells
        for i, valeur in enumerate((niveau, nombre, delai, exposition)):
            cellules[i].text = ""
            run = cellules[i].paragraphs[0].add_run(valeur)
            run.font.size = Pt(9)
            if i == 0 and niveau == "Critique":
                run.bold = True
                run.font.color.rgb = ROUGE
    doc.add_paragraph()

    h(doc, "1.2 Les trois scénarios d'attaque les plus dangereux", 2)
    p(doc, "Ces scénarios ont été reproduits et vérifiés pendant la mission. "
           "Ils décrivent ce qu'un attaquant obtiendrait réellement, sans "
           "connaissance préalable du système.", taille=10)

    for numero, titre_scenario, texte in (
        ("Scénario 1", "Extraction de la base utilisateurs depuis l'extérieur",
         "Un visiteur non authentifié obtient les adresses électroniques et les "
         "empreintes de mots de passe des clients, en quelques minutes, depuis "
         "n'importe quel poste connecté à Internet. Aucune trace n'apparaît dans "
         "les journaux applicatifs."),
        ("Scénario 2", "Lecture des factures d'un autre client",
         "Un client connecté consulte les factures, les coordonnées et "
         "l'historique d'achat de tous les autres clients, en modifiant un "
         "numéro dans l'adresse de la page. Une fuite de données personnelles "
         "au sens du RGPD, avec obligation de notification."),
        ("Scénario 3", "Contournement du contrôle d'accès de l'API mobile",
         "Un compte de niveau standard atteint les dossiers d'un autre service, "
         "pièces jointes comprises, ce qui rompt le cloisonnement prévu par "
         "l'organisation et expose des dossiers confidentiels."),
    ):
        h(doc, f"{numero} — {titre_scenario}", 3)
        p(doc, texte, taille=10)

    h(doc, "1.3 Impact pour l'activité", 2)
    puce(doc, "exposition à une notification de violation de données et à une "
              "sanction administrative, pour les scénarios 1 et 2 ;",
         "Conformité : ")
    puce(doc, "perte de confiance des clients professionnels, dont certains "
              "exigent contractuellement un niveau de sécurité démontré ;",
         "Réputation : ")
    puce(doc, "aucune interruption de service observée, mais le scénario 1 "
              "permet la récupération des empreintes de mots de passe, qui "
              "conduit souvent à une compromission de comptes sur d'autres "
              "services, par réutilisation.", "Exploitation : ")

    h(doc, "1.4 Décisions attendues", 2)
    tableau = doc.add_table(rows=1, cols=3)
    tableau.style = "Table Grid"
    for i, titre_col in enumerate(["Priorité", "Action", "Effort estimé"]):
        cellule = tableau.rows[0].cells[i]
        cellule.text = ""
        run = cellule.paragraphs[0].add_run(titre_col)
        run.bold = True
        run.font.size = Pt(9)
        ombrer(cellule, "E8EDEB")
    for priorite, action, effort in (
        ("Immédiat", "Paramétrer les requêtes SQL du catalogue et contrôler la "
                     "propriété des objets côté serveur", "2 à 3 jours de développement"),
        ("7 jours", "Limiter le débit sur l'authentification et raccourcir la "
                    "durée de vie des jetons de session", "1 à 2 jours"),
        ("30 jours", "Revoir les droits du compte de base et ajouter les en-têtes "
                     "de sécurité", "1 demi-journée"),
        ("Trimestre", "Prévoir des tests d'autorisation automatisés dans la "
                      "chaîne d'intégration continue", "3 à 5 jours, une fois"),
    ):
        cellules = tableau.add_row().cells
        for i, valeur in enumerate((priorite, action, effort)):
            cellules[i].text = ""
            run = cellules[i].paragraphs[0].add_run(valeur)
            run.font.size = Pt(9)
            if i == 0:
                run.bold = True
    doc.add_paragraph()

    h(doc, "1.5 Ce que la mission n'a pas couvert", 2)
    p(doc, "Cette section est indispensable à la lecture du rapport. L'absence "
           "de faille sur un point non testé ne signifie pas que ce point est "
           "sain.", taille=10)
    puce(doc, "les applications mobiles iOS et Android, hors périmètre contractuel ;")
    puce(doc, "l'infrastructure réseau interne et l'annuaire, non inclus ;")
    puce(doc, "les composants tiers hébergés par des prestataires (paiement, "
              "messagerie), dont le test nécessite leur autorisation ;")
    puce(doc, "les tests de charge et de déni de service, exclus pour ne pas "
              "perturber la production.")

    doc.add_page_break()

    # ------------------------------------------------------------ Périmètre
    h(doc, "2. Périmètre et déroulement", 1)
    h(doc, "2.1 Périmètre autorisé", 2)
    p(doc, "Le test a été conduit exclusivement sur les cibles listées dans "
           "l'autorisation écrite signée le 28 février 2026. Toute cible non "
           "listée ci-dessous est hors périmètre.", taille=10)
    puce(doc, "portail client — https://portail.exemple-client.ci ;")
    puce(doc, "tunnel de commande — parcours complet, du panier au paiement ;")
    puce(doc, "API publique — https://api.exemple-client.ci, versions v1 et v2 ;")
    puce(doc, "comptes de test fournis : trois comptes clients de niveaux "
              "différents, un compte administrateur de démonstration.")

    h(doc, "2.2 Fenêtres d'intervention et précautions", 2)
    p(doc, "Les tests ont été menés entre 22 h et 6 h GMT, afin de limiter "
           "l'impact sur la production. Aucune donnée métier n'a été copiée : "
           "les preuves se limitent aux extraits nécessaires à la démonstration, "
           "et les données personnelles y sont tronquées.", taille=10)

    h(doc, "2.3 Phases", 2)
    for titre_phase, duree, contenu in (
        ("Cadrage", "2 jours", "Définition du périmètre, des comptes de test et "
                               "des exclusions. Signature de l'autorisation."),
        ("Reconnaissance", "2 jours", "Cartographie des sous-domaines, des "
                                      "services exposés et des technologies."),
        ("Analyse", "5 jours", "Recherche de vulnérabilités, revue de "
                               "configuration, analyse du contrôle d'accès."),
        ("Exploitation", "3 jours", "Consolidation en scénarios d'attaque et "
                                    "mesure de l'impact réel."),
        ("Restitution", "2 jours", "Rapport à deux niveaux et séance de "
                                   "restitution orale."),
    ):
        paragraphe = doc.add_paragraph()
        run = paragraphe.add_run(f"{titre_phase} ({duree}) — ")
        run.bold = True
        run.font.size = Pt(10)
        paragraphe.add_run(contenu).font.size = Pt(10)

    doc.add_page_break()

    # ------------------------------------------------------------ Synthèse technique
    h(doc, "3. Synthèse des constats", 1)
    p(doc, "Huit constats ont été identifiés. Ils sont détaillés au chapitre 4 "
           "et suivis dans le portail client, où chaque correction peut donner "
           "lieu à une demande de contre-visite.", taille=10)

    tableau_findings(doc, [
        ("C-01", "Injection SQL dans la recherche du catalogue", "Critique", "9.1", "Extraction de la base", "Corrigée"),
        ("C-02", "Contrôle d'accès horizontal sur les factures", "Critique", "8.6", "Fuite de données clients", "Corrigée"),
        ("C-03", "Absence de limitation de débit à l'authentification", "Élevé", "7.5", "Force brute", "En correction"),
        ("C-04", "Autorisation objet absente sur l'API", "Élevé", "8.1", "Cloisonnement rompu", "Ouverte"),
        ("C-05", "Jeton de session non invalidé à la déconnexion", "Élevé", "7.1", "Réutilisation de session", "En correction"),
        ("C-06", "Composant frontal obsolète", "Moyen", "5.9", "Exploitation connue", "Ouverte"),
        ("C-07", "Messages d'erreur révélant la pile technique", "Moyen", "5.3", "Reconnaissance", "Ouverte"),
        ("C-08", "Divulgation par en-têtes de version", "Faible", "3.1", "Reconnaissance", "Acceptée"),
    ])
    doc.add_paragraph()
    p(doc, "Les références « C-0x » sont celles utilisées dans le portail de "
           "suivi, afin que vos équipes retrouvent immédiatement le constat "
           "correspondant.", italique=True, couleur=GRIS, taille=9)

    doc.add_page_break()

    # ------------------------------------------------------------ Partie technique
    h(doc, "4. Constats détaillés", 1)
    p(doc, "Cette partie s'adresse aux équipes techniques. Chaque constat "
           "comporte une description, les étapes de reproduction, l'impact "
           "démontré et le correctif attendu. Les extraits sont issus de "
           "l'environnement de test et ont été anonymisés.", taille=10)

    fiche(
        doc, "C-01", "Injection SQL dans le paramètre de recherche du catalogue",
        "Critique", "9.1", "CWE-89 · A03:2021 — Injection", "OWASP Top 10",
        "Corrigée",
        "Le paramètre « recherche » de l'endpoint public /catalogue est concaténé "
        "directement dans la requête SQL, sans requête paramétrée ni validation. "
        "Un guillemet non échappé permet de modifier la clause WHERE et de faire "
        "porter la requête sur une autre table.",
        "GET /catalogue?recherche=x%27%20UNION%20SELECT%20null,email,hash_mdp"
        "%20FROM%20utilisateurs--%20\n"
        "Host: portail.exemple-client.ci\n\n"
        "HTTP/1.1 200 OK\n"
        "Content-Type: application/json\n\n"
        "{ \"resultats\": [ ... ], \"total\": 412 }\n\n"
        "→ les 412 lignes renvoyées contiennent les adresses électroniques et\n"
        "  les empreintes de mots de passe des utilisateurs.",
        "Un visiteur non authentifié extrait l'intégralité de la base "
        "utilisateurs. Les empreintes, obtenues sans limitation de débit, "
        "peuvent être attaquées hors ligne. Aucune entrée n'apparaît dans les "
        "journaux applicatifs : la tentative est indétectable.",
        "Utiliser des requêtes paramétrées sur l'ensemble des points d'entrée du "
        "catalogue. Valider en liste blanche les colonnes de tri et de filtre. "
        "Restreindre les droits du compte de base de données aux seules tables "
        "nécessaires, en lecture seule lorsque c'est possible.",
        "Requête rejouée après correction : la réponse est revenue à son "
        "comportement normal, sans fuite. Statut corrigé confirmé par "
        "contre-visite, vérification effectuée le 12 mars 2026.",
    )

    fiche(
        doc, "C-04", "Autorisation au niveau objet absente sur l'API",
        "Élevé", "8.1", "CWE-284 · API01:2023 — Autorisation au niveau objet",
        "OWASP API Top 10", "Ouverte",
        "Les endpoints /api/v2/dossiers/{id} vérifient le rôle de l'appelant "
        "mais pas la propriété de l'objet demandé. Un identifiant d'un autre "
        "service est traité sans contrôle supplémentaire.",
        "GET /api/v2/dossiers/8830 HTTP/1.1\n"
        "Host: api.exemple-client.ci\n"
        "Authorization: Bearer <jeton d'un compte standard, service A>\n\n"
        "HTTP/1.1 200 OK\n\n"
        "{ \"id\": 8830, \"service\": \"service-B\", \"pieces_jointes\": [ ... ] }\n\n"
        "→ le dossier appartient au service B ; il est renvoyé intégralement,\n"
        "  pièces jointes comprises.",
        "Rupture du cloisonnement entre services : un compte de niveau standard "
        "accède à des dossiers qui ne lui sont pas destinés. Le contrôle "
        "d'accès n'est pas seulement insuffisant, il donne une fausse assurance "
        "puisqu'un contrôle de rôle existe et passe.",
        "Contrôler la propriété de chaque objet côté serveur, en dérivant "
        "l'appartenance du jeton d'authentification et jamais d'un paramètre de "
        "la requête. Ajouter des tests d'autorisation automatisés dans la chaîne "
        "d'intégration, sur au moins deux comptes distincts par endpoint.",
        "Constante ouverte à la date d'émission du rapport. Une contre-visite "
        "est disponible dès que la correction est déployée : la demande se fait "
        "depuis le portail de suivi, sans frais supplémentaires.",
    )

    fiche(
        doc, "C-08", "Divulgation d'information par les en-têtes de réponse",
        "Faible", "3.1", "CWE-200 · A05:2021 — Mauvaise configuration",
        "OWASP Top 10", "Acceptée",
        "Les en-têtes de réponse du portail exposent le serveur applicatif, sa "
        "version exacte et le système d'exploitation sous-jacent.",
        "HTTP/1.1 200 OK\n"
        "Server: <serveur>/<version exacte> (<système>)\n"
        "X-Powered-By: <cadre applicatif>/<version>\n\n"
        "→ la version exacte permet de cibler des vulnérabilités publiques.",
        "Impact limité en lui-même : il s'agit d'une aide à la reconnaissance. "
        "Le risque devient réel lorsque la version exposée correspond à une "
        "vulnérabilité publique connue et non corrigée.",
        "Masquer les en-têtes de version au niveau du serveur frontal. Ne jamais "
        "exposer de numéro de version dans une réponse publique.",
        "Constat accepté par le client : la correction est planifiée au prochain "
        "cycle de mise à jour de l'infrastructure. Le risque résiduel est "
        "consigné et suivi dans le portail.",
    )

    doc.add_page_break()

    # ------------------------------------------------------------ Re-test
    h(doc, "5. Attestation de contre-visite", 1)
    p(doc, "Les constats ci-dessous ont fait l'objet d'une contre-visite : "
           "l'exploitation a été rejouée après correction, et son échec a été "
           "constaté. Cette attestation ne couvre que les points listés.", taille=10)

    tableau = doc.add_table(rows=1, cols=4)
    tableau.style = "Table Grid"
    for i, titre_col in enumerate(["Réf.", "Constat", "Vérifié le", "Résultat"]):
        cellule = tableau.rows[0].cells[i]
        cellule.text = ""
        run = cellule.paragraphs[0].add_run(titre_col)
        run.bold = True
        run.font.size = Pt(9)
        ombrer(cellule, "E8EDEB")
    for reference_c, constat, verifie, resultat in (
        ("C-01", "Injection SQL dans la recherche", "12/03/2026",
         "Exploitation rejouée : échec. Requêtes paramétrées effectives."),
        ("C-02", "Contrôle d'accès horizontal sur les factures", "15/03/2026",
         "Six identifiants d'autres comptes testés : tous refusés."),
    ):
        cellules = tableau.add_row().cells
        for i, valeur in enumerate((reference_c, constat, verifie, resultat)):
            cellules[i].text = ""
            run = cellules[i].paragraphs[0].add_run(valeur)
            run.font.size = Pt(9)
    doc.add_paragraph()

    p(doc, "Limites de cette attestation", gras=True, taille=10)
    p(doc, "Elle porte uniquement sur les deux constats listés, à la date "
           "indiquée. Elle ne constitue ni une certification de conformité, ni "
           "une garantie d'absence de vulnérabilité. Toute modification "
           "ultérieure du code ou de la configuration peut rouvrir les "
           "faiblesses corrigées.", taille=9.5, couleur=GRIS)

    doc.add_paragraph()
    p(doc, "Fin du document — exemple de démonstration.", italique=True,
      couleur=GRIS, taille=9)

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    doc.save(SORTIE)
    taille_ko = os.path.getsize(SORTIE) // 1024
    print(f"  Rapport écrit : {SORTIE}  ({taille_ko} Ko)")
    print(f"  Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")


if __name__ == "__main__":
    construire()
