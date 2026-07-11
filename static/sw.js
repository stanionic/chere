const CACHE_NAME = 'chere-v1';
const ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/img/favicon-192.png',
  '/static/img/favicon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
