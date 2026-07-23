/* =========================================================
   CHERE — PWA Installer
   Détection intelligente, beforeinstallprompt, iOS guide
   Logique : 1 jour avant réaffichage, localStorage
   ========================================================= */

(function () {
  'use strict';

  const CHERE_PWA_KEY = 'chere_pwa_install';
  const DISMISS_DAYS = 1; // 1 jour avant réaffichage

  let deferredPrompt = null;
  let isInstalled = false;

  // === UTILITAIRES ===

  function getStorage() {
    try {
      const raw = localStorage.getItem(CHERE_PWA_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function setStorage(data) {
    try {
      localStorage.setItem(CHERE_PWA_KEY, JSON.stringify(data));
    } catch (e) { /* silencieux */ }
  }

  function isExpired(timestamp) {
    if (!timestamp) return true;
    const now = Date.now();
    const diff = now - timestamp;
    return diff > DISMISS_DAYS * 24 * 60 * 60 * 1000;
  }

  // === DÉTECTION ===

  function detectDevice() {
    const ua = navigator.userAgent || navigator.vendor || '';
    const isAndroid = /android/i.test(ua);
    const isIOS = /iphone|ipad|ipod/i.test(ua);
    const isSafari = /safari/i.test(ua) && !/chrome/i.test(ua);
    const isChrome = /chrome/i.test(ua) && !/edge|opr/i.test(ua);
    const isSamsung = /samsung/i.test(ua) || /sm-/i.test(ua);
    const isFirefox = /firefox/i.test(ua);
    const isEdge = /edg/i.test(ua);
    const isOpera = /opr/i.test(ua);
    const isDesktop = !isAndroid && !isIOS;

    return {
      ua,
      isAndroid,
      isIOS,
      isSafari,
      isChrome,
      isSamsung,
      isFirefox,
      isEdge,
      isOpera,
      isDesktop,
      isMobile: isAndroid || isIOS
    };
  }

  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  function isSupportedBrowser() {
    const device = detectDevice();
    return device.isChrome || device.isSamsung || device.isEdge ||
           device.isOpera || device.isFirefox || device.isSafari;
  }

  // === AFFICHAGE POPUP ===

  function showInstallPopup(device) {
    const overlay = document.getElementById('chere-pwa-overlay');
    if (overlay) {
      overlay.classList.add('chere-pwa-show');
    }
  }

  function hideInstallPopup() {
    const overlay = document.getElementById('chere-pwa-overlay');
    if (overlay) {
      overlay.classList.remove('chere-pwa-show');
    }
  }

  // === BEFOREINSTALLPROMPT (ANDROID) ===

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;

    const device = detectDevice();
    const storage = getStorage();

    // Ne pas afficher si déjà installé
    if (isInstalled || isStandalone()) return;

    // Ne pas afficher si refusé récemment (1 jour)
    if (storage && storage.dismissed && !isExpired(storage.timestamp)) return;

    // Ne pas afficher si déjà accepté
    if (storage && storage.accepted) return;

    // Afficher après un délai (configurable via data attribute)
    const delay = parseInt(document.documentElement.getAttribute('data-pwa-delay') || '5000', 10);
    setTimeout(function () {
      showInstallPopup(device);
    }, delay);
  });

  // === IOS / AUTRES ===

  document.addEventListener('DOMContentLoaded', function () {
    const device = detectDevice();

    // Si déjà en mode standalone, ne rien faire
    if (isStandalone()) {
      isInstalled = true;
      return;
    }

    const storage = getStorage();

    // Ne pas afficher si refusé récemment
    if (storage && storage.dismissed && !isExpired(storage.timestamp)) return;

    // Ne pas afficher si déjà accepté
    if (storage && storage.accepted) return;

    // Pour iOS Safari
    if (device.isIOS && device.isSafari) {
      const delay = parseInt(document.documentElement.getAttribute('data-pwa-delay') || '8000', 10);
      setTimeout(function () {
        showInstallPopup(device);
      }, delay);
      return;
    }

    // Pour les autres navigateurs mobiles (Firefox, Samsung, Edge)
    if (device.isMobile && !device.isChrome) {
      // On attend beforeinstallprompt, mais on peut aussi montrer un guide
      const delay = parseInt(document.documentElement.getAttribute('data-pwa-delay') || '5000', 10);
      setTimeout(function () {
        // Si deferredPrompt n'a pas été capturé, on montre quand même le guide iOS-like
        if (!deferredPrompt) {
          showInstallPopup(device);
        }
      }, delay);
    }
  });

  // === GESTION DES ACTIONS POPUP ===

  document.addEventListener('click', function (e) {
    const target = e.target;

    // Bouton "Installer maintenant"
    if (target.matches('.chere-pwa-install-btn')) {
      e.preventDefault();
      if (deferredPrompt) {
        // Android Chrome : déclencher l'installation native
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function (choice) {
          if (choice.outcome === 'accepted') {
            setStorage({ accepted: true, timestamp: Date.now() });
            isInstalled = true;
            // Envoyer l'événement au serveur
            sendInstallEvent('completed');
          } else {
            setStorage({ dismissed: true, timestamp: Date.now() });
            sendInstallEvent('dismissed');
          }
          deferredPrompt = null;
          hideInstallPopup();
        });
      } else {
        // Pour iOS ou autres : cacher le popup et marquer comme installé (guide affiché)
        setStorage({ accepted: true, timestamp: Date.now() });
        isInstalled = true;
        hideInstallPopup();
        sendInstallEvent('guide_shown');
      }
    }

    // Bouton "Fermer" ou "Plus tard"
    if (target.matches('.chere-pwa-close-btn, .chere-pwa-later-btn')) {
      e.preventDefault();
      setStorage({ dismissed: true, timestamp: Date.now() });
      hideInstallPopup();
      sendInstallEvent('dismissed');
    }
  });

  // === DÉTECTION D'INSTALLATION RÉUSSIE ===

  window.addEventListener('appinstalled', function () {
    isInstalled = true;
    setStorage({ accepted: true, timestamp: Date.now() });
    hideInstallPopup();
    sendInstallEvent('installed');
  });

  // === ENVOI D'ÉVÉNEMENT AU SERVEUR ===

  function sendInstallEvent(action) {
    const device = detectDevice();
    const payload = {
      action: action,
      device_type: device.isAndroid ? 'android' : (device.isIOS ? 'ios' : 'desktop'),
      browser: device.isChrome ? 'chrome' :
               device.isSafari ? 'safari' :
               device.isSamsung ? 'samsung' :
               device.isFirefox ? 'firefox' :
               device.isEdge ? 'edge' : 'other',
      os: navigator.platform || '',
      language: navigator.language || '',
      url: window.location.href
    };

    // Envoi silencieux (fire-and-forget)
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/v1/pwa/install-event', JSON.stringify(payload));
    } else {
      fetch('/api/v1/pwa/install-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true
      }).catch(function () { /* silencieux */ });
    }
  }

  // === EXPOSITION GLOBALE (pour debug) ===
  window.__CHERE_PWA = {
    deferredPrompt: deferredPrompt,
    isInstalled: isInstalled,
    detectDevice: detectDevice,
    getStorage: getStorage,
    showInstallPopup: showInstallPopup,
    hideInstallPopup: hideInstallPopup
  };

})();
