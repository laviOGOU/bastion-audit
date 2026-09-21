-- ===========================================================================
--  BASTION — schéma de base de données pour Supabase (PostgreSQL)
-- ===========================================================================
--  À exécuter une seule fois, dans l'éditeur SQL de votre projet Supabase :
--  Tableau de bord → SQL Editor → New query → coller → Run.
--
--  Les tables sont préfixées « bastion_ » : le projet peut déjà contenir
--  d'autres tables (domain_analyses, par exemple), et rien ne doit entrer en
--  collision avec elles.
--
--  CHOIX ASSUMÉ : les colonnes de date et d'heure sont de type « text » et non
--  « timestamptz ». L'application compare et affiche ces valeurs sous la forme
--  « AAAA-MM-JJ HH:MM:SS ». Conserver ce format évite une conversion dans chaque
--  gabarit et garantit un comportement identique en SQLite (développement local)
--  et sur Supabase (production). La contrepartie est une perte de la validation
--  de type côté base : elle est compensée par le fait que toutes les écritures
--  passent par le code de l'application.
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 1. Comptes d'administration
-- ---------------------------------------------------------------------------
create table if not exists bastion_utilisateurs (
    id            bigserial primary key,
    identifiant   text not null unique,
    hash_mdp      text not null,
    cree_le       text not null,
    dernier_acces text
);

-- ---------------------------------------------------------------------------
-- 2. Tentatives de connexion (limitation de la force brute)
-- ---------------------------------------------------------------------------
create table if not exists bastion_tentatives (
    id          bigserial primary key,
    ip          text not null,
    identifiant text,
    horodatage  text not null,
    succes      integer not null default 0
);
create index if not exists bastion_tentatives_ip_idx
    on bastion_tentatives (ip, horodatage);

-- ---------------------------------------------------------------------------
-- 3. Demandes de devis
-- ---------------------------------------------------------------------------
create table if not exists bastion_demandes (
    id            bigserial primary key,
    cree_le       text not null,
    organisation  text not null,
    contact_nom   text not null,
    contact_email text not null,
    contact_tel   text,
    perimetre     text,
    taille_equipe text,
    message       text,
    nda_demande   integer default 0,
    statut        text not null default 'nouveau',
    notes         text
);
create index if not exists bastion_demandes_statut_idx on bastion_demandes (statut);

-- ---------------------------------------------------------------------------
-- 4. Clients
-- ---------------------------------------------------------------------------
create table if not exists bastion_clients (
    id      bigserial primary key,
    nom     text not null,
    secteur text,
    contact text,
    cree_le text not null
);

-- ---------------------------------------------------------------------------
-- 5. Missions d'audit
-- ---------------------------------------------------------------------------
create table if not exists bastion_missions (
    id          bigserial primary key,
    client_id   bigint references bastion_clients (id) on delete cascade,
    reference   text not null unique,
    perimetre   text,
    referentiel text,
    date_debut  text,
    date_fin    text,
    statut      text not null default 'en_cours',
    cree_le     text not null
);

-- ---------------------------------------------------------------------------
-- 6. Vulnérabilités — le cœur du portail de suivi
-- ---------------------------------------------------------------------------
create table if not exists bastion_vulnerabilites (
    id              bigserial primary key,
    mission_id      bigint references bastion_missions (id) on delete cascade,
    titre           text not null,
    severite        text not null,
    cvss            double precision,
    cwe             text,
    categorie       text,
    description     text,
    impact          text,
    preuve          text,
    remediation     text,
    statut          text not null default 'ouverte',
    responsable     text,
    date_constat    text not null,
    date_echeance   text,
    date_correction text
);
create index if not exists bastion_vulnerabilites_severite_idx
    on bastion_vulnerabilites (severite);
create index if not exists bastion_vulnerabilites_statut_idx
    on bastion_vulnerabilites (statut);

-- ---------------------------------------------------------------------------
-- 7. Contre-visites (re-tests)
-- ---------------------------------------------------------------------------
create table if not exists bastion_retests (
    id         bigserial primary key,
    vuln_id    bigint references bastion_vulnerabilites (id) on delete cascade,
    demande_le text not null,
    realise_le text,
    resultat   text
);

-- ---------------------------------------------------------------------------
-- 8. Journal de traçabilité
-- ---------------------------------------------------------------------------
create table if not exists bastion_journal (
    id         bigserial primary key,
    horodatage text not null,
    utilisateur text,
    action     text not null,
    detail     text,
    ip         text
);
create index if not exists bastion_journal_horodatage_idx
    on bastion_journal (horodatage desc);


-- ===========================================================================
--  SÉCURITÉ — activation du contrôle d'accès au niveau des lignes (RLS)
-- ===========================================================================
--  Sans RLS, toute personne disposant de la clé publique du projet (la clé
--  « anon », qui n'est pas un secret) peut lire, modifier et supprimer
--  l'intégralité de ces tables via l'API REST.
--
--  Le schéma ci-dessous active RLS et n'accorde RIEN au rôle « anon ».
--  L'application doit donc utiliser la clé « service_role », qui contourne RLS
--  et ne doit JAMAIS quitter le serveur (elle ne doit pas être placée dans du
--  JavaScript côté navigateur).
--
--  Si vous ne disposez que de la clé « anon », utilisez le bloc alternatif
--  en fin de fichier — en sachant ce qu'il implique.
-- ===========================================================================

alter table bastion_utilisateurs    enable row level security;
alter table bastion_tentatives      enable row level security;
alter table bastion_demandes        enable row level security;
alter table bastion_clients         enable row level security;
alter table bastion_missions        enable row level security;
alter table bastion_vulnerabilites  enable row level security;
alter table bastion_retests         enable row level security;
alter table bastion_journal         enable row level security;

-- Aucune politique n'est créée pour le rôle « anon » : refus par défaut.
-- Le rôle « service_role » contourne RLS par conception et n'a pas besoin de
-- politique.


-- ===========================================================================
--  VÉRIFICATION
-- ===========================================================================
--  Après exécution, cette requête doit renvoyer 8 lignes, toutes avec
--  rowsecurity = true.
--
--    select tablename, rowsecurity
--      from pg_tables
--     where schemaname = 'public' and tablename like 'bastion_%'
--     order by tablename;
--
-- ===========================================================================


-- ===========================================================================
--  BLOC ALTERNATIF — À N'UTILISER QUE SI VOUS N'AVEZ QUE LA CLÉ « ANON »
-- ===========================================================================
--  Décommentez ce bloc pour que l'application fonctionne avec la clé anonyme.
--
--  ⚠️  CE QUE CELA SIGNIFIE CONCRÈTEMENT
--
--  La clé « anon » est publique par conception : elle est faite pour être
--  exposée dans un navigateur. En l'autorisant sur ces tables, vous acceptez
--  que quiconque récupère cette clé puisse lire, modifier et supprimer vos
--  demandes de devis, vos clients et vos vulnérabilités client.
--
--  Dans notre cas le risque reste contenu, parce que la clé est conservée dans
--  les variables d'environnement du serveur et n'est jamais envoyée au
--  navigateur. Mais c'est une protection par obscurité, pas une sécurité.
--
--  La bonne pratique reste d'ajouter la clé « service_role » dans les variables
--  de la plateforme d'hébergement et de garder ce bloc commenté.
-- ---------------------------------------------------------------------------

-- create policy bastion_anon_select on bastion_demandes
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_demandes
--     for insert to anon with check (true);
-- create policy bastion_anon_update on bastion_demandes
--     for update to anon using (true);
--
-- create policy bastion_anon_select on bastion_clients
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_clients
--     for insert to anon with check (true);
--
-- create policy bastion_anon_select on bastion_missions
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_missions
--     for insert to anon with check (true);
--
-- create policy bastion_anon_select on bastion_vulnerabilites
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_vulnerabilites
--     for insert to anon with check (true);
-- create policy bastion_anon_update on bastion_vulnerabilites
--     for update to anon using (true);
--
-- create policy bastion_anon_select on bastion_retests
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_retests
--     for insert to anon with check (true);
-- create policy bastion_anon_update on bastion_retests
--     for update to anon using (true);
--
-- create policy bastion_anon_select on bastion_journal
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_journal
--     for insert to anon with check (true);
--
-- create policy bastion_anon_select on bastion_utilisateurs
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_utilisateurs
--     for insert to anon with check (true);
-- create policy bastion_anon_update on bastion_utilisateurs
--     for update to anon using (true);
--
-- create policy bastion_anon_select on bastion_tentatives
--     for select to anon using (true);
-- create policy bastion_anon_insert on bastion_tentatives
--     for insert to anon with check (true);
-- create policy bastion_anon_delete on bastion_tentatives
--     for delete to anon using (true);
