const CACHE_NAME = 'chere-v2';
const STATIC_CACHE = 'chere-static-v2';
const PAGE_CACHE = 'chere-pages-v2';
const OFFLINE_URL = '/templates/pwa/offline.html';

const PRECACHE_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/pwa/install.js',
  '/static/pwa/install.css',
  '/static/img/logo-nav.png',
  '/static/img/logo.png',
  '/static/img/logo-mark.png',
  '/static/img/favicon-16.png',
  '/static/img/favicon-180.png',
  '/static/img/favicon-192.png',
  '/static/img/favicon-512.png',
  '/static/img/favicon.ico',
  '/static/manifest.json'
];

const RUNTIME_PAGES = [
  '/',
  '/about',
  '/events',
  '/contact',
  '/innovation',
  '/renewable-energy',
  '/humanitarian',
  '/projects',
  '/partners',
  '/blog',
  '/services',
  '/eval'
];

// === INSTALL ===
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// === ACTIVATE ===
self.addEventListener('activate', event => {
  const validCaches = [STATIC_CACHE, PAGE_CACHE];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(name => {
          if (!validCaches.includes(name) && name !== CACHE_NAME) {
            return caches.delete(name);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// === FETCH STRATEGIES ===
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and external requests
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) {
    // External resources: CDN, fonts, etc. — Network First
    event.respondWith(networkFirstWithFallback(request));
    return;
  }

  const pathname = url.pathname;

  // Static assets (CSS, JS, images) — Cache First
  if (pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|ico|webp|woff2?)$/)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // PWA manifest — Cache First
  if (pathname === '/manifest.json' || pathname.startsWith('/static/')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // API calls — Network First
  if (pathname.startsWith('/api/')) {
    event.respondWith(networkFirstWithTimeout(request, 3000));
    return;
  }

  // Navigation / pages — Network First with offline fallback
  if (RUNTIME_PAGES.includes(pathname) || request.mode === 'navigate') {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }

  // Default: Network First
  event.respondWith(networkFirstWithFallback(request));
});

// === CACHE STRATEGIES ===

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return new Response('Offline', { status: 408 });
  }
}

async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(PAGE_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    // Return offline page
    const offlineResponse = await caches.match(OFFLINE_URL);
    if (offlineResponse) return offlineResponse;
    return new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/html' } });
  }
}

async function networkFirstWithTimeout(request, timeout = 5000) {
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Timeout')), timeout)
  );
  try {
    const response = await Promise.race([
      fetch(request),
      timeoutPromise
    ]);
    if (response.ok) {
      const cache = await caches.open(PAGE_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ error: 'offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function networkFirstWithFallback(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    return cached || new Response('Offline', { status: 503 });
  }
}
