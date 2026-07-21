/* GasRadar service worker — shell oscura al instante (sin flash blanco) */
const CACHE = "gasradar-v0.9.31";
const PRECACHE = [
  "/",
  "/static/styles.css?v=0.9.29",
  "/static/brand-logos.js?v=0.9.1",
  "/static/app.js?v=0.9.31",
  "/static/logo.svg?v=0.2.9",
  "/static/logo-192.png?v=0.5.0",
  "/static/logo-512.png?v=0.5.0",
  "/static/favicon-32.png?v=0.2.9",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // API: solo red
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(req).catch(
        () =>
          new Response(JSON.stringify({ ok: false, offline: true }), {
            status: 503,
            headers: { "Content-Type": "application/json" },
          })
      )
    );
    return;
  }

  // Navegación HTML: CACHÉ PRIMERO (evita pantalla blanca esperando red/cold start)
  // luego actualiza en segundo plano.
  if (req.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith(".html")) {
    event.respondWith(
      caches.match("/").then((cached) => {
        const network = fetch(req)
          .then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE).then((c) => {
                c.put("/", copy);
                c.put(req, res.clone());
              });
            }
            return res;
          })
          .catch(() => cached || caches.match("/"));
        // Si hay shell en caché, muéstrala YA (oscura); si no, espera red
        return cached || network;
      })
    );
    return;
  }

  // Estáticos: cache primero
  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req)
          .then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE).then((c) => c.put(req, copy));
            }
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});
