/* =========================================================
   CHERE — PWA Installer v2
   - Intercepte beforeinstallprompt (Android/Chrome/Edge/Samsung)
   - Guide iOS Safari (partager → sur écran d'accueil)
   - Lise config depuis /api/v1/pwa/config (delay, dismiss_days, enabled)
   - Popup glassmorphism : localStorage + 1j minimum (configurable)
   - Logique : affichage auto apres Xs, bouton Installer / Plus tard / Fermer
   - Appel /api/v1/pwa/install-event pour statistiques admin
   - Service Worker registration inline ici (unique source de vérité)
   ========================================================= */

(function () {
  'use strict';

  const PWA_STORAGE_KEY = 'chere_pwa_v2';
  const INSTALL_ENDPOINT = '/api/v1/pwa/install-event';
  const CONFIG_ENDPOINT = '/api/v1/pwa/config';
  const SW_PATH = '/static/sw.js';

  let deferredPrompt = null;
  let runtimeConfig = null;
  let popupShownInThisSession = false;

  // ========== Service Worker (dès le chargement) ==========
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      try {
        navigator.serviceWorker.register(SW_PATH, { scope: '/' })
          .then(reg => { /* OK */ })
          .catch(err => { console.debug('[CHERE-PWA] SW registration failed:', err); });
      } catch (e) { /* silencieux */ }
    });
  }

  // ========== Helpers storage ==========
  function readStorage() {
    try {
      const raw = localStorage.getItem(PWA_STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }

  function writeStorage(patch) {
    try {
      const cur = readStorage();
      localStorage.setItem(PWA_STORAGE_KEY, JSON.stringify(Object.assign(cur, patch)));
    } catch (e) { /* silencieux */ }
  }

  function dismissIsExpired(storage) {
    if (!storage || !storage.dismissedAt) return true;
    const days = (runtimeConfig && runtimeConfig.dismiss_duration_days) ? runtimeConfig.dismiss_duration_days : 1;
    const ms = days * 24 * 60 * 60 * 1000;
    return (Date.now() - storage.dismissedAt) > ms;
  }

  // ========== Device detection ==========
  function detect() {
    const ua = (navigator.userAgent || '') + ' ' + (navigator.vendor || '');
    const isIOS = /iphone|ipad|ipod/i.test(ua);
    const isAndroid = /android/i.test(ua);
    const isSafari = /safari/i.test(ua) && !/chrome|crios|edg|opr\//i.test(ua);
    const isChrome = /chrome|crios/i.test(ua) && !/edg|opr\//i.test(ua);
    const isSamsung = /samsung/i.test(ua);
    const isEdge = /edg/i.test(ua);
    const isOpera = /opr\//i.test(ua);
    const isMobile = isIOS || isAndroid || /mobile/i.test(ua);

    return {
      ua, isIOS, isAndroid, isSafari, isChrome, isSamsung, isEdge, isOpera, isMobile,
      isDesktop: !isMobile,
      supportsNativePrompt: (isAndroid && (isChrome || isSamsung || isEdge || isOpera)) ||
                             (!isMobile && (isChrome || isEdge || isOpera))
    };
  }

  function isStandalone() {
    try {
      return (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) ||
             (window.navigator && window.navigator.standalone === true) ||
             (window.matchMedia && window.matchMedia('(display-mode: fullscreen)').matches);
    } catch (e) { return false; }
  }

  // ========== Popup rendering helpers ==========
  function qs(id) { return document.getElementById(id); }

  function applyDeviceVariant(device) {
    const guideEl = qs('chere-pwa-ios-guide');
    const installBtn = document.querySelector('.chere-pwa-install-btn');
    const overlay = qs('chere-pwa-overlay');
    if (!overlay) return;

    // Title / subtitle / button personnalises depuis config si presents
    if (runtimeConfig) {
      const titleEl = document.querySelector('.chere-pwa-title');
      const subEl = document.querySelector('.chere-pwa-subtitle');
      const btnEl = document.querySelector('.chere-pwa-install-btn');
      if (titleEl && runtimeConfig.custom_title) titleEl.textContent = runtimeConfig.custom_title;
      if (subEl && runtimeConfig.custom_description) subEl.textContent = runtimeConfig.custom_description;
      if (btnEl && runtimeConfig.custom_button) btnEl.textContent = runtimeConfig.custom_button;
    }

    // iOS Safari : montre le guide 3 étapes, change le texte du bouton pour "J'ai compris"
    if (guideEl) {
      if (device.isIOS && !deferredPrompt) {
        guideEl.classList.add('chere-pwa-active');
        if (installBtn) installBtn.textContent = (runtimeConfig && runtimeConfig.custom_button) || "J'ai compris";
      } else {
        guideEl.classList.remove('chere-pwa-active');
      }
    }
  }

  function showPopup(device) {
    if (popupShownInThisSession) return;
    const overlay = qs('chere-pwa-overlay');
    if (!overlay) return;
    applyDeviceVariant(device);
    overlay.classList.add('chere-pwa-show');
    overlay.setAttribute('aria-hidden', 'false');
    popupShownInThisSession = true;
    sendEvent('requested', device);
  }

  function hidePopup() {
    const overlay = qs('chere-pwa-overlay');
    if (!overlay) return;
    overlay.classList.remove('chere-pwa-show');
    overlay.setAttribute('aria-hidden', 'true');
  }

  // ========== Tracking events admin ==========
  function sendEvent(action, device) {
    device = device || detect();
    const payload = {
      action: action,
      device_type: device.isAndroid ? 'android' : device.isIOS ? 'ios' : 'desktop',
      browser: device.isChrome ? 'chrome' : device.isSafari ? 'safari' :
               device.isSamsung ? 'samsung' : device.isEdge ? 'edge' :
               device.isOpera ? 'opera' : 'other',
      os: (navigator.platform || navigator.userAgent || '').slice(0, 50),
      language: (navigator.language || '').slice(0, 10),
      url: (window.location.href || '').slice(0, 2048),
    };
    try {
      const body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        navigator.sendBeacon(INSTALL_ENDPOINT, body);
      } else {
        fetch(INSTALL_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body,
          credentials: 'same-origin',
          keepalive: true
        }).catch(() => {});
      }
    } catch (e) { /* silencieux */ }
  }

  // ========== Actions UI ==========
  function onClickInstall(e, device) {
    const btn = e.target.closest('.chere-pwa-install-btn');
    if (!btn) return;
    e.preventDefault();

    if (deferredPrompt) {
      try {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(choice => {
          if (choice.outcome === 'accepted') {
            writeStorage({ acceptedAt: Date.now() });
            sendEvent('completed', device);
          } else {
            writeStorage({ dismissedAt: Date.now() });
            sendEvent('dismissed', device);
          }
          deferredPrompt = null;
          hidePopup();
        }).catch(() => { hidePopup(); });
      } catch (err) {
        writeStorage({ acceptedAt: Date.now() });
        hidePopup();
      }
    } else {
      // iOS guide ou fallback : considerer vu comme guide_shown
      writeStorage({ acceptedAt: Date.now() });
      sendEvent('guide_shown', device);
      hidePopup();
    }
  }

  function onClickDismiss(e, device) {
    const t = e.target;
    if (!t.closest('.chere-pwa-close-btn, .chere-pwa-later-btn')) return;
    e.preventDefault();
    writeStorage({ dismissedAt: Date.now() });
    sendEvent('dismissed', device);
    hidePopup();
  }

  function onClickOverlayOutside(e) {
    if (e.target.id === 'chere-pwa-overlay') {
      writeStorage({ dismissedAt: Date.now() });
      sendEvent('dismissed', detect());
      hidePopup();
    }
  }

  // ========== Chargement config et orchestration ==========
  async function loadConfig() {
    try {
      const r = await fetch(CONFIG_ENDPOINT, { credentials: 'same-origin' });
      if (r.ok) {
        runtimeConfig = await r.json();
      }
    } catch (e) { /* ignore : valeurs par défaut ci-dessous */ }
    if (!runtimeConfig) {
      runtimeConfig = {
        enabled: true,
        popup_delay: 5,
        dismiss_duration_days: 1,
        custom_title: null,
        custom_description: null,
        custom_button: null,
      };
    }
    return runtimeConfig;
  }

  function maybeSchedulePopup() {
    const device = detect();

    // Jamais si déjà standalone
    if (isStandalone()) return;

    // Jamais si désactivé dans config
    if (runtimeConfig && runtimeConfig.enabled === false) return;

    // Jamais si on vient de refuser (timeout config)
    const storage = readStorage();
    if (storage.acceptedAt) return;
    if (storage.dismissedAt && !dismissIsExpired(storage)) return;

    const delaySec = Math.max(1, (runtimeConfig && runtimeConfig.popup_delay) || 5);
    const delayMs = delaySec * 1000;

    setTimeout(() => {
      // Si beforeinstallprompt a été capturé, on affiche (Android/desktop)
      if (deferredPrompt) {
        showPopup(device);
        return;
      }
      // iOS Safari → toujours afficher le guide
      if (device.isIOS && device.isSafari) {
        showPopup(device);
        return;
      }
      // Autres navigateurs mobiles : montre quand même un guide / bouton guide mode
      if (device.isMobile) {
        showPopup(device);
        return;
      }
      // Desktop Chrome / Edge : ne montrer que si beforeinstallprompt a été émis, sinon rien
    }, delayMs);
  }

  // ========== Events globaux ==========
  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    deferredPrompt = e;
    // Si popup déjà programmée et pas affichée, elle capturera deferredPrompt normalement.
    // On relance la logique pour éviter d'attendre inutilement si l'utilisateur a déjà atteint 5s.
    if (!popupShownInThisSession) {
      const storage = readStorage();
      if (runtimeConfig && runtimeConfig.enabled !== false && !storage.acceptedAt && dismissIsExpired(storage)) {
        const delaySec = Math.max(0.5, (runtimeConfig && runtimeConfig.popup_delay) || 5);
        // Pas besoin de réécrire showPopup : beforeinstallprompt est suivi par le setTimeout initial
      }
    }
  });

  window.addEventListener('appinstalled', () => {
    writeStorage({ acceptedAt: Date.now() });
    sendEvent('installed', detect());
    hidePopup();
  });

  document.addEventListener('DOMContentLoaded', async () => {
    const device = detect();

    // Events clic du popup (délégation)
    document.addEventListener('click', e => {
      if (e.target.closest('.chere-pwa-install-btn')) onClickInstall(e, device);
      if (e.target.closest('.chere-pwa-close-btn, .chere-pwa-later-btn')) onClickDismiss(e, device);
      if (e.target.id === 'chere-pwa-overlay') onClickOverlayOutside(e);
    });

    // Touche Echap
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        const ov = qs('chere-pwa-overlay');
        if (ov && ov.classList.contains('chere-pwa-show')) {
          writeStorage({ dismissedAt: Date.now() });
          sendEvent('dismissed', detect());
          hidePopup();
        }
      }
    });

    await loadConfig();
    maybeSchedulePopup();
  });

  // Exposition globale pour debug (fenêtre console: window.__CHERE_PWA.showPopup())
  window.__CHERE_PWA = Object.freeze({
    showPopup: () => showPopup(detect()),
    hidePopup: hidePopup,
    getConfig: () => runtimeConfig,
    detect: detect,
    isStandalone: isStandalone,
    resetStorage: () => { try { localStorage.removeItem(PWA_STORAGE_KEY); } catch(e){} },
  });
})();
