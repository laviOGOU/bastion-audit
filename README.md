# BASTION

**Site de test d'intrusion et d'audit de sécurité** — présentation des prestations,
portail de suivi des vulnérabilités (PTaaS), espace d'administration privé et base
de données.

---

## 1. Nom du projet

**BASTION** — *Audit & test d'intrusion*.

Application web Python (Flask) conçue pour présenter une offre de test d'intrusion
et d'audit de sécurité, et pour outiller le suivi des vulnérabilités découvertes
chez les clients. Le nom, l'adresse de contact et les coordonnées se modifient en
un seul endroit : le fichier `config.py`.

---

## 2. Problème résolu

Un cabinet d'audit se heurte à deux difficultés opposées, et un site qui n'en
traite qu'une seule rate l'autre.

**Le problème de la crédibilité.** Une direction des systèmes d'information ne
confie pas un test d'intrusion — c'est-à-dire un accès autorisé au cœur de son
système — sur la base d'une page vitrine. Elle veut connaître les référentiels
appliqués, la nature exacte des tests menés, ce qui se passe en cas de découverte
critique, et ce qui ne sera *pas* testé. Sans ces réponses écrites, la discussion
ne s'engage pas.

**Le problème du suivi.** Un rapport d'audit livré sous forme de document se
périme le jour même. Les vulnérabilités restent ouvertes, personne ne sait qui
corrige quoi ni pour quand, et la contre-visite — la seule étape qui prouve
qu'une faille est fermée — n'a pas de canal pour être demandée.

**Ce que fait BASTION.** Le site traite les deux : il expose publiquement tout ce
qu'un décideur doit vérifier avant de signer, et il fournit un espace de suivi où
chaque vulnérabilité porte un statut, un responsable, une échéance et une
demande de contre-visite. À cela s'ajoute une règle de fond : **aucune
certification n'est revendiquée sans être détenue.** La page « Conformité »
affiche le statut réel de chaque certification, y compris « projetée ».

---

## 3. Fonctionnalités

### Site public

- **Accueil** — positionnement, engagements, chiffres clés, aperçu du périmètre.
- **Périmètre d'expertise et méthodologies** — cinq périmètres de test (web, API
  REST et GraphQL, mobile iOS/Android, cloud AWS/Azure/GCP, réseaux et Active
  Directory), référentiels appliqués, déroulé en six phases, méthode de double
  cotation (technique et métier), et **limites annoncées** de l'analyse.
- **Conformité et accréditations** — statut réel de six certifications
  (OSCP, CEH, eWPTX, ISO 27001 LI, OSEP, CISSP) marqué *obtenue*, *en préparation*
  ou *projetée* ; accompagnement RGPD, ISO 27001, PCI-DSS, SOC 2 et NIS 2 ;
  encadré explicite « ce que nous ne revendiquons pas ».
- **Livrables** — les quatre livrables de chaque mission (synthèse exécutive,
  rapport technique, suivi des corrections, attestation de re-test), extrait d'une
  fiche de constat réelle, trois formules commerciales.
- **Portail de suivi PTaaS** — démonstration publique : indicateurs, répartition
  par sévérité, journal des constats, suivi des missions.
- **Vérifier une dépendance** — outil public qui interroge en direct l'API **OSV**
  et affiche les vulnérabilités connues d'un paquet, par écosystème et par version.
- **Transparence éthique et légale** — déroulé de la confidentialité, cinq
  engagements écrits, cadre légal appliqué, liste de ce qui ne sera jamais fait.
- **Divulgation responsable** — politique complète et fichier
  `/.well-known/security.txt` conforme à la RFC 9116.
- **Demande de devis** — formulaire validé côté serveur, option de signature de
  l'accord de confidentialité en amont, enregistrement en base avec référence.
- **Rapport d'exemple anonymisé** — document Word téléchargeable, montrant la
  structure à deux niveaux (synthèse exécutive et partie technique avec preuves
  de concept et remédiations).

### Espace d'administration (privé)

- **Tableau de bord** — demandes à traiter, missions actives, vulnérabilités
  ouvertes, contre-visites en attente, alerte sur les vulnérabilités critiques
  ou élevées encore ouvertes.
- **Demandes de devis** — liste, filtre par statut, fiche détaillée, notes
  internes, réponse par courriel pré-remplie.
- **Clients et missions** — chaque mission porte une référence, un périmètre, un
  référentiel et sa période.
- **Vulnérabilités** — liste filtrable par sévérité et par statut, fiche complète
  (description, impact, preuve de concept, correctif attendu, historique des
  contre-visites), changement de statut, demande de contre-visite.
- **Contre-visites** — file d'attente et historique ; la validation enregistre le
  résultat de la vérification et clôt la vulnérabilité.
- **Journal de traçabilité** — horodatage de toute action sensible : connexions,
  échecs de connexion, rejets de jeton, changements de statut, modifications de
  mot de passe.
- **Paramètres** — changement de mot de passe et état de l'instance.

### Sécurité de l'application elle-même

Un site qui vend des tests d'intrusion doit être exemplaire sur sa propre surface.

- Politique de sécurité du contenu (CSP) restrictive, sans script externe ;
- protection CSRF sur **toutes** les requêtes modifiant l'état ;
- limitation des tentatives de connexion (5 par IP et par tranche de 15 minutes) ;
- mots de passe hachés (Werkzeug), longueur minimale de 12 caractères ;
- cookie de session `HttpOnly`, `SameSite=Lax`, `Secure` en hébergement ;
- en-têtes `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`,
  `Permissions-Policy`, `Cross-Origin-Opener-Policy` ;
- refus des redirections vers une URL externe après connexion ;
- requêtes SQL entièrement paramétrées ;
- neutralisation des balises dans toutes les entrées utilisateur ;
- `Cache-Control: no-store` sur les pages d'administration ;
- aucune trace d'exception exposée au visiteur.

---

## 4. Technologies utilisées

| Composant | Technologie | Version |
|---|---|---|
| Langage | Python | 3.11 |
| Cadre web | Flask | 3.1.3 |
| Base de données | SQLite (module `sqlite3` de la bibliothèque standard) | 3 |
| Moteur de gabarits | Jinja2 (fourni avec Flask) | 3.1 |
| Hachage des mots de passe | Werkzeug Security (scrypt / PBKDF2) | 3.1 |
| Génération de documents | python-docx | 1.1+ |
| Fond animé | Canvas HTML5, JavaScript sans dépendance | — |
| Feuilles de style | CSS écrit à la main, variables CSS, aucune bibliothèque | — |
| Polices | Space Grotesk, Figtree, JetBrains Mono (Google Fonts) | — |
| Captures d'écran | Chrome headless + protocole CDP (`websockets`) | — |
| Gestion d'environnement | `uv` (environnement virtuel + dépendances) | 0.12 |

Aucune dépendance JavaScript externe n'est chargée : le fond animé, la bascule de
thème et les compteurs sont écrits en JavaScript natif. C'est une contrainte de
sécurité autant que de sobriété — moins de code tiers, moins de surface d'attaque.

---

## 5. API utilisée

### API OSV — Open Source Vulnerabilities

- **Fournisseur** : Google
- **Adresse** : `https://api.osv.dev/v1/query`
- **Documentation** : <https://google.github.io/osv.dev/api/>
- **Authentification** : aucune (API publique et gratuite)
- **Usage dans l'application** : page **« Vérifier une dépendance »**
- **Implémentation** : `providers/osv.py`

**Ce que fait l'appel.** Le visiteur choisit un écosystème (npm, PyPI, Maven, Go,
crates.io, NuGet, Packagist, RubyGems, Pub, Hex), saisit un nom de paquet et,
facultativement, une version. L'application envoie une requête POST JSON à OSV et
reçoit la liste des avis de sécurité publiés pour ce paquet et cette version.

**Ce que l'application fait des données.** Le module normalise chaque avis :

- identifiant OSV et alias (ex. `GHSA-29mw-wpgm-hmr9`) ;
- gravité, déduite de `database_specific.severity` et, à défaut, du vecteur CVSS ;
- **première version corrigée** extraite de `affected[].ranges[].events[].fixed` ;
- date de publication et lien vers l'avis d'origine.

Les résultats sont triés de la gravité la plus forte à la plus faible, puis
affichés avec une pastille de sévérité. Un compteur distingue les avis de gravité
critique ou élevée. Chaque appel est journalisé dans le journal de traçabilité.

**Gestion des erreurs.** L'API est un service externe : son indisponibilité ne
doit pas se transformer en erreur 500. Le module lève une exception dédiée,
capturée par la route, qui affiche un message explicite au visiteur. Les codes
d'erreur HTTP autres que 400, les délais dépassés et les réponses illisibles sont
traités séparément. Le délai d'attente est fixé à 20 secondes.

**Exemple vérifié pendant la mise au point** :

```
npm : lodash 4.17.11   →  7 avis, dont GHSA-29mw-wpgm-hmr9 (ReDoS), corrigé en 4.17.12
PyPI : requests 2.31.0 →  6 avis, dont 3 de gravité élevée, corrigés en 2.32.4
PyPI : flask 3.1.3     →  0 avis
```

**Limite assumée.** Aucun avis ne ne signifie pas *aucune vulnérabilité*. La page
le dit explicitement au visiteur : une faille non encore publiée, ou non couverte
par les sources agrégées, n'apparaîtra pas. Et savoir qu'une faille existe ne dit
pas si elle est exploitable dans le contexte du visiteur — c'est précisément le
travail de l'audit.

---

## 6. Installation

### Prérequis

- Python 3.10 ou supérieur
- `uv` (recommandé) ou `pip`

### Mise en place

```bash
cd D:\PYTHON\audit-securite

# Créer l'environnement virtuel et installer les dépendances
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

# Remplir la base avec des données de démonstration (facultatif)
.venv/Scripts/python.exe seed.py

# Générer le rapport d'exemple téléchargeable
.venv/Scripts/python.exe generate_rapport.py

# Lancer le site
.venv/Scripts/python.exe app.py
```

Le site répond alors sur **<http://127.0.0.1:5002>**.

### Premier démarrage

Au premier lancement, un compte d'administration est créé automatiquement et ses
identifiants sont écrits dans `storage/credentials.txt`. Le mot de passe est
aléatoire. **Changez-le dès la première connexion** (Admin → Paramètres), puis
supprimez le fichier.

### Vérifier l'installation

```bash
# 49 vérifications : routes publiques, en-têtes, CSRF, connexion, filtres, 404
.venv/Scripts/python.exe test_routes.py
.venv/Scripts/python.exe test_cibles.py
```

### Captures d'écran

```bash
# Nécessite Google Chrome. Écrit les images dans captures/.
.venv/Scripts/python.exe shots.py
```

---

## 7. Variables d'environnement

Copiez `.env.example` en `.env` et renseignez les valeurs. **Le fichier `.env` ne
doit jamais être versionné** — la règle figure dans `.gitignore`.

| Variable | Obligatoire | Rôle | Valeur par défaut |
|---|---|---|---|
| `AUDIT_SECRET_KEY` | En hébergement | Clé de signature des sessions. À générer avec `python -c "import secrets; print(secrets.token_hex(32))"` | un fichier local `storage/.secret_key` est créé au premier démarrage |
| `AUDIT_STORAGE_DIR` | Non | Emplacement du stockage (base de données et clé). À pointer vers un volume persistant en hébergement | `./storage` |
| `AUDIT_DB_PATH` | Non | Chemin explicite du fichier de base de données | `<storage>/bastion.db` |
| `AUDIT_PORT` | Non | Port d'écoute en local | `5002` |
| `PORT` | Fournie par la plateforme | Variable lue automatiquement : sa présence bascule l'écoute sur `0.0.0.0:$PORT` | absente en local |

Aucun mot de passe, aucune clé d'API tierce n'est présent dans le code. L'API OSV
ne demande pas d'authentification.

---

## 8. Architecture

```
audit-securite/
├── app.py                     Application Flask : routes publiques et admin,
│                              gestion des erreurs, création du compte initial
├── config.py                  Configuration centrale : identité du site,
│                              chemins, réglages de sécurité, détection
│                              d'hébergement par la variable PORT
├── content.py                 Tout le contenu éditorial du site, en un seul
│                              endroit (périmètres, référentiels, phases,
│                              certifications, engagements, formules)
├── db.py                      Schéma SQLite, requêtes paramétrées,
│                              statistiques du tableau de bord
├── security.py                En-têtes HTTP, CSRF, limitation de connexion,
│                              validation des entrées, contrôle de redirection
├── providers/
│   └── osv.py                 Client de l'API OSV : interrogation,
│                              normalisation des avis, gestion des erreurs
├── templates/
│   ├── base.html              Gabarit commun : en-tête, navigation, pied
│   ├── index.html             Accueil
│   ├── expertise.html         Périmètre et méthodologies
│   ├── conformite.html        Accréditations et conformité réglementaire
│   ├── livrables.html         Livrables, extrait de constat, formules
│   ├── ptass.html             Portail de suivi (démonstration publique)
│   ├── verifier.html          Vérification de dépendance (API OSV)
│   ├── ethique.html           Transparence éthique et légale
│   ├── divulgation.html       Politique de divulgation responsable
│   ├── contact.html           Formulaire de demande de devis
│   ├── contact_recu.html      Confirmation d'envoi
│   ├── erreur.html            Pages d'erreur 400/403/404/500
│   └── admin/                 Neuf gabarits de l'espace privé
├── static/
│   ├── css/style.css          Feuille de style unique, thème sombre
│   ├── js/matrix.js           Fond animé « pluie de caractères »
│   ├── js/site.js             Navigation, bascule du fond, compteurs
│   ├── img/favicon.svg        Icône
│   └── rapport/               Rapport d'exemple anonymisé (.docx)
├── storage/                   Base de données, clé de session, identifiants
│                              initiaux — JAMAIS versionné
├── captures/                  Captures d'écran du site
├── seed.py                    Données de démonstration (fictives)
├── generate_rapport.py        Génère le rapport d'exemple en Word
├── shots.py                   Captures d'écran via Chrome headless et CDP
├── test_routes.py             49 vérifications de bout en bout
├── test_cibles.py             Vérifications ciblées (redirection, 404, fuites)
├── requirements.txt
├── Procfile                   Commande de démarrage en hébergement
└── .env.example, .gitignore
```

### Modèle de données

Six tables, toutes reliées par des clés étrangères avec suppression en cascade.

```
utilisateurs ──┐
               │  (authentification de l'espace privé)
tentatives ────┘  (anti-force brute : IP, horodatage, succès)

clients ──< missions ──< vulnerabilites ──< retests
                              │
demandes                      └─ statut, responsable, échéance,
   (demandes de devis)            date de correction

journal  ← toute action sensible, horodatée
```

- `demandes` — demandes de devis reçues, avec statut de traitement.
- `clients` — organisations clientes.
- `missions` — engagements contractuels : référence, périmètre, référentiel,
  période.
- `vulnerabilites` — le cœur du portail : titre, sévérité, score CVSS, CWE,
  catégorie OWASP, description, impact, preuve de concept, correctif attendu,
  statut, responsable, échéance.
- `retests` — contre-visites : date de demande, date de réalisation, résultat.
- `journal` — traçabilité des actions : horodatage, utilisateur, action, détail, IP.

### Cycle de vie d'une vulnérabilité

```
ouverte ──> en_correction ──> (demande de contre-visite) ──> vérification ──> corrigee
   │                                                                           │
   └────────────────────> acceptee (risque assumé, consigné) <─────────────────┘
```

Le passage à `corrigee` n'est possible qu'après enregistrement du résultat de la
contre-visite. C'est ce qui distingue un statut d'une preuve.

### Sécurité de session

- Cookie de session signé avec une clé générée au premier démarrage.
- Jeton CSRF unique par session, comparé en temps constant
  (`hmac.compare_digest`), exigé sur toute requête `POST`, `PUT`, `PATCH` ou
  `DELETE`.
- Limitation par adresse IP : au-delà de 5 échecs en 15 minutes, la connexion est
  refusée et l'événement est journalisé.
- Après connexion, la redirection n'est acceptée que si la cible est un chemin
  interne au site (protection contre la redirection ouverte).
- Session vidée intégralement à la déconnexion.

### Hébergement

Le fichier `Procfile` contient la commande de démarrage. `config.py` détecte la
présence de la variable `PORT` : si elle existe, l'application écoute sur
`0.0.0.0:$PORT`, sinon sur `127.0.0.1:5002`. Aucune modification de code n'est
nécessaire pour passer de l'un à l'autre.

**Attention** : sur la plupart des plateformes, le disque applicatif est éphémère.
Sans volume persistant, la base SQLite est recréée à chaque redéploiement. En
production, définissez `AUDIT_STORAGE_DIR` vers un volume monté, ou remplacez
`db.py` par un client PostgreSQL.

---

## 9. Captures d'écran

Les captures se trouvent dans le dossier `captures/`. Elles ont été prises avec
Chrome headless en 1440 px de large, sur la version locale du site.

### Site public

| Fichier | Page |
|---|---|
| `01_accueil.png` | Accueil — positionnement, engagements, chiffres clés |
| `02_expertise.png` | Périmètre d'expertise et méthodologies |
| `03_conformite.png` | Conformité et accréditations, statut réel des certifications |
| `04_livrables.png` | Livrables, extrait de fiche de constat, formules |
| `05_ethique.png` | Transparence éthique et légale |
| `06_divulgation.png` | Politique de divulgation responsable |
| `07_ptass.png` | Portail de suivi des vulnérabilités (démonstration) |
| `08_contact.png` | Demande de devis |
| `09_connexion_admin.png` | Connexion à l'espace privé |
| `09b_verifier_dependance.png` | Vérification de dépendance — formulaire |
| `09c_verifier_resultat.png` | Résultat d'une vérification OSV (lodash 4.17.11) |

### Espace d'administration

| Fichier | Page |
|---|---|
| `10_admin_tableau_de_bord.png` | Tableau de bord et alerte sur les vulnérabilités graves |
| `11_admin_vulnerabilites.png` | Liste filtrable des vulnérabilités |
| `12_admin_fiche_vulnerabilite.png` | Fiche détaillée avec preuve de concept |
| `13_admin_retests.png` | Contre-visites en attente et historique |
| `14_admin_demandes.png` | Demandes de devis |
| `15_admin_journal.png` | Journal de traçabilité |

`![Accueil](captures/01_accueil.png)`

---

## 10. URL de démonstration

**En local** — c'est l'adresse de référence, l'application y est complète :

- Site public : <http://127.0.0.1:5002>
- Espace d'administration : <http://127.0.0.1:5002/admin/>
- Identifiants : `storage/credentials.txt` (générés au premier démarrage)
- Fichier de divulgation : <http://127.0.0.1:5002/.well-known/security.txt>
- Rapport d'exemple : <http://127.0.0.1:5002/rapport-exemple>

**En hébergement** — le fichier `Procfile` et la détection de la variable `PORT`
sont prêts. Aucun déploiement n'a été effectué à ce jour, faute de compte de
plateforme configuré pour ce projet. La procédure, si vous hébergez :

1. Pousser le dépôt sur GitHub (`.gitignore` protège déjà `.env` et `storage/`) ;
2. Créer un service à partir du dépôt ;
3. Renseigner `AUDIT_SECRET_KEY` dans les variables du service ;
4. Monter un volume persistant et définir `AUDIT_STORAGE_DIR` vers son point de
   montage — sinon la base est perdue à chaque redéploiement ;
5. Au premier déploiement, récupérer le mot de passe dans les journaux ou
   redéfinir un compte.

---

## 11. Test d'intrusion de l'application

Un site qui vend des tests d'intrusion doit accepter d'être testé. L'application
a donc été attaquée pour de vrai, sur l'instance locale, avec de véritables
requêtes HTTP — pas par relecture du code.

**Résultat : 94 attaques simulées, 15 classes, 3 faiblesses trouvées puis
corrigées, 0 vulnérabilité résiduelle.**

| Campagne | Résultat |
|---|---|
| 1re campagne, avant correction | 94 attaques, **3 vulnérabilités** |
| Campagne finale, après correction | 94 attaques, **0 vulnérabilité** |

Les journaux bruts des deux campagnes et le détail attaque par attaque sont
conservés dans `captures/` : `pentest_campagne_1_avant_correction.txt`,
`pentest_campagne_finale_apres_correction.txt`, `rapport_pentest.json`.
Le rapport complet est dans **`RAPPORT-PENTEST-BASTION.docx`**.

### Les trois faiblesses trouvées et corrigées

**1. Énumération de comptes par le temps de réponse** — *faible*.
La vérification du mot de passe n'était exécutée que si l'identifiant existait.
Un compte réel répondait en ~450 ms, un compte inexistant en ~70 ms : cet écart
de **362 ms** permettait de constituer la liste des comptes valides sans jamais
connaître un mot de passe.
*Correctif :* une empreinte factice est vérifiée lorsque l'identifiant n'existe
pas. Écart ramené à **21 ms**, dans le bruit de mesure.

**2. En-tête `Server` divulguant les versions exactes** — *faible*.
Le serveur annonçait `Werkzeug/3.1.8 Python/3.14.7`. Une version exacte de cadre
applicatif désigne directement les vulnérabilités publiques à tenter.
*Correctif :* la version est neutralisée à la source, via une classe de
gestionnaire de requêtes. Poser l'en-tête depuis l'application ne suffisait pas :
le serveur écrit le sien **après** elle. En-tête désormais `Server: BASTION`.

**3. Absence de limitation de débit sur la page d'appel externe** — *moyen*.
La page « Vérifier une dépendance » déclenche une requête sortante vers l'API OSV
à chaque visite, sans aucune limite. Elle pouvait servir d'amplificateur et
épuiser le quota du service tiers au détriment de tous les visiteurs.
*Correctif :* limitation par adresse IP à 20 vérifications par 5 minutes, avec
code 429 et message explicite. 26 requêtes envoyées : **12 refusées, 14 servies**.

### Les défenses qui ont résisté

- **Injection SQL** — 15 charges sur 3 points d'entrée, dont la destruction de
  table et l'union. Toutes les requêtes sont paramétrées.
- **Injection de code (XSS)** — 7 charges via le formulaire public, y compris la
  forme imbriquée `<<script>`. L'échappement automatique tient.
- **CSRF** — 4 variantes refusées en 400, dont un jeton valide provenant d'une
  autre session.
- **Authentification** — limitation à la 6e tentative, cookie falsifié rejeté
  (signature impossible à reproduire sans la clé), identifiant de session
  renouvelé à la connexion (fixation neutralisée).
- **Contrôle d'accès** — les 10 écrans d'administration redirigent sans session,
  sans divulguer la moindre donnée.
- **Traversée de répertoire** — 14 chemins tentés (`.env`, `config.py`, base de
  données, identifiants, variantes encodées) : tous refusés en 404.
- **Divulgation** — console de débogage inaccessible, mode débogage désactivé,
  aucune trace d'exception dans les réponses.
- **En-têtes** — 7 en-têtes présents et corrects ; `script-src 'self'`, sans
  `unsafe-inline` ni domaine externe.
- **Cookie de session** — `HttpOnly` et `SameSite=Lax` présents ; `Secure`
  activé automatiquement en hébergement.
- **Redirection ouverte** — 4 destinations externes refusées, y compris une URL
  relative au protocole et un schéma `javascript:`.

### Deux faux positifs, consignés

Une première version de la campagne a signalé **une politique de contenu
incomplète**. Vérification faite : le test cherchait `unsafe-inline` dans toute la
politique, alors que l'occurrence légitime se trouve dans `style-src`. Après
isolation de la seule directive `script-src` : `script-src 'self'`. Le défaut
était dans le test, pas dans l'application — et il est corrigé.

Le second, une **trace d'exception dans les pages d'erreur**, n'a jamais été
reproduit. Les pages 400, 403, 404 et 500 renvoient un message générique.

### Limites explicites de cette évaluation

Un rapport qui annonce « aucune vulnérabilité » sans nuance est un rapport
malhonnête. Ce qui suit n'a **pas** été testé :

- L'application est testée **par son auteur** : les angles morts de conception
  sont, par nature, invisibles à celui qui les a conçus.
- L'instance tourne sur le **serveur de développement Werkzeug, en HTTP local**.
  Aucun test sur un serveur de production, sur TLS, ou derrière un pare-feu
  applicatif.
- Les attaques réseau de bas niveau (détournement de session, empoisonnement
  DNS) sont hors périmètre d'une évaluation applicative.
- La limitation de débit vit **en mémoire, par processus** : en multi-instance,
  chaque processus compte séparément et il faut un stockage partagé.

### Rejouer la campagne

```bash
.venv/Scripts/python.exe pentest_bastion.py        # attaque l'instance locale
.venv/Scripts/python.exe generate_rapport_pentest.py  # régénère le rapport Word
```

Le script remet à zéro le compteur de tentatives entre les séries de mesures —
sans quoi le verrouillage anti-force-brute fausse les mesures de temps.

---

## Ce que ce projet ne fait pas

Il est utile de l'écrire ici aussi.

- **Aucun certificat de conformité n'est délivré.** Ni RGPD, ni ISO 27001, ni
  PCI-DSS, ni SOC 2, ni NIS 2. Ces documents relèvent d'organismes accrédités.
- **Aucune certification n'est revendiquée.** La page « Conformité » affiche le
  statut réel de chaque certification, en distinguant celles qui sont détenues,
  celles qui sont en préparation et celles qui sont projetées.
- **L'outil de vérification de dépendance n'est pas un audit.** Il consulte une
  base publique d'avis connus. Il ne mesure ni l'atteignabilité du code
  vulnérable, ni le contexte d'exécution, ni les droits effectifs d'un attaquant.
- **Les données de démonstration sont fictives.** Clients, vulnérabilités,
  adresses et extraits de requêtes du jeu de démonstration et du rapport
  d'exemple ont été construits pour l'illustration. Le rapport le mentionne
  explicitement en page de garde.

---

## Licence et usage

Code fourni à titre de démonstration. Les données de démonstration
(`seed.py`, rapport d'exemple) sont fictives et librement réutilisables comme
modèle. Avant tout usage public : remplacer les coordonnées de `config.py`,
changer le mot de passe d'administration, définir `AUDIT_SECRET_KEY`, et
supprimer `storage/credentials.txt`.
