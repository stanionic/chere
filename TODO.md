# TODO — Module PWA "CHERE APP INSTALLER"
> Durée avant réaffichage : **1 jour** (configurable depuis l'admin)

## Phase 1 — Assets et Configuration PWA
- [x] 1.1 Créer le dossier `app/static/pwa/icons/`
- [x] 1.2 Mettre à jour `static/manifest.json` (version complète standalone)
- [x] 1.3 Créer `app/templates/pwa/offline.html`

## Phase 2 — Service Worker
- [x] 2.1 Mettre à jour `static/sw.js` (service worker complet avec cache stratégique)

## Phase 3 — JavaScript Intelligent + CSS
- [x] 3.1 Créer `app/static/pwa/install.js` (détection, beforeinstallprompt, iOS guide, localStorage 1 jour)
- [x] 3.2 Créer `app/static/pwa/install.css` (glassmorphism CHERE)

## Phase 4 — Popup d'Installation
- [x] 4.1 Créer `app/templates/components/install_popup.html`

## Phase 5 — Base de Données
- [x] 5.1 Ajouter modèle `AppInstallation` dans `app/models.py`
- [x] 5.2 Ajouter modèle `PwaConfig` pour la config admin (délai, texte, 1 jour par défaut)

## Phase 6 — Blueprint PWA
- [x] 6.1 Créer `app/blueprints/pwa/__init__.py`
- [x] 6.2 Créer `app/blueprints/pwa/routes.py`
- [x] 6.3 Enregistrer blueprint dans `app/__init__.py`

## Phase 7 — Administration Mobile
- [x] 7.1 Ajouter `MobileInstallSettingsForm` dans `app/blueprints/admin/forms.py`
- [x] 7.2 Ajouter routes admin pour la config mobile
- [x] 7.3 Créer `app/templates/admin/mobile_install.html`
- [x] 7.4 Mettre à jour `app/templates/admin/base_admin.html` (lien sidebar)

## Phase 8 — Internationalisation
- [x] 8.1 Ajouter traductions PWA dans `app/i18n.py` (FR/EN)

## Phase 9 — Templates et intégration
- [x] 9.1 Mettre à jour `app/templates/base.html` (inclure popup + scripts PWA)

## Phase 10 — Tests
- [x] 10.1 Créer `tests/test_pwa.py`
- [x] 10.2 Vérifier que l'application démarre sans erreur

## Phase 11 — Migration Base de Données
- [x] 11.1 Créer la migration Alembic pour les nouveaux modèles
- [x] 11.2 Appliquer la migration (stampée comme appliquée - tables existantes)
