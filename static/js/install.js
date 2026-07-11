(() => {
  let deferredPrompt = null;

  function createBanner() {
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
    banner.style.background = 'linear-gradient(90deg, rgba(20,70,160,0.98), rgba(25,135,84,0.98))';
    banner.style.color = '#fff';
    banner.style.borderRadius = '12px';
    banner.style.boxShadow = '0 6px 18px rgba(0,0,0,0.18)';

    const text = document.createElement('div');
    text.style.flex = '1';
    text.style.fontSize = '14px';
    text.style.fontWeight = '600';
    text.textContent = 'Ajouter CHERE à l\'écran d\'accueil pour une expérience native.';

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '8px';

    const installBtn = document.createElement('button');
    installBtn.className = 'btn btn-light btn-sm';
    installBtn.textContent = 'Installer';

    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-outline-light btn-sm';
    closeBtn.textContent = 'Fermer';

    actions.appendChild(installBtn);
    actions.appendChild(closeBtn);

    banner.appendChild(text);
    banner.appendChild(actions);

    document.body.appendChild(banner);

    installBtn.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice && choice.outcome === 'accepted') {
        banner.remove();
      }
      deferredPrompt = null;
    });

    closeBtn.addEventListener('click', () => banner.remove());
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent automatic prompt; show our own banner instead.
    e.preventDefault();
    deferredPrompt = e;
    // show banner on mobile viewport sizes
    if (window.innerWidth <= 900) {
      if (!document.getElementById('pwa-install-banner')) createBanner();
    }
  });

  // Fallback for iOS: show an instruction banner (can't trigger install programmatically)
  function isiOS() {
    return /iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase());
  }

  function showIOSInstructions() {
    if (!isiOS() || document.getElementById('pwa-install-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.style.position = 'fixed';
    banner.style.left = '12px';
    banner.style.right = '12px';
    banner.style.bottom = '18px';
    banner.style.zIndex = '99999';
    banner.style.padding = '10px 14px';
    banner.style.background = '#1446a0';
    banner.style.color = '#fff';
    banner.style.borderRadius = '12px';
    banner.style.boxShadow = '0 6px 18px rgba(0,0,0,0.18)';
    banner.style.fontSize = '14px';
    banner.style.fontWeight = '600';
    banner.textContent = 'Pour installer l\'application CHERE sur iOS, appuyez sur Partager puis « Sur l\'écran d\'accueil ». ';
    const close = document.createElement('button');
    close.className = 'btn btn-outline-light btn-sm';
    close.style.marginLeft = '10px';
    close.textContent = 'Fermer';
    close.addEventListener('click', () => banner.remove());
    banner.appendChild(close);
    document.body.appendChild(banner);
  }

  window.addEventListener('load', () => {
    // show iOS hint after a short delay on mobile
    setTimeout(() => showIOSInstructions(), 1200);
    // register service worker if supported
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/static/sw.js').catch(() => {});
    }
  });
})();
