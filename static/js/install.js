(() => {
  let deferredPrompt = null;
  const storageKey = 'chere-pwa-install-dismissed';

  function isMobile() {
    return /android|iphone|ipad|ipod|mobile/i.test(window.navigator.userAgent);
  }

  function createBanner(message, type = 'install') {
    if (document.getElementById('pwa-install-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.style.position = 'fixed';
    banner.style.left = '12px';
    banner.style.right = '12px';
    banner.style.bottom = '18px';
    banner.style.zIndex = '99999';
    banner.style.display = 'flex';
    banner.style.justifyContent = 'space-between';
    banner.style.alignItems = 'center';
    banner.style.gap = '12px';
    banner.style.padding = '10px 14px';
    banner.style.background = type === 'ios' ? '#1446a0' : 'linear-gradient(90deg, rgba(20,70,160,0.98), rgba(25,135,84,0.98))';
    banner.style.color = '#fff';
    banner.style.borderRadius = '12px';
    banner.style.boxShadow = '0 6px 18px rgba(0,0,0,0.18)';

    const text = document.createElement('div');
    text.style.flex = '1';
    text.style.fontSize = '14px';
    text.style.fontWeight = '600';
    text.textContent = message;

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '8px';

    if (type === 'install') {
      const installBtn = document.createElement('button');
      installBtn.className = 'btn btn-light btn-sm';
      installBtn.textContent = 'Installer';
      installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const choice = await deferredPrompt.userChoice;
        if (choice && choice.outcome === 'accepted') {
          banner.remove();
        }
        deferredPrompt = null;
      });
      actions.appendChild(installBtn);
    }

    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-outline-light btn-sm';
    closeBtn.textContent = 'Fermer';
    closeBtn.addEventListener('click', () => {
      localStorage.setItem(storageKey, '1');
      banner.remove();
    });
    actions.appendChild(closeBtn);

    banner.appendChild(text);
    banner.appendChild(actions);
    document.body.appendChild(banner);
  }

  function showInstallPrompt() {
    if (!isMobile() || localStorage.getItem(storageKey) === '1') return;
    if (deferredPrompt) {
      createBanner('Ajouter CHERE à l\'écran d\'accueil pour une expérience native.');
    } else if (/iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase())) {
      createBanner('Pour installer CHERE sur iPhone ou iPad, appuyez sur Partager puis « Sur l\'écran d\'accueil ».', 'ios');
    }
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (isMobile()) {
      setTimeout(showInstallPrompt, 1500);
    }
  });

  window.addEventListener('load', () => {
    setTimeout(showInstallPrompt, 1800);
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/static/sw.js').catch(() => {});
    }
  });
})();
