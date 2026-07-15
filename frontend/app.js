const $ = (sel) => document.querySelector(sel);

const STORAGE_KEY = "gasradar_last_location";

const state = {
  lat: null,
  lon: null,
  label: "",
  fuel: "regular",
  radius: 5,
  stations: [],
  cheapest: null,
  reportStationId: null,
  zip: null,
};

function saveLocation(loc) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        lat: loc.lat,
        lon: loc.lon,
        label: loc.label,
        zip: loc.zip || null,
        saved_at: Date.now(),
      })
    );
  } catch (_) {
    /* ignore */
  }
}

function loadSavedLocation() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const o = JSON.parse(raw);
    if (o.lat == null || o.lon == null) return null;
    // válido 30 días
    if (o.saved_at && Date.now() - o.saved_at > 30 * 24 * 3600 * 1000) return null;
    return o;
  } catch (_) {
    return null;
  }
}

function money(n) {
  if (n == null || Number.isNaN(n)) return "—";
  return `$${Number(n).toFixed(2)}`;
}

function fuelLabel(fuel) {
  const map = {
    regular: "Regular",
    mid: "Mid",
    premium: "Premium",
    diesel: "Diesel",
  };
  return map[fuel] || fuel || "Regular";
}

function showToast(msg) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.remove("show"), 2200);
}

/** Texto listo para WhatsApp / iMessage / copiar */
function buildShareText(station) {
  const name = station.name || "Estación";
  const price = money(station.price);
  const fuel = fuelLabel(state.fuel);
  const dist =
    station.distance_mi != null ? `${station.distance_mi} mi` : "";
  const zona = state.label || "";
  const maps = mapsUrl(station);
  const appUrl = location.origin + location.pathname;

  let lines = [
    `⛽ GasRadar — precio de gasolina`,
    ``,
    `${name}`,
    `${fuel}: ${price}/gal`,
  ];
  if (dist) lines.push(`Distancia: ${dist}`);
  if (zona) lines.push(`Zona: ${zona}`);
  lines.push(``);
  lines.push(`📍 Cómo llegar: ${maps}`);
  lines.push(``);
  lines.push(`App: ${appUrl}`);
  lines.push(`Por Alberto · tecnologiameridahd@gmail.com`);
  return lines.join("\n");
}

async function sharePrice(station) {
  if (!station || station.lat == null) {
    showToast("No hay precio para compartir");
    return;
  }
  const text = buildShareText(station);
  const title = `Gasolina ${money(station.price)} — ${station.name || "GasRadar"}`;

  // 1) Compartir nativo (iPhone / Android)
  if (navigator.share) {
    try {
      await navigator.share({ title, text });
      return;
    } catch (e) {
      // usuario canceló
      if (e && e.name === "AbortError") return;
    }
  }

  // 2) WhatsApp (muy usado)
  const wa = `https://wa.me/?text=${encodeURIComponent(text)}`;
  try {
    window.open(wa, "_blank", "noopener");
    return;
  } catch (_) {
    /* fallthrough */
  }

  // 3) Copiar al portapapeles
  try {
    await navigator.clipboard.writeText(text);
    showToast("Precio copiado — pégalo a tus amigos");
  } catch (_) {
    // fallback viejo
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    showToast("Precio copiado");
  }
}

/** Detecta iPhone/iPad vs Android vs PC */
function detectPlatform() {
  const ua = navigator.userAgent || navigator.vendor || "";
  if (/iPad|iPhone|iPod/i.test(ua)) return "ios";
  // iPadOS 13+ a veces se hace pasar por Mac
  if (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1) return "ios";
  if (/Android/i.test(ua)) return "android";
  return "web";
}

/**
 * Enlace de navegación:
 * - Estación real (OSM): ir a lat/lon exactos
 * - Sugerencia / demo: buscar por nombre cerca de ti (evita direcciones inventadas)
 * - iPhone → Apple Maps | Android/PC → Google Maps
 */
function mapsUrl(stationOrLat, lon, name) {
  // Acepta (station) o (lat, lon, name) por compatibilidad
  let lat, stationName, mapsQuery, isSearch;
  if (stationOrLat && typeof stationOrLat === "object") {
    const s = stationOrLat;
    lat = s.lat;
    lon = s.lon;
    stationName = s.name || "Gasolina";
    mapsQuery = s.maps_query || s.name || "gas station";
    isSearch = s.is_demo || s.source === "search_suggest" || s.nav_mode === "search";
  } else {
    lat = stationOrLat;
    stationName = name || "Gasolina";
    mapsQuery = stationName;
    isSearch = false;
  }

  const platform = detectPlatform();
  const dest = `${lat},${lon}`;
  const q = encodeURIComponent(mapsQuery);

  // Modo búsqueda: Maps encuentra la gasolinera real cerca
  if (isSearch) {
    if (platform === "ios") {
      return `https://maps.apple.com/?q=${q}`;
    }
    return `https://www.google.com/maps/search/?api=1&query=${q}`;
  }

  // Coordenadas reales de OpenStreetMap
  if (platform === "ios") {
    // daddr + q ayuda a Apple Maps a fijar el destino
    return `https://maps.apple.com/?daddr=${dest}&q=${encodeURIComponent(stationName)}&dirflg=d&ll=${dest}`;
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${dest}&destination=${encodeURIComponent(
    stationName
  )}&travelmode=driving`;
}

function mapsButtonLabel() {
  return "Cómo llegar";
}

function setStatus(msg, kind = "loading") {
  const el = $("#status");
  el.className = kind;
  el.textContent = msg;
}

async function search({ lat, lon, zip } = {}) {
  setStatus("GasRadar escaneando estaciones…", "loading");
  $("#results").innerHTML = "";
  $("#bestCard").style.display = "none";

  const params = new URLSearchParams();
  params.set("fuel", state.fuel);
  params.set("radius_mi", String(state.radius));
  params.set("limit", "35");
  if (zip) params.set("zip", zip);
  if (lat != null && lon != null) {
    params.set("lat", String(lat));
    params.set("lon", String(lon));
  }

  try {
    const res = await fetch(`/api/search?${params.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Error ${res.status}`);
    }
    const data = await res.json();
    state.lat = data.center.lat;
    state.lon = data.center.lon;
    state.label = data.center.label;
    state.stations = data.stations || [];
    if (zip) state.zip = zip;
    saveLocation({
      lat: state.lat,
      lon: state.lon,
      label: state.label,
      zip: state.zip || zip || null,
    });
    if (state.zip && $("#zipInput") && !$("#zipInput").value) {
      $("#zipInput").value = state.zip;
    }
    render(data);
  } catch (e) {
    setStatus(e.message || "Error de búsqueda", "error");
  }
}

function render(data) {
  $("#locationLabel").textContent = data.center.label;
  const avg = data.state_avg || {};
  const meta = data.price_meta || {};
  const src =
    meta.avg_source === "eia"
      ? `EIA oficial${meta.eia_period ? " · " + meta.eia_period : ""}`
      : "estimado";
  $("#stateAvg").textContent = `Promedio estado: ${money(avg[state.fuel] || avg.regular)} (${src})`;

  if (data.cheapest) {
    const b = data.cheapest;
    state.cheapest = b;
    $("#bestCard").style.display = "block";
    $("#bestPrice").textContent = money(b.price);
    $("#bestName").textContent = b.name;
    $("#bestMeta").textContent = `${b.distance_mi} mi · ${b.source === "user" ? "reportado" : "estimado"}`;
    // cheapest puede no traer maps_query; buscar en stations
    const full =
      state.stations.find((x) => x.id === b.station_id) ||
      state.stations.find((x) => x.name === b.name) ||
      b;
    $("#bestMaps").href = mapsUrl(full);
    $("#bestMaps").textContent = "Cómo llegar";
  } else {
    state.cheapest = null;
  }

  if (!state.stations.length) {
    setStatus("No hay estaciones en ese radio. Prueba 10 mi.", "empty");
    return;
  }

  setStatus(
    `${data.count} estaciones · ordenadas por precio más bajo · ${state.fuel}`,
    "loading"
  );

  const html = state.stations
    .map((s, i) => {
      const rankClass = i === 0 ? "rank gold" : "rank";
      let src;
      if (s.price_source === "user") {
        const n = s.reports_count ? ` · ${s.reports_count} rep` : "";
        const age = s.price_age_hours != null ? ` · ${s.price_age_hours}h` : "";
        src = `<span class="badge user">reportado${n}${age}</span>`;
      } else if (s.price_source === "eia_estimate") {
        src = `<span class="badge eia">EIA + marca</span>`;
      } else {
        src = `<span class="badge estimate">estimado</span>`;
      }
      const addr = s.address
        ? `<p class="station-sub">${escapeHtml(s.address)}</p>`
        : "";
      const demoBadge = s.is_demo
        ? `<span class="badge estimate">buscar en mapa</span> `
        : "";
      return `
      <article class="station" data-id="${s.id}">
        <div class="station-top">
          <div>
            <p class="station-name"><span class="${rankClass}">${i + 1}</span>${escapeHtml(s.name)}</p>
            <p class="station-sub">${demoBadge}${escapeHtml(s.brand || "")} · ${s.distance_mi} mi ${src}</p>
            ${addr}
          </div>
          <div class="station-price">${money(s.price)}</div>
        </div>
        <div class="station-actions">
          <a class="btn-ghost" href="${mapsUrl(s)}" target="_blank" rel="noopener">${mapsButtonLabel()}</a>
          <button class="btn-ghost" type="button" data-share="${escapeHtml(s.id)}">Compartir</button>
          <button class="btn-ghost" type="button" data-report="${s.id}" data-name="${escapeHtml(s.name)}">Reportar precio</button>
        </div>
      </article>`;
    })
    .join("");

  $("#results").innerHTML = html;
  $("#disclaimer").textContent = data.disclaimer || "";

  $("#results").querySelectorAll("[data-report]").forEach((btn) => {
    btn.addEventListener("click", () => openReport(btn.dataset.report, btn.dataset.name));
  });
  $("#results").querySelectorAll("[data-share]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-share");
      const st = state.stations.find((x) => x.id === id);
      if (st) sharePrice(st);
    });
  });
}

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function openReport(stationId, name) {
  state.reportStationId = stationId;
  $("#reportTitle").textContent = `Reportar · ${name}`;
  $("#reportPrice").value = "";
  $("#modal").classList.add("open");
}

function closeReport() {
  $("#modal").classList.remove("open");
  state.reportStationId = null;
}

async function submitReport() {
  const price = parseFloat($("#reportPrice").value);
  if (!state.reportStationId || Number.isNaN(price)) {
    alert("Pon un precio válido");
    return;
  }
  const res = await fetch("/api/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      station_id: state.reportStationId,
      fuel: state.fuel,
      price,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert(err.detail || "No se pudo guardar");
    return;
  }
  closeReport();
  // refresh same location
  await search({ lat: state.lat, lon: state.lon });
}

function useGps() {
  if (!navigator.geolocation) {
    setStatus("GPS no disponible. Usa un ZIP (ej. 80903 Colorado Springs).", "error");
    return;
  }
  if (window.isSecureContext !== true && !["localhost", "127.0.0.1"].includes(location.hostname)) {
    setStatus("GPS no disponible aquí. Usa un ZIP (ej. 80903).", "error");
    return;
  }
  setStatus("Obteniendo tu ubicación real…", "loading");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      state.zip = null;
      search({ lat: pos.coords.latitude, lon: pos.coords.longitude });
    },
    () => {
      setStatus("Sin GPS. Usa un ZIP (Colorado Springs: 80903).", "error");
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 }
  );
}

/** Arranque: NO forzar Denver. 1) última zona guardada 2) GPS 3) pedir ZIP */
function startApp() {
  const saved = loadSavedLocation();
  if (saved) {
    state.zip = saved.zip || null;
    if (saved.zip && $("#zipInput")) $("#zipInput").value = saved.zip;
    setStatus("Cargando tu última ubicación…", "loading");
    if (saved.zip) {
      search({ zip: saved.zip });
    } else {
      search({ lat: saved.lat, lon: saved.lon });
    }
    // actualizar con GPS si se puede (en segundo plano)
    tryGpsBackground();
    return;
  }

  if (
    navigator.geolocation &&
    (window.isSecureContext === true ||
      ["localhost", "127.0.0.1"].includes(location.hostname))
  ) {
    setStatus("Detectando tu ubicación…", "loading");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        search({ lat: pos.coords.latitude, lon: pos.coords.longitude });
      },
      () => {
        setStatus(
          "Activa GPS o escribe tu ZIP (Colorado Springs: 80903).",
          "empty"
        );
        $("#locationLabel").textContent = "Sin ubicación — usa ZIP o GPS";
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
    return;
  }

  setStatus("Escribe tu ZIP (ej. 80903 Colorado Springs) o usa GPS.", "empty");
  $("#locationLabel").textContent = "Sin ubicación — usa ZIP o GPS";
}

function tryGpsBackground() {
  if (!navigator.geolocation) return;
  if (
    window.isSecureContext !== true &&
    !["localhost", "127.0.0.1"].includes(location.hostname)
  ) {
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      // si te moviste > ~3 millas, refrescar
      if (state.lat != null && state.lon != null) {
        const dlat = Math.abs(lat - state.lat);
        const dlon = Math.abs(lon - state.lon);
        if (dlat < 0.04 && dlon < 0.04) return;
      }
      state.zip = null;
      search({ lat, lon });
    },
    () => {},
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 120000 }
  );
}

function bind() {
  const bestShare = $("#bestShare");
  if (bestShare) {
    bestShare.addEventListener("click", () => {
      if (state.cheapest) sharePrice(state.cheapest);
      else if (state.stations[0]) sharePrice(state.stations[0]);
      else showToast("Busca precios primero");
    });
  }
  $("#btnGps").addEventListener("click", useGps);
  $("#btnZip").addEventListener("click", () => {
    const zip = $("#zipInput").value.trim();
    if (!zip) {
      alert("Escribe un ZIP de USA (Colorado Springs: 80903)");
      return;
    }
    state.zip = zip;
    search({ zip });
  });
  $("#zipInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("#btnZip").click();
  });
  $("#fuelSelect").addEventListener("change", (e) => {
    state.fuel = e.target.value;
    if (state.lat != null) search({ lat: state.lat, lon: state.lon });
  });
  $("#radiusSelect").addEventListener("change", (e) => {
    state.radius = Number(e.target.value);
    if (state.lat != null) search({ lat: state.lat, lon: state.lon });
  });
  $("#btnCloseModal").addEventListener("click", closeReport);
  $("#btnSubmitReport").addEventListener("click", submitReport);
  $("#modal").addEventListener("click", (e) => {
    if (e.target.id === "modal") closeReport();
  });
}

bind();
// Carga inicial: tu ubicación (no forzar Denver)
startApp();
