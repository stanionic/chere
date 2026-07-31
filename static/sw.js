/* =========================================================
   CHERE — Service Worker v3 (PWA install-friendly)
   Cache stratégique : static Cache-First, pages Network-First,
   offline fallback page accessible à la racine.
   ========================================================= */

const VERSION = 'v3';
const STATIC_CACHE = `chere-static-${VERSION}`;
const PAGE_CACHE   = `chere-pages-${VERSION}`;

const OFFLINE_URL = '/pwa/offline.html';

// Assets connus statiques servis par /static/ — précachés à l'install
const PRECACHE_ASSETS = [
  OFFLINE_URL,
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/pwa/install.js',
  '/static/pwa/install.css',
  '/static/img/logo-mark.png',
  '/static/img/favicon.ico',
  '/static/img/favicon-16.png',
  '/static/img/favicon-180.png',
  '/static/img/favicon-192.png',
  '/static/img/favicon-512.png',
  '/static/manifest.json'
];

// === INSTALL ===
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(PRECACHE_ASSETS)).catch(() => {})
  );
});

// === ACTIVATE ===
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== STATIC_CACHE && k !== PAGE_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// === HELPERS ===
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const resp = await fetch(request);
    if (resp && resp.ok && request.method === 'GET') {
      const copy = resp.clone();
      caches.open(STATIC_CACHE).then(c => c.put(request, copy)).catch(() => {});
    }
    return resp;
  } catch (e) {
    return new Response('Offline', { status: 408, statusText: 'Request Timeout' });
  }
}

async function networkFirst(request, { timeoutMs = 6000, offlinePage = false } = {}) {
  const timeout = new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), timeoutMs));
  try {
    const resp = await Promise.race([fetch(request), timeout]);
    if (resp && resp.ok && request.method === 'GET') {
      const copy = resp.clone();
      caches.open(PAGE_CACHE).then(c => c.put(request, copy)).catch(() => {});
    }
    return resp;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (offlinePage) {
      const fallback = await caches.match(OFFLINE_URL);
      if (fallback) return fallback;
    }
    if (request.headers && request.headers.get('accept') && request.headers.get('accept').includes('text/html')) {
      return new Response(
        '<html><body style="font-family:system-ui;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:2rem;text-align:center;color:#1446a0;"><div><h1>CHERE</h1><p>Vous etes hors ligne. Reconnectez-vous pour continuer.</p></div></body></html>',
        { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
      );
    }
    return new Response(
      JSON.stringify({ error: 'offline' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

// === FETCH ===
self.addEventListener('fetch', event => {
  const req = event.request;

  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) {
    // CDN / tierces parties : on ne les met pas en cache
    return;
  }

  const path = url.pathname;

  // Manifest + favicons + static (CSS, JS, images, fonts) : Cache First
  if (
    path === '/manifest.json' ||
    path.startsWith('/static/') ||
    /\.(?:css|js|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot)$/i.test(path)
  ) {
    event.respondWith(cacheFirst(req));
    return;
  }

  // API : Network First avec timeout, fallback JSON offline
  if (path.startsWith('/api/')) {
    event.respondWith(networkFirst(req, { timeoutMs: 5000 }));
    return;
  }

  // Pages / navigate : Network First avec fallback offline page
  if (req.mode === 'navigate' || /text\/html/.test(req.headers.get('accept') || '')) {
    event.respondWith(networkFirst(req, { timeoutMs: 8000, offlinePage: true }));
    return;
  }

  // Defaut : Network First
  event.respondWith(networkFirst(req));
});
