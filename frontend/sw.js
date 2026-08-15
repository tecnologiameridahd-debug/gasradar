/* GasRadar service worker — v0.9.60
 * JS/CSS: red primero (evita app.js viejo que “no busca”).
 * HTML: red primero + fallback caché (sin flash blanco en cold start).
 */
const CACHE = "gasradar-v0.9.60";
const PRECACHE = [
  "/",
  "/static/styles.css?v=0.9.60",
  "/static/brand-logos.js?v=0.9.1",
  "/static/app.js?v=0.9.60",
  "/static/logo.svg?v=0.2.9",
  "/static/logo-192.png?v=0.5.0",
  "/static/logo-512.png?v=0.5.0",
  "/static/favicon-32.png?v=0.2.9",
  "/manifest.webmanifest",
];

const DARK_SHELL = `<!DOCTYPE html>
<html lang="en" style="background:#0b1220;color-scheme:dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<meta name="theme-color" content="#0b1220"/>
<meta name="color-scheme" content="dark"/>
<title>GasRadar</title>
<style>
html,body{margin:0;min-height:100dvh;background:#0b1220!important;color:#eef3ff;
font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center}
.b{text-align:center}
.d{width:10px;height:10px;border-radius:50%;background:#22c55e;margin:12px auto 0;
animation:p .9s ease infinite alternate}
@keyframes p{from{opacity:.35}to{opacity:1}}
</style>
</head>
<body>
<div class="b"><div style="font-weight:700;letter-spacing:.02em;color:#9aabc7">GasRadar</div>
<div class="d"></div></div>
<script>
try {
  if (!sessionStorage.getItem("gr_sw_boot_55")) {
    sessionStorage.setItem("gr_sw_boot_55", "1");
    setTimeout(function () { location.reload(); }, 900);
  }
} catch (e) {}
</script>
</body></html>`;

function darkShellResponse() {
  return new Response(DARK_SHELL, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      await Promise.all(
        PRECACHE.map((url) =>
          cache.add(url).catch((err) => {
            console.warn("[sw] precache fail", url, err);
          })
        )
      );
      await self.skipWaiting();
    })()
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

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
  if (event.data && event.data.type === "CLEAR_CACHES") {
    event.waitUntil(
      caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
    );
  }
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

  // JS/CSS: RED PRIMERO (crítico — no servir app.js roto de caché vieja)
  if (
    url.pathname.endsWith(".js") ||
    url.pathname.endsWith(".css") ||
    url.pathname.includes("/static/app.js") ||
    url.pathname.includes("/static/styles.css")
  ) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // HTML / navegación: red primero, caché si offline
  if (req.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith(".html")) {
    event.respondWith(
      (async () => {
        try {
          const res = await fetch(req);
          if (res && res.ok) {
            const copy = res.clone();
            const cache = await caches.open(CACHE);
            await cache.put("/", copy.clone());
            await cache.put(req, copy);
          }
          return res;
        } catch (_) {
          const cached =
            (await caches.match(req)) ||
            (await caches.match("/")) ||
            (await caches.match("/static/app.js?v=0.9.53"));
          return cached || darkShellResponse();
        }
      })()
    );
    return;
  }

  // Resto: caché o red
  event.respondWith(
    caches.match(req).then((hit) => {
      const net = fetch(req).then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      });
      return hit || net.catch(() => darkShellResponse());
    })
  );
});
