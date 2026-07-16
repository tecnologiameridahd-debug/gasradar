const $ = (sel) => document.querySelector(sel);

const STORAGE_KEY = "gasradar_last_location";
const LANG_KEY = "gasradar_lang";

const I18N = {
  es: {
    subtitle: "Mejores precios cerca de ti · USA",
    btnGps: "Usar mi ubicación",
    zipLabel: "Código ZIP",
    zipPlaceholder: "ZIP (ej. 80903)",
    btnSearch: "Buscar",
    fuelLabel: "Combustible",
    radiusLabel: "Radio",
    mi3: "3 millas",
    mi5: "5 millas",
    mi10: "10 millas",
    mi15: "15 millas",
    noLocation: "Sin ubicación",
    locHint: "Escribe un ZIP o usa el GPS",
    cheapestBadge: "★ Más barata",
    directions: "Cómo llegar",
    share: "Compartir",
    nearYou: "Cerca de ti",
    loading: "Cargando…",
    contact: "Contacto:",
    privacy: "Privacidad",
    refPrices: "Precios de referencia",
    reportTitle: "Reportar precio",
    reportSub: "¿Cuánto viste en la bomba? (USD / galón)",
    reportHint: "Ejemplo: 2.99 o 3.15",
    cancel: "Cancelar",
    save: "Guardar",
    report: "Reportar",
    searching: "Buscando estaciones…",
    emptyTitle: "Sin resultados aún",
    emptyStart: "Escribe tu ZIP o toca Usar mi ubicación.",
    loadLast: "Cargando tu última zona…",
    noStations: "No hay estaciones reales aquí. Prueba 10 millas u otro ZIP.",
    timeout: "Tardó mucho. Prueba de nuevo o escribe un ZIP.",
    searchError: "Error de búsqueda. Prueba un ZIP.",
    stateAvg: (st, price) => `Promedio del estado${st}: ${price}`,
    reported: "reportado",
    estimated: "estimado",
    reportedPrice: "precio reportado",
    saveVsAvg: (p) => `Ahorras ~${p}/gal vs promedio`,
    overAvg: (p) => `${p}/gal sobre el promedio`,
    approxAvg: "≈ promedio",
    stationsByPrice: (n) => `${n} estaciones · por precio`,
    stationsWithReports: (n, ur) => `${n} estaciones · ${ur} con reporte`,
    station: "Estación",
    shareTitle: "⛽ GasRadar — precio de gasolina",
    distance: "Distancia",
    zone: "Zona",
    howTo: "Cómo llegar",
    app: "App",
    contactShare: "Contacto",
    noShare: "No hay precio para compartir",
    copied: "Precio copiado — pégalo a tus amigos",
    copiedShort: "Precio copiado",
    searchFirst: "Busca precios primero",
    needZip: "Escribe un ZIP de USA (ej. 80903)",
    zip5: "ZIP debe tener 5 dígitos",
    invalidPrice: "Pon un precio válido",
    priceRange: "Precio fuera de rango (1–12 USD)",
    saveFail: "No se pudo guardar",
    priceSaved: (p) => `Precio guardado: ${p}`,
    netError: "Error de red al guardar",
    gpsUnavailable: "GPS no disponible. Usa un ZIP (ej. 80903).",
    gpsHttps: "GPS solo funciona con HTTPS. Usa un ZIP.",
    gettingLoc: "Obteniendo tu ubicación…",
    gpsDenied: "Permiso de ubicación denegado. Usa un ZIP.",
    gpsTimeout: "GPS tardó mucho. Usa un ZIP (ej. 80903).",
    noGps: "Sin GPS. Usa un ZIP (Colorado Springs: 80903).",
    reportOf: (name) => `Reportar · ${name}`,
    disclaimerFallback:
      "Estaciones reales. Precios: reportes o estimación. No es precio de bomba en vivo.",
  },
  en: {
    subtitle: "Best prices near you · USA",
    btnGps: "Use my location",
    zipLabel: "ZIP code",
    zipPlaceholder: "ZIP (e.g. 80903)",
    btnSearch: "Search",
    fuelLabel: "Fuel",
    radiusLabel: "Radius",
    mi3: "3 miles",
    mi5: "5 miles",
    mi10: "10 miles",
    mi15: "15 miles",
    noLocation: "No location",
    locHint: "Enter a ZIP or use GPS",
    cheapestBadge: "★ Cheapest",
    directions: "Directions",
    share: "Share",
    nearYou: "Near you",
    loading: "Loading…",
    contact: "Contact:",
    privacy: "Privacy",
    refPrices: "Reference prices",
    reportTitle: "Report price",
    reportSub: "What did you see at the pump? (USD / gallon)",
    reportHint: "Example: 2.99 or 3.15",
    cancel: "Cancel",
    save: "Save",
    report: "Report",
    searching: "Searching stations…",
    emptyTitle: "No results yet",
    emptyStart: "Enter your ZIP or tap Use my location.",
    loadLast: "Loading your last area…",
    noStations: "No real stations here. Try 10 miles or another ZIP.",
    timeout: "Took too long. Try again or enter a ZIP.",
    searchError: "Search error. Try a ZIP.",
    stateAvg: (st, price) => `State average${st}: ${price}`,
    reported: "reported",
    estimated: "estimated",
    reportedPrice: "reported price",
    saveVsAvg: (p) => `Save ~${p}/gal vs average`,
    overAvg: (p) => `${p}/gal above average`,
    approxAvg: "≈ average",
    stationsByPrice: (n) => `${n} stations · by price`,
    stationsWithReports: (n, ur) => `${n} stations · ${ur} with reports`,
    station: "Station",
    shareTitle: "⛽ GasRadar — gas price",
    distance: "Distance",
    zone: "Area",
    howTo: "Directions",
    app: "App",
    contactShare: "Contact",
    noShare: "No price to share",
    copied: "Price copied — paste it to friends",
    copiedShort: "Price copied",
    searchFirst: "Search prices first",
    needZip: "Enter a US ZIP (e.g. 80903)",
    zip5: "ZIP must be 5 digits",
    invalidPrice: "Enter a valid price",
    priceRange: "Price out of range (1–12 USD)",
    saveFail: "Could not save",
    priceSaved: (p) => `Price saved: ${p}`,
    netError: "Network error while saving",
    gpsUnavailable: "GPS unavailable. Use a ZIP (e.g. 80903).",
    gpsHttps: "GPS needs HTTPS. Use a ZIP.",
    gettingLoc: "Getting your location…",
    gpsDenied: "Location permission denied. Use a ZIP.",
    gpsTimeout: "GPS timed out. Use a ZIP (e.g. 80903).",
    noGps: "No GPS. Use a ZIP (Colorado Springs: 80903).",
    reportOf: (name) => `Report · ${name}`,
    disclaimerFallback:
      "Real stations. Prices: user reports or estimates. Not live pump prices.",
  },
};

const state = {
  lat: null,
  lon: null,
  label: "",
  fuel: "regular",
  radius: 5,
  stations: [],
  cheapest: null,
  reportStationId: null,
  reportName: "",
  zip: null,
  searching: false,
  lastData: null,
  lang: loadLang(),
};

function loadLang() {
  try {
    const s = localStorage.getItem(LANG_KEY);
    if (s === "en" || s === "es") return s;
  } catch (_) {}
  const nav = (navigator.language || "es").toLowerCase();
  return nav.startsWith("en") ? "en" : "es";
}

function saveLang(lang) {
  try {
    localStorage.setItem(LANG_KEY, lang);
  } catch (_) {}
}

function t(key, ...args) {
  const pack = I18N[state.lang] || I18N.es;
  const v = pack[key] != null ? pack[key] : I18N.es[key];
  if (typeof v === "function") return v(...args);
  return v != null ? v : key;
}

function applyStaticI18n() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    const val = t(key);
    if (el.tagName === "OPTION") el.textContent = val;
    else el.textContent = val;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (key) el.setAttribute("placeholder", t(key));
  });
  const es = $("#btnLangEs");
  const en = $("#btnLangEn");
  if (es) es.classList.toggle("active", state.lang === "es");
  if (en) en.classList.toggle("active", state.lang === "en");
  document.title =
    state.lang === "en"
      ? "GasRadar — Gas prices USA"
      : "GasRadar — Precios de gasolina USA";
}

function setLang(lang) {
  if (lang !== "es" && lang !== "en") return;
  state.lang = lang;
  saveLang(lang);
  applyStaticI18n();
  if (state.lastData) render(state.lastData);
  else if (!state.searching && state.lat == null && !state.stations.length) {
    const loc = $("#locationLabel");
    const avg = $("#stateAvg");
    if (loc && (!loc.textContent || loc.dataset.i18n)) {
      /* keep */
    }
    if (loc && (loc.textContent === I18N.es.noLocation || loc.textContent === I18N.en.noLocation || loc.getAttribute("data-i18n"))) {
      loc.textContent = t("noLocation");
    }
    if (avg && !state.lastData) avg.textContent = t("locHint");
    const st = $("#status");
    if (st && !st.hidden) setStatus(t("emptyStart"), "empty");
  }
  // Si modal abierto con nombre de estación
  if ($("#modal")?.classList.contains("open") && state.reportName) {
    $("#reportTitle").textContent = t("reportOf", state.reportName);
  }
}

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
    if (o.saved_at && Date.now() - o.saved_at > 30 * 24 * 3600 * 1000) return null;
    return o;
  } catch (_) {
    return null;
  }
}

function money(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
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
  const el =
    $("#toast") ||
    (() => {
      const x = document.createElement("div");
      x.id = "toast";
      x.className = "toast";
      document.body.appendChild(x);
      return x;
    })();
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.remove("show"), 2400);
}

function setLocDot(mode) {
  const dot = $("#locDot");
  if (!dot) return;
  dot.classList.remove("on", "loading");
  if (mode === "on") dot.classList.add("on");
  if (mode === "loading") dot.classList.add("loading");
}

function setBusy(busy) {
  state.searching = busy;
  ["#btnGps", "#btnZip", "#fuelSelect", "#radiusSelect"].forEach((sel) => {
    const el = $(sel);
    if (el) el.disabled = !!busy;
  });
}

function buildShareText(station) {
  const name = station.name || t("station");
  const price = money(station.price);
  const fuel = fuelLabel(state.fuel);
  const dist = station.distance_mi != null ? `${station.distance_mi} mi` : "";
  const zona = state.label || "";
  const maps = mapsUrl(station);
  const appUrl = location.origin + location.pathname;

  let lines = [t("shareTitle"), ``, `${name}`, `${fuel}: ${price}/gal`];
  if (dist) lines.push(`${t("distance")}: ${dist}`);
  if (zona) lines.push(`${t("zone")}: ${zona}`);
  lines.push(``);
  lines.push(`📍 ${t("howTo")}: ${maps}`);
  lines.push(``);
  lines.push(`${t("app")}: ${appUrl}`);
  lines.push(`${t("contactShare")}: contact@gasradarapp.com`);
  return lines.join("\n");
}

async function sharePrice(station) {
  if (!station || station.lat == null) {
    showToast(t("noShare"));
    return;
  }
  const text = buildShareText(station);
  const title = `Gas ${money(station.price)} — ${station.name || "GasRadar"}`;

  if (navigator.share) {
    try {
      await navigator.share({ title, text });
      return;
    } catch (e) {
      if (e && e.name === "AbortError") return;
    }
  }

  const wa = `https://wa.me/?text=${encodeURIComponent(text)}`;
  try {
    window.open(wa, "_blank", "noopener");
    return;
  } catch (_) {
    /* fallthrough */
  }

  try {
    await navigator.clipboard.writeText(text);
    showToast(t("copied"));
  } catch (_) {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    showToast(t("copiedShort"));
  }
}

function detectPlatform() {
  const ua = navigator.userAgent || navigator.vendor || "";
  if (/iPad|iPhone|iPod/i.test(ua)) return "ios";
  if (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1) return "ios";
  if (/Android/i.test(ua)) return "android";
  return "web";
}

/**
 * Enlace de navegación (sin cambios de lógica de maps).
 */
function mapsUrl(stationOrLat, lon, name) {
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

  if (isSearch) {
    if (platform === "ios") {
      return `https://maps.apple.com/?q=${q}`;
    }
    return `https://www.google.com/maps/search/?api=1&query=${q}`;
  }

  if (platform === "ios") {
    return `https://maps.apple.com/?daddr=${dest}&q=${encodeURIComponent(stationName)}&dirflg=d&ll=${dest}`;
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${dest}&destination=${encodeURIComponent(
    stationName
  )}&travelmode=driving`;
}

function mapsButtonLabel() {
  return t("directions");
}

function setStatus(msg, kind = "loading") {
  const el = $("#status");
  if (!el) return;
  el.className = kind;
  if (kind === "empty") {
    el.innerHTML = `<div class="empty-title">${escapeHtml(t("emptyTitle"))}</div>${escapeHtml(msg)}`;
  } else {
    el.textContent = msg;
  }
  el.hidden = false;
  const sk = $("#skeleton");
  if (sk) sk.hidden = kind !== "loading";
  if (kind === "loading") setLocDot("loading");
}

function hideStatus() {
  const el = $("#status");
  if (el) {
    el.hidden = true;
    el.textContent = "";
  }
  const sk = $("#skeleton");
  if (sk) sk.hidden = true;
}

function sourceBadgeHtml(s) {
  if (s.price_source === "user") {
    const n = s.reports_count ? ` · ${s.reports_count}` : "";
    const age = s.price_age_hours != null ? ` · ${s.price_age_hours}h` : "";
    return `<span class="badge user">${t("reported")}${n}${age}</span>`;
  }
  return `<span class="badge estimate">${t("estimated")}</span>`;
}

function rankClass(i) {
  if (i === 0) return "rank gold";
  if (i === 1) return "rank silver";
  if (i === 2) return "rank bronze";
  return "rank";
}

function vsAvgHtml(vs) {
  if (vs == null || Number.isNaN(Number(vs))) return "";
  const v = Number(vs);
  if (Math.abs(v) < 0.005) {
    return `<div class="station-vs">${t("approxAvg")}</div>`;
  }
  if (v < 0) {
    return `<div class="station-vs cheaper">−${money(Math.abs(v))}</div>`;
  }
  return `<div class="station-vs pricier">+${money(v)}</div>`;
}

async function search({ lat, lon, zip } = {}) {
  if (state.searching) return;

  setBusy(true);
  setStatus(t("searching"), "loading");
  $("#results").innerHTML = "";
  const bestCard = $("#bestCard");
  if (bestCard) bestCard.hidden = true;
  const head = $("#resultsHead");
  if (head) head.hidden = true;

  const params = new URLSearchParams();
  params.set("fuel", state.fuel);
  params.set("radius_mi", String(state.radius));
  params.set("limit", "25");
  if (zip) params.set("zip", zip);
  if (lat != null && lon != null) {
    params.set("lat", String(lat));
    params.set("lon", String(lon));
  }

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 25000);

  try {
    const res = await fetch(`/api/search?${params.toString()}`, {
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail =
        typeof err.detail === "string"
          ? err.detail
          : Array.isArray(err.detail)
            ? err.detail.map((d) => d.msg || d).join(", ")
            : null;
      throw new Error(detail || `Error ${res.status}`);
    }
    const data = await res.json();
    state.lat = data.center.lat;
    state.lon = data.center.lon;
    state.label = data.center.label;
    state.stations = data.stations || [];
    state.lastData = data;
    if (zip) state.zip = zip;
    if (data.center && data.center.zip) state.zip = data.center.zip;
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
    clearTimeout(timer);
    setLocDot("off");
    if (e && e.name === "AbortError") {
      setStatus(t("timeout"), "error");
    } else {
      setStatus(e.message || t("searchError"), "error");
    }
  } finally {
    setBusy(false);
  }
}

function render(data) {
  $("#locationLabel").textContent = data.center.label || "—";
  setLocDot("on");

  const avg = data.state_avg || {};
  const fuelAvg = avg[state.fuel] != null ? avg[state.fuel] : avg.regular;
  const st = data.center.state ? ` ${data.center.state}` : "";
  $("#stateAvg").textContent = t("stateAvg", st, money(fuelAvg));

  if (data.cheapest) {
    const b = data.cheapest;
    state.cheapest = b;
    $("#bestCard").hidden = false;
    $("#bestPrice").textContent = money(b.price);
    $("#bestName").textContent = b.name;
    const conf = b.source === "user" ? t("reportedPrice") : t("estimated");
    $("#bestMeta").textContent = `${b.distance_mi} mi · ${conf}`;
    const badge = $("#bestSourceBadge");
    if (badge) {
      if (b.source === "user") {
        badge.textContent = t("reported");
        badge.className = "badge user";
      } else {
        badge.textContent = t("estimated");
        badge.className = "badge estimate";
      }
    }

    const saveEl = $("#bestSave");
    const savings =
      b.savings_vs_avg != null
        ? b.savings_vs_avg
        : b.vs_avg != null
          ? -b.vs_avg
          : null;
    if (saveEl) {
      if (savings != null && savings > 0.004) {
        saveEl.hidden = false;
        saveEl.className = "best-save";
        saveEl.textContent = t("saveVsAvg", money(savings));
      } else if (savings != null && savings < -0.004) {
        saveEl.hidden = false;
        saveEl.className = "best-save over";
        saveEl.textContent = t("overAvg", money(Math.abs(savings)));
      } else {
        saveEl.hidden = true;
      }
    }

    const full =
      state.stations.find((x) => x.id === b.station_id) ||
      state.stations.find((x) => x.name === b.name) ||
      b;
    $("#bestMaps").href = mapsUrl(full);
    $("#bestMaps").textContent = t("directions");
  } else {
    state.cheapest = null;
    $("#bestCard").hidden = true;
  }

  if (!state.stations.length) {
    setStatus(t("noStations"), "empty");
    const head = $("#resultsHead");
    if (head) head.hidden = true;
    $("#disclaimer").textContent = data.disclaimer || t("disclaimerFallback");
    return;
  }

  hideStatus();
  const head = $("#resultsHead");
  if (head) {
    head.hidden = false;
    const cnt = $("#resultsCount");
    if (cnt) {
      const ur = data.user_reports_count || 0;
      cnt.textContent =
        ur > 0
          ? t("stationsWithReports", data.count, ur)
          : t("stationsByPrice", data.count);
    }
  }

  const html = state.stations
    .map((s, i) => {
      const src = sourceBadgeHtml(s);
      const brandBit =
        s.brand &&
        s.brand !== s.name &&
        s.brand !== "Gasolinera" &&
        s.brand.toLowerCase() !== "gas station"
          ? `${escapeHtml(s.brand)} · `
          : "";
      const addr = s.address
        ? `<p class="station-sub">${escapeHtml(s.address)}</p>`
        : "";
      return `
      <article class="station" data-id="${escapeHtml(s.id)}">
        <div class="station-top">
          <div>
            <p class="station-name"><span class="${rankClass(i)}">${i + 1}</span>${escapeHtml(s.name)}</p>
            <p class="station-sub">${brandBit}${s.distance_mi} mi ${src}</p>
            ${addr}
          </div>
          <div class="station-price-col">
            <div class="station-price">${money(s.price)}</div>
            ${vsAvgHtml(s.vs_avg)}
          </div>
        </div>
        <div class="station-actions">
          <a class="btn-ghost" href="${mapsUrl(s)}" target="_blank" rel="noopener">${mapsButtonLabel()}</a>
          <button class="btn-ghost" type="button" data-share="${escapeHtml(s.id)}">${escapeHtml(t("share"))}</button>
          <button class="btn-ghost" type="button" data-report="${escapeHtml(s.id)}" data-name="${escapeHtml(s.name)}">${escapeHtml(t("report"))}</button>
        </div>
      </article>`;
    })
    .join("");

  $("#results").innerHTML = html;
  // Disclaimer API está en español; en EN usamos texto corto local
  if (state.lang === "en") {
    $("#disclaimer").textContent = t("disclaimerFallback");
  } else {
    $("#disclaimer").textContent = data.disclaimer || t("disclaimerFallback");
  }

  $("#results").querySelectorAll("[data-report]").forEach((btn) => {
    btn.addEventListener("click", () =>
      openReport(btn.dataset.report, btn.dataset.name)
    );
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
  state.reportName = name || "";
  $("#reportTitle").textContent = t("reportOf", name || "");
  $("#reportPrice").value = "";
  $("#modal").classList.add("open");
  setTimeout(() => {
    try {
      $("#reportPrice").focus();
    } catch (_) {}
  }, 80);
}

function closeReport() {
  $("#modal").classList.remove("open");
  state.reportStationId = null;
  state.reportName = "";
}

async function submitReport() {
  const raw = ($("#reportPrice").value || "").trim();
  const price = parseFloat(raw);
  if (!state.reportStationId || Number.isNaN(price)) {
    showToast(t("invalidPrice"));
    return;
  }
  if (price < 1 || price > 12) {
    showToast(t("priceRange"));
    return;
  }

  const btn = $("#btnSubmitReport");
  if (btn) btn.disabled = true;

  try {
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
      showToast(err.detail || t("saveFail"));
      return;
    }
    closeReport();
    showToast(t("priceSaved", money(price)));
    await search({ lat: state.lat, lon: state.lon, zip: state.zip || undefined });
  } catch (_) {
    showToast(t("netError"));
  } finally {
    if (btn) btn.disabled = false;
  }
}

function useGps() {
  if (!navigator.geolocation) {
    setStatus(t("gpsUnavailable"), "error");
    return;
  }
  if (
    window.isSecureContext !== true &&
    !["localhost", "127.0.0.1"].includes(location.hostname)
  ) {
    setStatus(t("gpsHttps"), "error");
    return;
  }
  setStatus(t("gettingLoc"), "loading");
  setLocDot("loading");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      state.zip = null;
      search({ lat: pos.coords.latitude, lon: pos.coords.longitude });
    },
    (err) => {
      setLocDot("off");
      const code = err && err.code;
      if (code === 1) setStatus(t("gpsDenied"), "error");
      else if (code === 3) setStatus(t("gpsTimeout"), "error");
      else setStatus(t("noGps"), "error");
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 }
  );
}

function startApp() {
  applyStaticI18n();
  const saved = loadSavedLocation();
  if (saved) {
    state.zip = saved.zip || null;
    if (saved.zip && $("#zipInput")) $("#zipInput").value = saved.zip;
    setStatus(t("loadLast"), "loading");
    if (saved.zip) search({ zip: saved.zip });
    else search({ lat: saved.lat, lon: saved.lon });
    return;
  }

  setStatus(t("emptyStart"), "empty");
  $("#locationLabel").textContent = t("noLocation");
  $("#stateAvg").textContent = t("locHint");
  setLocDot("off");

  if (
    navigator.geolocation &&
    (window.isSecureContext === true ||
      ["localhost", "127.0.0.1"].includes(location.hostname))
  ) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (!state.stations.length && state.lat == null && !state.searching) {
          search({ lat: pos.coords.latitude, lon: pos.coords.longitude });
        }
      },
      () => {},
      { enableHighAccuracy: false, timeout: 6000, maximumAge: 120000 }
    );
  }
}

function bind() {
  $("#btnLangEs")?.addEventListener("click", () => setLang("es"));
  $("#btnLangEn")?.addEventListener("click", () => setLang("en"));

  const bestShare = $("#bestShare");
  if (bestShare) {
    bestShare.addEventListener("click", () => {
      if (state.cheapest) sharePrice(state.cheapest);
      else if (state.stations[0]) sharePrice(state.stations[0]);
      else showToast(t("searchFirst"));
    });
  }
  $("#btnGps").addEventListener("click", useGps);
  $("#btnZip").addEventListener("click", () => {
    const zip = $("#zipInput").value.trim();
    if (!zip) {
      showToast(t("needZip"));
      $("#zipInput").focus();
      return;
    }
    const digits = zip.replace(/\D/g, "");
    if (digits.length < 5) {
      showToast(t("zip5"));
      return;
    }
    state.zip = digits.slice(0, 5);
    search({ zip: state.zip });
  });
  $("#zipInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("#btnZip").click();
  });
  $("#zipInput").addEventListener("input", (e) => {
    const v = e.target.value.replace(/[^\d-]/g, "").slice(0, 10);
    if (v !== e.target.value) e.target.value = v;
  });
  $("#fuelSelect").addEventListener("change", (e) => {
    state.fuel = e.target.value;
    if (state.lat != null) {
      search({
        lat: state.lat,
        lon: state.lon,
        zip: state.zip || undefined,
      });
    }
  });
  $("#radiusSelect").addEventListener("change", (e) => {
    state.radius = Number(e.target.value);
    if (state.lat != null) {
      search({
        lat: state.lat,
        lon: state.lon,
        zip: state.zip || undefined,
      });
    }
  });
  $("#btnCloseModal").addEventListener("click", closeReport);
  $("#btnSubmitReport").addEventListener("click", submitReport);
  $("#reportPrice").addEventListener("keydown", (e) => {
    if (e.key === "Enter") submitReport();
  });
  $("#modal").addEventListener("click", (e) => {
    if (e.target.id === "modal") closeReport();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && $("#modal").classList.contains("open")) {
      closeReport();
    }
  });
}

bind();
startApp();
