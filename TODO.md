# TODO — Module PWA "CHERE APP INSTALLER"
> Durée avant réaffichage : **1 jour** (configurable depuis l'admin)
> **Code status (2026-07-31)** : 100% implémenté + committé sur `stanionic/chere:main` (commits 7c50bc0 → 031570f → f99e05c)
> Tests unitaires OK : `/api/v1/pwa/config` 200 (defaults+custom), `/api/v1/pwa/install-event` 201, `/api/v1/pwa/stats` 200, popup présent sur 15 routes publiques.

## Phase 1 — Assets et Configuration PWA
- [x] 1.1 Créer le dossier `app/static/pwa/icons/`
- [x] 1.2 Mettre à jour `static/manifest.json` (version complète standalone)
- [x] 1.3 Créer `app/templates/pwa/offline.html`
- [x] 1.4 Route Flask `GET /manifest.json` (blueprint PWA, Content-Type `application/manifest+json`)
- [x] 1.5 Générer 11 icônes maskable PWA (16→512 px) + favicons PNG/ICO via Pillow

## Phase 2 — Service Worker
- [x] 2.1 Mettre à jour `static/sw.js` (service worker complet avec cache stratégique)
- [x] 2.2 Scope `/` + `skipWaiting()` + `clients.claim()` + version `chere-static-v3` / `chere-pages-v3`
- [x] 2.3 Route `/pwa/offline.html` dans blueprint PWA + fallback HTML si template absent

## Phase 3 — JavaScript Intelligent + CSS
- [x] 3.1 Créer `app/static/pwa/install.js` (détection, beforeinstallprompt, iOS guide, localStorage 1 jour)
- [x] 3.2 Créer `app/static/pwa/install.css` (glassmorphism CHERE)
- [x] 3.3 Chargement config admin depuis `/api/v1/pwa/config` (delay + jours + textes custom)
- [x] 3.4 Tracking anonymisé via `sendBeacon` + fallback `fetch(keepalive:true)` → `/api/v1/pwa/install-event`

## Phase 4 — Popup d'Installation
- [x] 4.1 Créer `app/templates/components/install_popup.html`
- [x] 4.2 Guide iOS Safari 3 étapes « Partager → Ajouter à l'écran d'accueil → Ajouter »

## Phase 5 — Base de Données
- [x] 5.1 Ajouter modèle `AppInstallation` dans `app/models.py`
- [x] 5.2 Ajouter modèle `PwaConfig` pour la config admin (délai, texte, 1 jour par défaut)
- [x] 5.3 Server defaults SQLite (`server_default`) pour `PwaConfig.enabled/popup_delay/dismiss_duration_days`

## Phase 6 — Blueprint PWA
- [x] 6.1 Créer `app/blueprints/pwa/__init__.py`
- [x] 6.2 Créer `app/blueprints/pwa/routes.py`
- [x] 6.3 Enregistrer blueprint dans `app/__init__.py`
- [x] 6.4 CSRF exemption sur `/api/v1/pwa/install-event` (sendBeacon n'a pas de cookie CSRF)

## Phase 7 — Administration Mobile
- [x] 7.1 Ajouter `MobileInstallSettingsForm` dans `app/blueprints/admin/forms.py`
- [x] 7.2 Ajouter routes admin pour la config mobile (`/admin/mobile-install` GET/POST)
- [x] 7.3 Créer `app/templates/admin/mobile_install.html`
- [x] 7.4 Mettre à jour `app/templates/admin/base_admin.html` (lien sidebar)
- [x] 7.5 Stats admin inline : propositions/installations/refus + taux de conversion + by_device + 10 derniers events

## Phase 8 — Internationalisation
- [x] 8.1 Ajouter traductions PWA dans `app/i18n.py` (FR/EN)
- [x] 8.2 Clés : `pwa.install_title`, `pwa.install_subtitle`, `pwa.install_button`, `pwa.later_button`, `pwa.ios_step_1/2/3`, `pwa.ios_share`, `pwa.ios_add_to_home`, `pwa.ios_add`

## Phase 9 — Templates et intégration
- [x] 9.1 Mettre à jour `app/templates/base.html` (inclure popup + scripts PWA)
- [x] 9.2 Intégration dans templates standalone non-`extends base.html` :
  - [x] 9.2.1 `app/templates/barista/index.html`
  - [x] 9.2.2 `app/templates/barista/card.html`
  - [x] 9.2.3 `app/templates/pwa/offline.html`
- [x] 9.3 Pages admin et erreurs 404/500 couvertes via `extends base.html` / `extends base_admin.html`

## Phase 10 — Tests
- [x] 10.1 Créer `tests/test_pwa.py`
- [x] 10.2 Vérifier que l'application démarre sans erreur
- [x] 10.3 Smoke tests inline : 15 routes publiques contiennent popup PWA (0 échec)

## Phase 11 — Migration Base de Données
- [x] 11.1 Créer la migration Alembic pour les nouveaux modèles
- [x] 11.2 Appliquer la migration (stampée comme appliquée - tables existantes)
- [x] 11.3 Fallback DDL direct SQLite-safe + ORM auto-create via `_apply_pwa_db.py` (tables `app_installations` + `pwa_config`)

## Phase 12 — Endpoints exposés (référence)
- [x] 12.1 `GET  /manifest.json`                    → PWA manifest (10 icônes, shortcuts events/contact)
- [x] 12.2 `GET  /pwa/offline.html`                → page hors-ligne glassmorphism
- [x] 12.3 `GET  /api/v1/pwa/config`               → enabled, popup_delay, dismiss_duration_days, custom title/desc/button
- [x] 12.4 `POST /api/v1/pwa/install-event`        → tracking requested/installed/dismissed (201 Created, exempt CSRF)
- [x] 12.5 `GET  /api/v1/pwa/stats`                → KPIs + by_device + 10 derniers events
- [x] 12.6 `GET/POST /admin/mobile-install`        → config admin + stats (login + role admin requis)

