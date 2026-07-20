const $ = (sel) => document.querySelector(sel);

const STORAGE_KEY = "gasradar_last_location";
const LANG_KEY = "gasradar_lang";

const I18N = {
  es: {
    subtitle: "Gasolina más barata cerca de ti",
    footerValue: "Gasolina más barata cerca de ti · compara por GPS o ZIP",
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
    eiaTitle: "Promedio esta semana",
    eiaNote: "Promedio del estado esta semana · no es el precio de cada bomba",
    eiaWeek: (period) => (period ? `Semana del ${period}` : "Promedio semanal"),
    eiaStateLine: (st, fuel) => `${st} · ${fuel}`,
    eiaBadge: "prom. sem.",
    eiaChipLabel: "prom. sem.",
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
    gpsRetrying: "Afinando GPS… un momento",
    gpsDenied: "Permiso de ubicación denegado. Actívalo en el navegador o usa un ZIP.",
    gpsTimeout: "GPS tardó mucho. Prueba de nuevo o escribe un ZIP.",
    noGps: "No se pudo ubicar. Escribe un ZIP (ej. 80903).",
    gpsOk: (m) => `Ubicación OK (±${m} m)`,
    gpsWeak: "Ubicación poco precisa — si falla, usa un ZIP",
    gpsBusy: "Ya estamos obteniendo la ubicación…",
    reportOf: (name) => `Reportar · ${name}`,
    disclaimerFallback:
      "Estaciones reales. Precios: reportes o estimación. No es precio de bomba en vivo.",
    installApp: "Instalar app",
    installOk: "GasRadar listo para instalar",
    installDone: "App instalada — búscala en tu pantalla de inicio",
    installIos:
      "En iPhone: toca Compartir → Añadir a pantalla de inicio",
    installAlready: "Ya está instalada o ábrela desde el icono del teléfono",
    telegramAlerts: "Alertas",
    trustpilotReview: "Deja una reseña",
    buyMeCoffee: "Apóyame",
    pullHint: "Desliza para actualizar",
    pullRelease: "Suelta para actualizar",
    pullRefreshing: "Actualizando precios…",
    pullDone: "Precios actualizados",
  },
  en: {
    subtitle: "Cheapest gas near you",
    footerValue: "Cheapest gas near you · search by GPS or ZIP",
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
    eiaTitle: "This week's average",
    eiaNote: "State average this week · not the price at each pump",
    eiaWeek: (period) => (period ? `Week of ${period}` : "Weekly average"),
    eiaStateLine: (st, fuel) => `${st} · ${fuel}`,
    eiaBadge: "wk avg",
    eiaChipLabel: "wk avg",
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
    gpsRetrying: "Refining GPS… one moment",
    gpsDenied: "Location denied. Enable it in the browser or use a ZIP.",
    gpsTimeout: "GPS timed out. Try again or enter a ZIP.",
    noGps: "Couldn't locate you. Enter a ZIP (e.g. 80903).",
    gpsOk: (m) => `Location OK (±${m} m)`,
    gpsWeak: "Location is rough — if results look wrong, use a ZIP",
    gpsBusy: "Already getting your location…",
    reportOf: (name) => `Report · ${name}`,
    disclaimerFallback:
      "Real stations. Prices: user reports or estimates. Not live pump prices.",
    installApp: "Install app",
    installOk: "GasRadar is ready to install",
    installDone: "App installed — find it on your home screen",
    installIos: "On iPhone: tap Share → Add to Home Screen",
    installAlready: "Already installed, or open it from the home screen icon",
    telegramAlerts: "Alerts",
    trustpilotReview: "Leave a review",
    buyMeCoffee: "Support",
    pullHint: "Pull to refresh",
    pullRelease: "Release to refresh",
    pullRefreshing: "Updating prices…",
    pullDone: "Prices updated",
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
  // Título fijo (no cambiar): GasRadar — Gas prices USA
  document.title = "GasRadar — Gas prices USA";
  const metaDesc = document.getElementById("metaDesc");
  if (metaDesc) {
    metaDesc.setAttribute(
      "content",
      state.lang === "en"
        ? "Find the cheapest gas near you in the USA. Compare prices by GPS or ZIP with GasRadar."
        : "Gasolina más barata cerca de ti en USA. Compara precios por GPS o ZIP con GasRadar. Encuentra la estación más barata al instante."
    );
  }
  // Actualiza chip "prom. sem." / "wk avg" al cambiar idioma
  if (state.lastData) renderEiaBanner(state.lastData);
  else {
    const badge = $("#eiaBadge");
    if (badge) badge.textContent = t("eiaChipLabel");
    const chip = $("#eiaBanner");
    if (chip) chip.title = t("eiaNote");
  }
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

/** Precio estilo GasBuddy: recuadro + dólares grandes + centavos arriba */
function priceBoxHtml(n, { large = false } = {}) {
  const cls = large ? "price-box large" : "price-box";
  if (n == null || Number.isNaN(Number(n))) {
    return `<div class="${cls}"><span class="price-whole">—</span></div>`;
  }
  const fixed = Number(n).toFixed(2);
  const [whole, cents] = fixed.split(".");
  return `<div class="${cls}" title="${money(n)}"><span class="price-currency">$</span><span class="price-whole">${whole}</span><span class="price-cents">${cents}</span></div>`;
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
  if (s.price_source === "zyla" || s.price_source === "gasbuddy") {
    return `<span class="badge eia">${state.lang === "en" ? "live" : "en vivo"}</span>`;
  }
  if (s.price_source === "zyla_estimate") {
    return `<span class="badge eia">Zyla</span>`;
  }
  return `<span class="badge estimate">${t("estimated")}</span>`;
}

/** Slug de logo local /static/brands/{slug}.svg — genérico si no hay marca */
const BRAND_LOGO_PATTERNS = [
  ["sam's club", "sams-club"],
  ["sams club", "sams-club"],
  ["king soopers", "king-soopers"],
  ["7-eleven", "7-eleven"],
  ["7 eleven", "7-eleven"],
  ["7-11", "7-eleven"],
  ["circle k", "circle-k"],
  ["phillips 66", "phillips-66"],
  ["phillip 66", "phillips-66"],
  ["phillips66", "phillips-66"],
  ["diamond shamrock", "diamond-shamrock"],
  ["murphy usa", "murphy"],
  ["kum & go", "kum-go"],
  ["kum and go", "kum-go"],
  ["flying j", "flying-j"],
  ["loaf 'n jug", "loaf-n-jug"],
  ["loaf n jug", "loaf-n-jug"],
  ["loaf'n jug", "loaf-n-jug"],
  ["quiktrip", "quiktrip"],
  ["quicktrip", "quiktrip"],
  ["u pump it", "u-pump-it"],
  ["upumpit", "u-pump-it"],
  ["love's", "loves"],
  ["loves", "loves"],
  ["casey's", "caseys"],
  ["caseys", "caseys"],
  ["race trac", "racetrac"],
  ["racetrac", "racetrac"],
  ["raceway", "racetrac"],
  ["shell", "shell"],
  ["chevron", "chevron"],
  ["exxon", "exxon"],
  ["mobil", "mobil"],
  ["arco", "arco"],
  ["costco", "costco"],
  ["walmart", "walmart"],
  ["safeway", "safeway"],
  ["conoco", "conoco"],
  ["sinclair", "sinclair"],
  ["valero", "valero"],
  ["maverik", "maverik"],
  ["holiday", "holiday"],
  ["cenex", "cenex"],
  ["texaco", "texaco"],
  ["kroger", "kroger"],
  ["murphy", "murphy"],
  ["speedway", "speedway"],
  ["pilot", "pilot"],
  ["marathon", "marathon"],
  ["sunoco", "sunoco"],
  ["wawa", "wawa"],
  ["sheetz", "sheetz"],
  ["citgo", "citgo"],
  ["getgo", "getgo"],
  ["get go", "getgo"],
  ["alon", "valero"],
  ["qt", "quiktrip"],
  ["bp", "bp"],
];

function brandLogoSlug(station) {
  const blob = `${station?.brand || ""} ${station?.name || ""}`.toLowerCase();
  for (const [needle, slug] of BRAND_LOGO_PATTERNS) {
    if (needle === "bp") {
      if (/(?:^|[^a-z])bp(?:[^a-z]|$)/.test(blob)) return slug;
      continue;
    }
    if (needle === "qt") {
      if (/(?:^|[^a-z])qt(?:[^a-z]|$)/.test(blob)) return slug;
      continue;
    }
    if (blob.includes(needle)) return slug;
  }
  return "generic";
}

function brandLogoSrc(slug) {
  const data = typeof BRAND_LOGO_DATA !== "undefined" ? BRAND_LOGO_DATA : null;
  if (data && data[slug]) return data[slug];
  if (data && data.generic) return data.generic;
  // Fallback por si falta brand-logos.js (archivo estático)
  return `/static/brands/${slug || "generic"}.svg?v=0.9.1`;
}

function brandLogoHtml(station) {
  const slug = brandLogoSlug(station);
  const label = station?.brand || station?.name || "Gas";
  const src = brandLogoSrc(slug);
  // data-URI inline — no depende de /static/brands ni de red
  return `<img class="station-logo" src="${src}" width="40" height="40" alt="" decoding="async" data-brand="${escapeHtml(slug)}" title="${escapeHtml(label)}" onerror="this.onerror=null;if(window.BRAND_LOGO_DATA&amp;&amp;BRAND_LOGO_DATA.generic)this.src=BRAND_LOGO_DATA.generic" />`;
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

/* Cache local: misma búsqueda = respuesta al instante (8 min) */
const _searchMem = new Map();
const SEARCH_MEM_MS = 8 * 60 * 1000;

function searchMemKey({ lat, lon, zip }) {
  const z = zip || state.zip || "";
  const la = lat != null ? Number(lat).toFixed(3) : "";
  const lo = lon != null ? Number(lon).toFixed(3) : "";
  return `${z}|${la}|${lo}|${state.fuel}|${state.radius}`;
}

function applySearchData(data, { zip } = {}) {
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
}

async function search({ lat, lon, zip, force = false, soft = false } = {}) {
  if (state.searching) return;

  const memKey = searchMemKey({ lat, lon, zip });
  if (force) {
    try {
      _searchMem.delete(memKey);
    } catch (_) {
      /* ignore */
    }
  } else {
    const memHit = _searchMem.get(memKey);
    if (memHit && Date.now() - memHit.ts < SEARCH_MEM_MS && memHit.data) {
      applySearchData(memHit.data, { zip });
      return;
    }
  }

  setBusy(true);
  // soft = pull-to-refresh: no vaciar lista (como GasBuddy)
  if (!soft) {
    setStatus(t("searching"), "loading");
    $("#results").innerHTML = "";
    const bestCard = $("#bestCard");
    if (bestCard) bestCard.hidden = true;
    const head = $("#resultsHead");
    if (head) head.hidden = true;
  }

  const params = new URLSearchParams();
  params.set("fuel", state.fuel);
  params.set("radius_mi", String(state.radius));
  params.set("limit", "20");
  if (zip) params.set("zip", zip);
  if (lat != null && lon != null) {
    params.set("lat", String(lat));
    params.set("lon", String(lon));
  }

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 22000);

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
    try {
      _searchMem.set(memKey, { ts: Date.now(), data });
      if (_searchMem.size > 40) {
        const first = _searchMem.keys().next().value;
        _searchMem.delete(first);
      }
    } catch (_) {
      /* ignore */
    }
    applySearchData(data, { zip });
  } catch (e) {
    clearTimeout(timer);
    if (soft) {
      // pull-to-refresh: mantener lista y avisar
      showToast(e && e.name === "AbortError" ? t("timeout") : e.message || t("searchError"));
    } else {
      setLocDot("off");
      if (e && e.name === "AbortError") {
        setStatus(t("timeout"), "error");
      } else {
        setStatus(e.message || t("searchError"), "error");
      }
    }
  } finally {
    setBusy(false);
  }
}

function renderEiaBanner(data) {
  // Chip siempre visible en header: "prom. sem. $3.72"
  const chip = $("#eiaBanner");
  if (!chip) return;
  const avg = (data && data.state_avg) || {};
  const fuelAvg = avg[state.fuel] != null ? avg[state.fuel] : avg.regular;
  const stCode = (data && data.center && data.center.state) || "";

  const badge = $("#eiaBadge");
  const text = $("#eiaChipText");
  if (badge) badge.textContent = t("eiaChipLabel");
  if (text) {
    text.textContent =
      fuelAvg != null && !Number.isNaN(Number(fuelAvg)) ? money(fuelAvg) : "$—";
  }
  chip.hidden = false;
  chip.title = stCode ? `${stCode} · ${t("eiaNote")}` : t("eiaNote");
  chip.setAttribute(
    "aria-label",
    `${t("eiaChipLabel")} ${text ? text.textContent : ""}`.trim()
  );
}

function render(data) {
  $("#locationLabel").textContent = data.center.label || "—";
  setLocDot("on");

  // Ubicación en loc-box; el promedio va solo en el chip chico del header
  const fuel = fuelLabel(state.fuel);
  $("#stateAvg").textContent = data.center.state
    ? `${data.center.state} · ${fuel}`
    : fuel;
  renderEiaBanner(data);

  // Deep-link al bot con ZIP actual
  const tg = $("#btnTelegram");
  if (tg && data.center && data.center.zip) {
    tg.href = `https://t.me/GasRadar_bot?start=${encodeURIComponent(data.center.zip)}`;
  }

  if (data.cheapest) {
    const b = data.cheapest;
    state.cheapest = b;
    $("#bestCard").hidden = false;
    $("#bestPrice").innerHTML = priceBoxHtml(b.price, { large: true });
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
          ${brandLogoHtml(s)}
          <div class="station-info">
            <p class="station-name"><span class="${rankClass(i)}">${i + 1}</span>${escapeHtml(s.name)}</p>
            <p class="station-sub">${brandBit}${s.distance_mi} mi ${src}</p>
            ${addr}
          </div>
          <div class="station-price-col">
            ${priceBoxHtml(s.price)}
            ${vsAvgHtml(s.vs_avg)}
          </div>
        </div>
        <div class="station-actions">
          <button class="btn-ghost" type="button" data-maps="${escapeHtml(s.id)}">${escapeHtml(mapsButtonLabel())}</button>
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

  $("#results").querySelectorAll("[data-maps]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.getAttribute("data-maps");
      const st = state.stations.find((x) => x.id === id);
      if (!st) return;
      const url = mapsUrl(st);
      try {
        window.open(url, "_blank", "noopener");
      } catch (_) {
        location.href = url;
      }
    });
  });
  $("#results").querySelectorAll("[data-report]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openReport(btn.dataset.report, btn.dataset.name);
    });
  });
  $("#results").querySelectorAll("[data-share]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.getAttribute("data-share");
      const st = state.stations.find((x) => x.id === id);
      if (st) sharePrice(st);
    });
  });

  // Resaltado al tocar la tarjeta (feedback tipo “entrar”, sin mapa)
  bindStationPressFeedback($("#results"));
}

function bindStationPressFeedback(root) {
  if (!root) return;
  const clear = (el) => el && el.classList.remove("is-pressed");

  root.querySelectorAll(".station").forEach((card) => {
    const isAction = (t) =>
      t && (t.closest("a") || t.closest("button") || t.closest("input"));

    card.addEventListener(
      "pointerdown",
      (e) => {
        if (e.button != null && e.button !== 0) return;
        if (isAction(e.target)) return;
        // limpia selección nativa (iOS/Android a veces “copia” el texto)
        try {
          const sel = window.getSelection && window.getSelection();
          if (sel && sel.removeAllRanges) sel.removeAllRanges();
        } catch (_) {
          /* ignore */
        }
        card.classList.add("is-pressed");
      },
      { passive: true }
    );
    card.addEventListener(
      "pointerup",
      () => clear(card),
      { passive: true }
    );
    card.addEventListener(
      "pointercancel",
      () => clear(card),
      { passive: true }
    );
    card.addEventListener(
      "pointerleave",
      () => clear(card),
      { passive: true }
    );
    // si el dedo se mueve (scroll), quitar resaltado
    card.addEventListener(
      "touchmove",
      () => clear(card),
      { passive: true }
    );
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

/** GPS mejorado: rápido → preciso → feedback de precisión → ZIP si falla */
let gpsBusy = false;

function gpsSecureOk() {
  return (
    window.isSecureContext === true ||
    ["localhost", "127.0.0.1"].includes(location.hostname)
  );
}

function getGpsPosition(options) {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject({ code: 0, message: "no geolocation" });
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, options);
  });
}

function focusZipFallback() {
  const zip = $("#zipInput");
  if (zip) {
    try {
      zip.focus({ preventScroll: false });
    } catch (_) {
      zip.focus();
    }
  }
}

function handleGpsError(err) {
  setLocDot("off");
  const code = err && err.code;
  if (code === 1) setStatus(t("gpsDenied"), "error");
  else if (code === 3) setStatus(t("gpsTimeout"), "error");
  else setStatus(t("noGps"), "error");
  focusZipFallback();
}

async function useGps() {
  if (gpsBusy) {
    showToast(t("gpsBusy"));
    return;
  }
  if (!navigator.geolocation) {
    setStatus(t("gpsUnavailable"), "error");
    focusZipFallback();
    return;
  }
  if (!gpsSecureOk()) {
    setStatus(t("gpsHttps"), "error");
    focusZipFallback();
    return;
  }

  const btn = $("#btnGps");
  gpsBusy = true;
  if (btn) btn.disabled = true;
  setStatus(t("gettingLoc"), "loading");
  setLocDot("loading");

  try {
    let pos = null;

    // 1) Rápido: red/wifi, cache reciente (mejor en ciudad)
    try {
      pos = await getGpsPosition({
        enableHighAccuracy: false,
        timeout: 8000,
        maximumAge: 60000,
      });
    } catch (e1) {
      if (e1 && e1.code === 1) {
        // Permiso denegado: no reintentar
        handleGpsError(e1);
        return;
      }
      // 2) Preciso: GPS del chip
      setStatus(t("gpsRetrying"), "loading");
      pos = await getGpsPosition({
        enableHighAccuracy: true,
        timeout: 14000,
        maximumAge: 0,
      });
    }

    let lat = pos.coords.latitude;
    let lon = pos.coords.longitude;
    let accuracy =
      typeof pos.coords.accuracy === "number" ? pos.coords.accuracy : null;

    // 3) Si la precisión es muy mala (> ~1.5 km), un reintento de alta precisión
    if (accuracy != null && accuracy > 1500) {
      setStatus(t("gpsRetrying"), "loading");
      try {
        const pos2 = await getGpsPosition({
          enableHighAccuracy: true,
          timeout: 12000,
          maximumAge: 0,
        });
        const a2 =
          typeof pos2.coords.accuracy === "number"
            ? pos2.coords.accuracy
            : null;
        if (a2 == null || a2 < accuracy) {
          lat = pos2.coords.latitude;
          lon = pos2.coords.longitude;
          accuracy = a2;
        }
      } catch (_) {
        /* nos quedamos con la primera */
      }
    }

    state.zip = null;
    state.gpsAccuracy = accuracy;

    if (accuracy != null && accuracy <= 80) {
      showToast(t("gpsOk", Math.round(accuracy)));
    } else if (accuracy != null && accuracy > 500) {
      showToast(t("gpsWeak"));
    }

    await search({ lat, lon });
  } catch (err) {
    handleGpsError(err);
  } finally {
    gpsBusy = false;
    if (btn) btn.disabled = false;
  }
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

  // Auto-GPS silencioso solo si no hay zona guardada (rápido, no molesta)
  if (navigator.geolocation && gpsSecureOk()) {
    getGpsPosition({
      enableHighAccuracy: false,
      timeout: 7000,
      maximumAge: 180000,
    })
      .then((pos) => {
        if (!state.stations.length && state.lat == null && !state.searching && !gpsBusy) {
          search({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
          });
        }
      })
      .catch(() => {
        /* silencioso: el usuario puede tocar el botón o usar ZIP */
      });
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

  setupPullToRefresh();
  bindBestCardPress();
}

function bindBestCardPress() {
  const card = $("#bestCard");
  if (!card) return;
  const clear = () => card.classList.remove("is-pressed");
  const isAction = (t) =>
    t && (t.closest("a") || t.closest("button") || t.closest("input"));

  card.addEventListener(
    "pointerdown",
    (e) => {
      if (e.button != null && e.button !== 0) return;
      if (isAction(e.target)) return;
      try {
        const sel = window.getSelection && window.getSelection();
        if (sel && sel.removeAllRanges) sel.removeAllRanges();
      } catch (_) {
        /* ignore */
      }
      card.classList.add("is-pressed");
    },
    { passive: true }
  );
  card.addEventListener("pointerup", clear, { passive: true });
  card.addEventListener("pointercancel", clear, { passive: true });
  card.addEventListener("pointerleave", clear, { passive: true });
  card.addEventListener("touchmove", clear, { passive: true });
}

/* ——— Pull-to-refresh estilo GasBuddy ——— */
function setupPullToRefresh() {
  const ptr = $("#ptr");
  const label = $("#ptrLabel");
  const ring = $("#ptrRing");
  if (!ptr) return;

  const THRESHOLD = 70;
  const MAX = 118;
  let startY = 0;
  let pulling = false;
  let armed = false;
  let dist = 0;
  let refreshing = false;

  function pageScrollTop() {
    return window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
  }

  function setPtr(px, mode) {
    dist = px;
    const ready = px >= THRESHOLD;
    ptr.classList.toggle("visible", px > 4 || mode === "refreshing");
    ptr.classList.toggle("ready", ready && mode !== "refreshing");
    ptr.classList.toggle("refreshing", mode === "refreshing");
    ptr.style.setProperty("--ptr-pull", `${Math.min(MAX, px)}px`);
    if (ring) {
      // anillo que se llena al tirar
      const p = Math.min(1, px / THRESHOLD);
      ring.style.setProperty("--ptr-p", String(p));
      if (mode === "refreshing") {
        ring.style.transform = "";
      } else {
        ring.style.transform = `rotate(${p * 280}deg)`;
      }
    }
    if (label) {
      if (mode === "refreshing") label.textContent = t("pullRefreshing");
      else if (ready) label.textContent = t("pullRelease");
      else label.textContent = t("pullHint");
    }
  }

  function resetPtr(animate) {
    if (animate) ptr.classList.add("snap");
    else ptr.classList.remove("snap");
    setPtr(0, "idle");
    if (animate) {
      setTimeout(() => ptr.classList.remove("snap"), 280);
    }
  }

  async function refreshFromPull() {
    if (refreshing || state.searching) {
      resetPtr(true);
      return;
    }
    if (state.lat == null && !state.zip) {
      resetPtr(true);
      showToast(t("searchFirst"));
      return;
    }

    refreshing = true;
    setPtr(Math.min(THRESHOLD + 8, MAX * 0.72), "refreshing");
    document.body.classList.add("ptr-busy");

    try {
      await search({
        lat: state.lat,
        lon: state.lon,
        zip: state.zip || undefined,
        force: true,
        soft: true,
      });
      showToast(t("pullDone"));
    } catch (_) {
      /* search ya muestra error */
    } finally {
      refreshing = false;
      document.body.classList.remove("ptr-busy");
      resetPtr(true);
    }
  }

  document.addEventListener(
    "touchstart",
    (e) => {
      if (refreshing || state.searching) return;
      if ($("#modal")?.classList.contains("open")) return;
      if (pageScrollTop() > 4) {
        armed = false;
        pulling = false;
        return;
      }
      // no activar en inputs / selects
      const tag = (e.target && e.target.tagName) || "";
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA" || e.target.isContentEditable) {
        armed = false;
        return;
      }
      startY = e.touches[0].clientY;
      armed = true;
      pulling = false;
      dist = 0;
    },
    { passive: true }
  );

  document.addEventListener(
    "touchmove",
    (e) => {
      if (!armed || refreshing) return;
      if (pageScrollTop() > 4) {
        armed = false;
        if (pulling) resetPtr(false);
        pulling = false;
        return;
      }
      const dy = e.touches[0].clientY - startY;
      if (dy < 8) {
        if (pulling && dy <= 0) {
          pulling = false;
          resetPtr(false);
        }
        return;
      }
      // resistencia tipo goma (GasBuddy)
      const resisted = Math.min(MAX, dy * 0.42);
      pulling = true;
      setPtr(resisted, "pull");
      // bloquear scroll nativo mientras tiramos
      if (resisted > 6) {
        try {
          e.preventDefault();
        } catch (_) {
          /* ignore */
        }
      }
    },
    { passive: false }
  );

  const endPull = () => {
    if (!armed && !pulling) return;
    armed = false;
    if (!pulling) return;
    pulling = false;
    if (dist >= THRESHOLD && !refreshing) {
      refreshFromPull();
    } else {
      resetPtr(true);
    }
  };

  document.addEventListener("touchend", endPull, { passive: true });
  document.addEventListener("touchcancel", endPull, { passive: true });
}

function trackVisit() {
  try {
    const body = {
      path: location.pathname || "/",
      referrer: document.referrer || "",
      lang: state.lang || document.documentElement.lang || "",
    };
    // no bloquear la app si falla
    fetch("/api/visit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      keepalive: true,
    }).catch(() => {});
  } catch (_) {
    /* ignore */
  }
}

/* ——— PWA: instalar + service worker ——— */
let deferredInstallPrompt = null;

function isStandaloneApp() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

function isIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent || "");
}

function showInstallButton(show) {
  const btn = $("#btnInstall");
  if (!btn) return;
  if (isStandaloneApp()) {
    btn.hidden = true;
    return;
  }
  btn.hidden = !show;
}

function setupPwaInstall() {
  const btn = $("#btnInstall");
  if (!btn) return;

  // Android/Chrome: evento nativo de instalar
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    showInstallButton(true);
  });

  window.addEventListener("appinstalled", () => {
    deferredInstallPrompt = null;
    showInstallButton(false);
    showToast(t("installDone"));
  });

  // iOS: mostrar botón con instrucciones (no hay prompt nativo)
  if (isIos() && !isStandaloneApp()) {
    showInstallButton(true);
  }

  btn.addEventListener("click", async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      try {
        const choice = await deferredInstallPrompt.userChoice;
        if (choice && choice.outcome === "accepted") {
          showToast(t("installDone"));
        }
      } catch (_) {
        /* ignore */
      }
      deferredInstallPrompt = null;
      showInstallButton(false);
      return;
    }
    if (isIos()) {
      showToast(t("installIos"));
      return;
    }
    if (isStandaloneApp()) {
      showToast(t("installAlready"));
      return;
    }
    showToast(t("installAlready"));
  });
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  // solo en https o localhost
  const ok =
    window.isSecureContext ||
    ["localhost", "127.0.0.1"].includes(location.hostname);
  if (!ok) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {
      /* ignore: PWA opcional */
    });
  });
}

bind();
setupPwaInstall();
registerServiceWorker();
trackVisit();
startApp();
