/**
 * Boldly Balance - Service Worker
 * Provides offline support and smart caching
 * Version: 1.0.0
 */

const CACHE_NAME = 'boldly-balance-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/reading-time.js',
    '/share-buttons.js',
    '/search.css',
    '/favicon.svg',
    '/posts.json',
    '/search-index.json'
];

// Install: Cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Cache strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip Plausible analytics and external scripts
    if (url.hostname.includes('plausible.io') || 
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com')) {
        return;
    }

    // Strategy: Cache First for static assets
    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Strategy: Stale While Revalidate for HTML pages
    if (request.mode === 'navigate') {
        event.respondWith(staleWhileRevalidate(request));
        return;
    }

    // Strategy: Network First for API calls
    if (url.pathname.includes('.json')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Default: Network with cache fallback
    event.respondWith(networkWithCacheFallback(request));
});

function isStaticAsset(url) {
    const staticExtensions = ['.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.woff2'];
    return staticExtensions.some(ext => url.pathname.endsWith(ext));
}

async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (err) {
        return new Response('Offline - Resource not cached', { status: 503 });
    }
}

async function staleWhileRevalidate(request) {
    const cached = await caches.match(request);
    
    const fetchPromise = fetch(request).then((response) => {
        if (response.ok) {
            const cache = caches.open(CACHE_NAME);
            cache.then(c => c.put(request, response.clone()));
        }
        return response;
    }).catch(() => cached);

    return cached || fetchPromise;
}

async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (err) {
        const cached = await caches.match(request);
        if (cached) return cached;
        throw err;
    }
}

async function networkWithCacheFallback(request) {
    try {
        return await fetch(request);
    } catch (err) {
        const cached = await caches.match(request);
        if (cached) return cached;
        throw err;
    }
}
