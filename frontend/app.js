const $ = (sel) => document.querySelector(sel);

const STORAGE_KEY = "gasradar_last_location";
const LANG_KEY = "gasradar_lang";

const I18N = {
  es: {
    subtitle: "Gasolina más barata cerca de ti",
    footerValue: "Gasolina más barata cerca de ti · compara por GPS o ZIP",
    footerLegal: "© 2026 GasRadar LLC · gasradarapp.com",
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
    wageTitle: "Horas para llenar el tanque",
    wageGallons: "Galones del tanque",
    wageGalShort: "gal",
    wageWork: "de trabajo",
    wageNote: "Sueldo mínimo estatal × el precio más barato cerca. En algunas ciudades pagan más.",
    wageLine: (st, wage, gal, cost, hours) =>
      `En ${st} el mínimo es $${wage}/h. Llenar ${gal} gal cuesta ~$${cost} = ${hours} h de trabajo.`,
    wageHours: (h) => (h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(1)} h`),
    directions: "Cómo llegar",
    navOpenTitle: "Cómo llegar",
    navOpenHint: "Se abrirá Apple Maps o Google Maps. GasRadar se queda aquí.",
    navOpenBtn: "Abrir mapas",
    navStayBtn: "Cancelar",
    navOpening: "Abriendo navegación…",
    share: "Compartir",
    nearYou: "Cerca de ti",
    loading: "Cargando…",
    contact: "Contacto:",
    privacy: "Privacidad",
    blog: "Blog",
    places: "Ciudades",
    waChannel: "Canal WhatsApp",
    pressTelemundo: "Salimos en Telemundo Denver",
    refPrices: "Precios de referencia",
    reportTitle: "Reportar precio",
    reportSub: "¿Cuánto viste en la bomba? (USD / galón)",
    reportHint: "Ejemplo: 2.99 o 3.15",
    cancel: "Cancelar",
    save: "Guardar",
    report: "Reportar",
    searching: "Buscando estaciones…",
    searchingStill: "Aún buscando precios en vivo…",
    searchingZip: (z) => `Buscando ZIP ${z}…`,
    searchingZipChange: (z) => `Cambiando a ZIP ${z}… (mantenemos la lista anterior un momento)`,
    terms: "Términos",
    rules: "Reglas",
    emptyTitle: "Sin resultados aún",
    emptyStart: "Escribe tu ZIP o toca Usar mi ubicación.",
    loadLast: "Cargando tu última zona…",
    noStations: "No hay estaciones reales aquí. Prueba 10 millas u otro ZIP.",
    timeout: "La red tardó. Espera un momento: seguimos cargando esa zona.",
    timeoutSoft: "Aún cargando precios de esa zona…",
    searchError: "Error de búsqueda. Prueba un ZIP.",
    stateAvg: (st, price) => `Promedio del estado${st}: ${price}`,
    eiaTitle: "Promedio esta semana",
    eiaNote: "Promedio del estado esta semana · no es el precio de cada bomba",
    eiaWeek: (period) => (period ? `Semana del ${period}` : "Promedio semanal"),
    eiaStateLine: (st, fuel) => `${st} · ${fuel}`,
    eiaBadge: "prom. sem.",
    eiaChipLabel: "prom. sem.",
    reported: "reportado",
    estimated: "referencia",
    livePrice: "en vivo",
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
    playGet: "Disponible en Google Play",
    playBanner: "Ya estamos en Google Play",
    playBannerCta: "Descargar",
    footerPlay: "App Android",
    installApp: "Instalar app",
    installOk: "GasRadar listo para instalar",
    installDone: "App instalada — búscala en tu pantalla de inicio",
    installIos:
      "En iPhone: toca Compartir → Añadir a pantalla de inicio",
    installAlready: "Ya está instalada o ábrela desde el icono del teléfono",
    telegramAlerts: "Alertas",
    trustpilotReview: "Deja una reseña",
    buyMeCoffee: "Dóname",
    donate: "Dóname",
    donateTitle: "Dóname lo que quieras",
    donateSub: "Elige un monto o pon el tuyo. Pago seguro con Stripe.",
    donateHint: "Mínimo $1 · tú eliges cuánto",
    donatePay: "Donar con Stripe",
    donateThanks: "¡Gracias por tu donación! 💛",
    donateCancel: "Donación cancelada",
    donateErr: "No se pudo abrir Stripe. Intenta de nuevo.",
    donateBusy: "Abriendo Stripe…",
    pullHint: "Desliza para actualizar",
    pullRelease: "Suelta para actualizar",
    pullRefreshing: "Actualizando precios…",
    pullDone: "Precios actualizados",
  },
  en: {
    subtitle: "Cheapest gas near you",
    footerValue: "Cheapest gas near you · search by GPS or ZIP",
    footerLegal: "© 2026 GasRadar LLC · gasradarapp.com",
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
    wageTitle: "Hours to fill the tank",
    wageGallons: "Tank size (gallons)",
    wageGalShort: "gal",
    wageWork: "of work",
    wageNote: "State minimum wage × cheapest nearby price. Some cities pay more.",
    wageLine: (st, wage, gal, cost, hours) =>
      `In ${st} the minimum is $${wage}/hr. Filling ${gal} gal costs ~$${cost} = ${hours} of work.`,
    wageHours: (h) => (h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(1)} h`),
    directions: "Directions",
    navOpenTitle: "Directions",
    navOpenHint: "Apple Maps or Google Maps will open. GasRadar stays here.",
    navOpenBtn: "Open maps",
    navStayBtn: "Cancel",
    navOpening: "Opening navigation…",
    share: "Share",
    nearYou: "Near you",
    loading: "Loading…",
    contact: "Contact:",
    privacy: "Privacy",
    blog: "Blog",
    places: "Cities",
    waChannel: "WhatsApp channel",
    pressTelemundo: "Featured on Telemundo Denver",
    refPrices: "Reference prices",
    reportTitle: "Report price",
    reportSub: "What did you see at the pump? (USD / gallon)",
    reportHint: "Example: 2.99 or 3.15",
    cancel: "Cancel",
    save: "Save",
    report: "Report",
    searching: "Searching stations…",
    searchingStill: "Still fetching live prices…",
    searchingZip: (z) => `Searching ZIP ${z}…`,
    searchingZipChange: (z) => `Switching to ZIP ${z}… (keeping previous list a moment)`,
    terms: "Terms",
    rules: "Rules",
    emptyTitle: "No results yet",
    emptyStart: "Enter your ZIP or tap Use my location.",
    loadLast: "Loading your last area…",
    noStations: "No real stations here. Try 10 miles or another ZIP.",
    timeout: "Network was slow. Hang on — still loading that area.",
    timeoutSoft: "Still loading that area…",
    searchError: "Search error. Try a ZIP.",
    stateAvg: (st, price) => `State average${st}: ${price}`,
    eiaTitle: "This week's average",
    eiaNote: "State average this week · not the price at each pump",
    eiaWeek: (period) => (period ? `Week of ${period}` : "Weekly average"),
    eiaStateLine: (st, fuel) => `${st} · ${fuel}`,
    eiaBadge: "wk avg",
    eiaChipLabel: "wk avg",
    reported: "reported",
    estimated: "reference",
    livePrice: "live",
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
    playGet: "Get it on Google Play",
    playBanner: "Now on Google Play",
    playBannerCta: "Install",
    footerPlay: "Android app",
    installApp: "Install app",
    installOk: "GasRadar is ready to install",
    installDone: "App installed — find it on your home screen",
    installIos: "On iPhone: tap Share → Add to Home Screen",
    installAlready: "Already installed, or open it from the home screen icon",
    telegramAlerts: "Alerts",
    trustpilotReview: "Leave a review",
    buyMeCoffee: "Donate",
    donate: "Donate",
    donateTitle: "Donate what you want",
    donateSub: "Pick an amount or enter your own. Secure Stripe checkout.",
    donateHint: "Minimum $1 · you choose how much",
    donatePay: "Donate with Stripe",
    donateThanks: "Thanks for your donation! 💛",
    donateCancel: "Donation canceled",
    donateErr: "Couldn't open Stripe. Try again.",
    donateBusy: "Opening Stripe…",
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
  searchToken: 0,
  searchAbort: null,
  lastData: null,
  lang: loadLang(),
};

function loadLang() {
  try {
    const s = localStorage.getItem(LANG_KEY);
    if (s === "en" || s === "es") return s;
  } catch (_) {}
  const nav = (navigator.language || "en").toLowerCase();
  return nav.startsWith("es") ? "es" : "en";
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
  const playSrc =
    state.lang === "es"
      ? "/static/google-play-badge-es.png"
      : "/static/google-play-badge-en.png";
  const playAlt = t("playGet");
  document.querySelectorAll("[data-play-badge]").forEach((img) => {
    img.src = playSrc;
    img.alt = playAlt;
    const wrap = img.closest("a");
    if (wrap) {
      wrap.title = playAlt;
      wrap.setAttribute("aria-label", playAlt);
    }
  });
  const galIn = $("#wageGallons");
  if (galIn) galIn.setAttribute("aria-label", t("wageGallons"));
  const bmc = $("#btnBuyMeCoffee");
  if (bmc) {
    bmc.setAttribute("title", t("donateTitle"));
    bmc.setAttribute("aria-label", t("donate"));
  }
  document.title =
    state.lang === "en"
      ? "Cheap gas near me (USA) | GasRadar"
      : "Gasolina barata cerca de ti (USA) | GasRadar";
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

function setBusy(busy, { background = false } = {}) {
  state.searching = !!busy;
  // No tocamos el aspecto del botón "Buscar" (en móvil se queda “pegado”
  // con :active / is-loading). El estado se ve en el mensaje de status.
  if (background) return;
  if (!busy) unlockSearchUi();
}

/**
 * Libera la UI (botón pegado / disabled).
 * abortFetch=true solo al cancelar a propósito; NO abortar al terminar bien
 * (si no, se cancela la búsqueda en curso y “no busca”).
 */
function unlockSearchUi({ abortFetch = false } = {}) {
  state.searching = false;
  if (abortFetch && state.searchAbort) {
    try {
      state.searchAbort.abort();
    } catch (_) {
      /* ignore */
    }
    state.searchAbort = null;
  }
  ["#btnGps", "#btnZip", "#fuelSelect", "#radiusSelect", "#zipInput"].forEach((sel) => {
    const el = $(sel);
    if (!el) return;
    el.disabled = false;
    el.classList.remove("is-loading", "is-pressed");
    el.removeAttribute("aria-busy");
    try {
      el.blur();
    } catch (_) {
      /* ignore */
    }
  });
  try {
    if (document.activeElement && document.activeElement.blur) {
      document.activeElement.blur();
    }
  } catch (_) {
    /* ignore */
  }
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
 * Enlaces de navegación (web + deep links nativos).
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
  return `https://www.google.com/maps/dir/?api=1&destination=${dest}&travelmode=driving`;
}

/** Deep link nativo (menos pestaña blanca en móvil). */
function mapsNativeUrl(st) {
  if (!st || st.lat == null || st.lon == null) return mapsUrl(st);
  const lat = st.lat;
  const lon = st.lon;
  const label = encodeURIComponent(st.name || "Gas");
  const platform = detectPlatform();
  if (platform === "ios") {
    return `maps://?daddr=${lat},${lon}&q=${label}&dirflg=d`;
  }
  if (platform === "android") {
    // Abre Google Maps app si está instalada; si no, el sistema cae al navegador
    return `google.navigation:q=${lat},${lon}`;
  }
  return mapsUrl(st);
}

function mapsButtonLabel() {
  return t("directions");
}

/** Abre Maps al tocar Cómo llegar (sin menú intermedio). */
function launchMaps(st) {
  if (!st) return;
  const web = mapsUrl(st);
  const platform = detectPlatform();
  // Móvil: deep link nativo (app de mapas). Escritorio: Google/Apple Maps en pestaña.
  const href =
    platform === "ios" || platform === "android" ? mapsNativeUrl(st) : web;
  try {
    const a = document.createElement("a");
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (_) {
    try {
      window.open(web, "_blank", "noopener");
    } catch (__) {
      location.href = web;
    }
  }
}

function openDirections(st) {
  if (!st) return;
  launchMaps(st);
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

function isLivePriceSource(src) {
  const s = String(src || "").toLowerCase();
  // Precios reales de bomba (VPS / GasBuddy / reportes de usuarios)
  return (
    s === "gasbuddy" ||
    s === "vps" ||
    s === "user" ||
    s.includes("gasbuddy") ||
    s.includes("live")
  );
}

function sourceBadgeHtml(s) {
  const src = String(s.price_source || s.source || "").toLowerCase();
  // Reportes de la comunidad
  if (src === "user") {
    const n = s.reports_count ? ` · ${s.reports_count}` : "";
    const age = s.price_age_hours != null ? ` · ${s.price_age_hours}h` : "";
    return `<span class="badge user" title="${escapeHtml(
      state.lang === "en" ? "Price reported by users" : "Precio reportado por usuarios"
    )}">${t("reported")}${n}${age}</span>`;
  }
  // En vivo = datos reales (GasBuddy vía VPS), NO promedios AAA/EIA
  if (isLivePriceSource(src)) {
    return `<span class="badge eia" title="${escapeHtml(
      state.lang === "en"
        ? "Live station price from our feed"
        : "Precio en vivo de la estación (fuente en tiempo real)"
    )}">${t("livePrice")}</span>`;
  }
  // AAA / EIA / ajustes: no son el precio de la bomba → "referencia", no "en vivo"
  return `<span class="badge estimate" title="${escapeHtml(
    state.lang === "en"
      ? "Area reference average — not a live pump price"
      : "Promedio de referencia de la zona — no es el precio de la bomba"
  )}">${t("estimated")}</span>`;
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
// Cache más largo: al volver a un ZIP reciente no se siente lag
const SEARCH_MEM_MS = 30 * 60 * 1000;

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
  // Sin precios en vivo: avisar (ya no mostramos estimados)
  if (data.partial && (!state.stations || !state.stations.length)) {
    try {
      showToast(
        state.lang === "en"
          ? "Loading live prices for that ZIP…"
          : "Cargando precios en vivo de ese ZIP…"
      );
    } catch (_) {
      /* ignore */
    }
  }
}

async function search({ lat, lon, zip, force = false, soft = false, background = false } = {}) {
  // Búsqueda en segundo plano: no pisar una del usuario
  if (background && state.searching) return;

  const zipDigits0 = zip ? String(zip).replace(/\D/g, "").slice(0, 5) : "";
  // Mismo ZIP ya en curso: no abortar ni reiniciar (eso obligaba a 5 clics)
  if (
    !background &&
    state.searching &&
    zipDigits0 &&
    state.zip === zipDigits0
  ) {
    return;
  }

  // Nueva búsqueda del usuario: cancela la anterior SOLO si cambió el ZIP
  if (!background && state.searchAbort) {
    try {
      state.searchAbort.abort();
    } catch (_) {
      /* ignore */
    }
    state.searchAbort = null;
  }

  const memKey = searchMemKey({ lat, lon, zip });
  if (force) {
    try {
      _searchMem.delete(memKey);
    } catch (_) {
      /* ignore */
    }
  } else {
    const memHit = _searchMem.get(memKey);
    // No reutilizar cache vacío (parecía que “no busca”)
    const hitStations = memHit && memHit.data && memHit.data.stations;
    if (
      memHit &&
      Date.now() - memHit.ts < SEARCH_MEM_MS &&
      memHit.data &&
      Array.isArray(hitStations) &&
      hitStations.length > 0
    ) {
      applySearchData(memHit.data, { zip });
      unlockSearchUi({ abortFetch: false });
      return;
    }
  }

  const myToken = ++state.searchToken;
  if (!background) state.searching = true;

  const zipDigits = zip ? String(zip).replace(/\D/g, "").slice(0, 5) : "";
  // Al cambiar ZIP: mantener lista anterior en pantalla
  const keepList =
    soft ||
    background ||
    (zipDigits &&
      state.stations &&
      state.stations.length > 0 &&
      state.zip &&
      state.zip !== zipDigits);

  if (!background) {
    if (!keepList) {
      setStatus(
        zipDigits ? t("searchingZip", zipDigits) : t("searching"),
        "loading"
      );
      const resEl = $("#results");
      if (resEl) resEl.innerHTML = "";
      const bestCard = $("#bestCard");
      if (bestCard) bestCard.hidden = true;
      const head = $("#resultsHead");
      if (head) head.hidden = true;
    } else {
      setStatus(
        zipDigits ? t("searchingZipChange", zipDigits) : t("searching"),
        "loading"
      );
    }
  }

  const params = new URLSearchParams();
  params.set("fuel", state.fuel);
  params.set("radius_mi", String(state.radius));
  params.set("limit", "22");
  if (zip) params.set("zip", zip);
  // Solo GPS si no hay ZIP explícito (evita mezclar ubicación vieja con ZIP nuevo)
  if (!zip && lat != null && lon != null) {
    params.set("lat", String(lat));
    params.set("lon", String(lon));
  }

  const ctrl = new AbortController();
  state.searchAbort = ctrl;
  const MAX_TRIES = background ? 1 : 8;
  const overall = setTimeout(() => {
    try {
      ctrl.abort();
    } catch (_) {
      /* ignore */
    }
  }, 24000);
  const stillTimer = setTimeout(() => {
    if (myToken === state.searchToken && state.searching && !background) {
      setStatus(t("searchingStill"), "loading");
    }
  }, 4500);

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  try {
    let data = null;
    for (let attempt = 1; attempt <= MAX_TRIES; attempt++) {
      if (myToken !== state.searchToken) return;
      if (attempt > 1) {
        setStatus(t("searchingStill"), "loading");
        await sleep(1100);
        if (myToken !== state.searchToken) return;
      }
      const res = await fetch(`/api/search?${params.toString()}`, {
        signal: ctrl.signal,
      });
      if (myToken !== state.searchToken) return;
      if (!res.ok) {
        if ([502, 503, 504].includes(res.status) && attempt < MAX_TRIES) {
          console.log("[GasRadar] gateway", res.status, "retry", attempt + 1);
          continue;
        }
        const err = await res.json().catch(() => ({}));
        const detail =
          typeof err.detail === "string"
            ? err.detail
            : Array.isArray(err.detail)
              ? err.detail.map((d) => d.msg || d).join(", ")
              : null;
        throw new Error(detail || t("timeoutSoft"));
      }
      data = await res.json();
      if (myToken !== state.searchToken) return;
      const n = data && Array.isArray(data.stations) ? data.stations.length : 0;
      if (n > 0) break;
      if (attempt < MAX_TRIES) {
        console.log("[GasRadar] empty ZIP, retry", attempt + 1, "/", MAX_TRIES);
      }
    }
    clearTimeout(stillTimer);
    if (myToken !== state.searchToken) return;
    if (!data || !data.center) {
      setStatus(t("timeoutSoft"), "error");
      return;
    }
    try {
      if (data && Array.isArray(data.stations) && data.stations.length > 0) {
        _searchMem.set(memKey, { ts: Date.now(), data });
        if (_searchMem.size > 40) {
          const first = _searchMem.keys().next().value;
          _searchMem.delete(first);
        }
      } else {
        _searchMem.delete(memKey);
      }
    } catch (_) {
      /* ignore */
    }
    applySearchData(data, { zip });
  } catch (e) {
    clearTimeout(stillTimer);
    // Reemplazada por otra búsqueda (otro ZIP): no mostrar error ni bloquear
    if (myToken !== state.searchToken) return;

    const isAbort = e && e.name === "AbortError";
    if (keepList || soft) {
      if (state.stations && state.stations.length) {
        showToast(isAbort ? t("timeoutSoft") : e.message || t("searchError"));
        setStatus(
          state.stations.length +
            " · " +
            (state.lang === "en"
              ? "previous area — still loading the new ZIP"
              : "zona anterior — seguimos cargando el ZIP nuevo"),
          "ok"
        );
      } else {
        setStatus(isAbort ? t("timeout") : e.message || t("searchError"), "error");
      }
    } else {
      setLocDot("off");
      setStatus(isAbort ? t("timeout") : e.message || t("searchError"), "error");
    }
  } finally {
    clearTimeout(overall);
    clearTimeout(stillTimer);
    try {
      const bz = $("#btnZip");
      if (bz) {
        bz.classList.remove("is-loading", "is-pressed");
        bz.disabled = false;
        bz.blur();
      }
      const bg = $("#btnGps");
      if (bg) {
        bg.classList.remove("is-loading", "is-pressed");
        bg.disabled = false;
        bg.blur();
      }
    } catch (_) {
      /* ignore */
    }
    if (myToken === state.searchToken) {
      if (state.searchAbort === ctrl) state.searchAbort = null;
      state.searching = false;
      // No abortFetch: la búsqueda ya terminó
      unlockSearchUi({ abortFetch: false });
    }
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

const TANK_KEY = "gasradar_tank_gal";

function tankGallons() {
  const el = $("#wageGallons");
  let g = el ? Number(el.value) : Number(localStorage.getItem(TANK_KEY) || 15);
  if (!Number.isFinite(g) || g < 5) g = 15;
  if (g > 40) g = 40;
  return g;
}

function renderWageCard(data) {
  const card = $("#wageCard");
  if (!card) return;
  const w = data && data.min_wage;
  const price =
    (data && data.cheapest && Number(data.cheapest.price)) ||
    (data && data.state_avg && Number(data.state_avg.regular));
  if (!w || !price || Number.isNaN(price)) {
    card.hidden = true;
    return;
  }
  const gal = tankGallons();
  const cost = price * gal;
  const hours = cost / Number(w.hourly);
  const hoursTxt = t("wageHours", hours);
  const hoursEl = $("#wageHoursBig");
  const stEl = $("#wageState");
  if (hoursEl) hoursEl.textContent = hoursTxt;
  if (stEl) stEl.textContent = `${w.state} $${Number(w.hourly).toFixed(2)}/h`;
  card.title = t(
    "wageLine",
    w.state,
    Number(w.hourly).toFixed(2),
    gal,
    cost.toFixed(2),
    hoursTxt
  );
  card.hidden = false;
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
    // cheapest del API usa "source"; la lista usa "price_source"
    const src = b.price_source || b.source || "";
    let confLabel = t("estimated");
    if (String(src).toLowerCase() === "user") confLabel = t("reportedPrice");
    else if (isLivePriceSource(src)) confLabel = t("livePrice");
    $("#bestMeta").textContent = `${b.distance_mi} mi · ${confLabel}`;
    const badge = $("#bestSourceBadge");
    if (badge) {
      if (String(src).toLowerCase() === "user") {
        badge.textContent = t("reported");
        badge.className = "badge user";
      } else if (isLivePriceSource(src)) {
        badge.textContent = t("livePrice");
        badge.className = "badge eia";
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
    renderWageCard(data);

    const bestMaps = $("#bestMaps");
    if (bestMaps) {
      bestMaps.textContent = t("directions");
      bestMaps.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        openDirections(full);
      };
    }
  } else {
    state.cheapest = null;
    $("#bestCard").hidden = true;
    renderWageCard(data);
  }

  if (!state.stations.length) {
    setStatus(t("noStations"), "empty");
    const head = $("#resultsHead");
    if (head) head.hidden = true;
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
            <p class="station-sub">${brandBit}${s.distance_mi} mi</p>
            ${addr}
          </div>
          <div class="station-price-col">
            <div class="station-price-row">
              ${src}
              ${priceBoxHtml(s.price)}
            </div>
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
  // Aviso de estaciones/precios (OpenStreetMap, estimaciones) → /privacy

  $("#results").querySelectorAll("[data-maps]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.getAttribute("data-maps");
      const st = state.stations.find((x) => x.id === id);
      if (st) openDirections(st);
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
  syncBodyModal();
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
  syncBodyModal();
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

const PLAY_BANNER_KEY = "gr_play_announce_v1";

function initPlayBanner() {
  const bar = $("#playAnnounce");
  const close = $("#playAnnounceClose");
  if (!bar) return;
  try {
    if (localStorage.getItem(PLAY_BANNER_KEY) === "1") {
      bar.hidden = true;
      return;
    }
  } catch (_) {}
  if (close) {
    close.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      bar.hidden = true;
      try {
        localStorage.setItem(PLAY_BANNER_KEY, "1");
      } catch (_) {}
    });
  }
}

let donateDigits = "5";

function donateValue() {
  const n = Number(donateDigits);
  return Number.isFinite(n) ? n : 0;
}

function setDonateDigits(s) {
  donateDigits = String(s || "");
  const el = $("#donateAmountText");
  if (el) el.textContent = donateDigits || "0";
  syncDonateChips();
}

function donateKey(k) {
  if (k === "del") {
    setDonateDigits(donateDigits.slice(0, -1));
    return;
  }
  if (k === ".") {
    if (donateDigits.includes(".")) return;
    setDonateDigits((donateDigits || "0") + ".");
    return;
  }
  if (!/^\d$/.test(k)) return;
  let next = donateDigits === "0" ? k : donateDigits + k;
  const parts = next.split(".");
  if (parts[1] && parts[1].length > 2) return;
  if (Number(next) > 500) return;
  setDonateDigits(next);
}

function syncBodyModal() {
  const open =
    $("#donateModal")?.classList.contains("open") ||
    $("#modal")?.classList.contains("open");
  document.body.classList.toggle("modal-open", !!open);
}

function openDonate(preset) {
  const modal = $("#donateModal");
  if (!modal) return;
  setDonateDigits(preset != null ? String(preset) : donateDigits || "5");
  modal.classList.add("open");
  syncBodyModal();
}

function closeDonate() {
  $("#donateModal")?.classList.remove("open");
  syncBodyModal();
}

function syncDonateChips() {
  const val = donateValue();
  document.querySelectorAll(".donate-chip").forEach((btn) => {
    const amt = Number(btn.getAttribute("data-amt"));
    btn.classList.toggle("is-on", amt === val);
  });
}

async function payDonate() {
  const raw = donateValue();
  if (!raw || raw < 1 || raw > 500) {
    showToast(t("donateHint"));
    return;
  }
  const btn = $("#btnDonatePay");
  if (btn) btn.disabled = true;
  showToast(t("donateBusy"));
  try {
    const r = await fetch("/api/donate/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: Math.round(raw * 100) / 100 }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || !j.url) {
      showToast(j.detail || t("donateErr"));
      return;
    }
    window.location.href = j.url;
  } catch (_) {
    showToast(t("donateErr"));
  } finally {
    if (btn) btn.disabled = false;
  }
}

function startApp() {
  applyStaticI18n();
  initPlayBanner();
  try {
    const q = new URLSearchParams(location.search);
    if (q.get("donated") === "1") showToast(t("donateThanks"));
    if (q.get("donated") === "0") showToast(t("donateCancel"));
    if (q.get("donate") === "1") setTimeout(() => openDonate(5), 250);
  } catch (_) {}
  const galEl = $("#wageGallons");
  if (galEl) {
    const saved = Number(localStorage.getItem(TANK_KEY) || 15);
    if (saved >= 5 && saved <= 40) galEl.value = String(saved);
    galEl.addEventListener("change", () => {
      const g = tankGallons();
      galEl.value = String(g);
      try {
        localStorage.setItem(TANK_KEY, String(g));
      } catch (_) {}
      if (state.lastData) renderWageCard(state.lastData);
    });
  }
  const zipQ = new URLSearchParams(location.search).get("zip") || "";
  const zipDigits = String(zipQ).replace(/\D/g, "").slice(0, 5);
  if (zipDigits.length === 5) {
    state.zip = zipDigits;
    if ($("#zipInput")) $("#zipInput").value = zipDigits;
    setStatus(t("searchingZip", zipDigits), "loading");
    search({ zip: zipDigits });
    return;
  }
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
            background: true,
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
  $("#btnBuyMeCoffee")?.addEventListener("click", () => openDonate(5));
  $("#linkDonateFooter")?.addEventListener("click", () => openDonate(5));
  $("#btnCloseDonate")?.addEventListener("click", closeDonate);
  $("#btnDonatePay")?.addEventListener("click", payDonate);
  $("#donatePad")?.addEventListener("click", (e) => {
    const key = e.target.closest("button[data-k]");
    if (!key) return;
    donateKey(key.getAttribute("data-k"));
  });
  $("#donatePresets")?.addEventListener("click", (e) => {
    const chip = e.target.closest(".donate-chip");
    if (!chip) return;
    const amt = chip.getAttribute("data-amt");
    if (amt) setDonateDigits(amt);
  });
  $("#donateModal")?.addEventListener("click", (e) => {
    if (e.target.id === "donateModal") closeDonate();
  });
  const bestShare = $("#bestShare");
  if (bestShare) {
    bestShare.addEventListener("click", () => {
      if (state.cheapest) sharePrice(state.cheapest);
      else if (state.stations[0]) sharePrice(state.stations[0]);
      else showToast(t("searchFirst"));
    });
  }
  $("#btnGps").addEventListener("click", useGps);
  var _lastZipSearchAt = 0;
  function runZipSearch() {
    // Evita doble disparo: el botón tiene onclick inline (respaldo si el
    // listener no se registra por SW viejo) + este addEventListener; ambos
    // se ejecutan en el mismo click y duplicaban la búsqueda (se sentía
    // "pegado" y lageaba al cambiar de ZIP).
    var now = Date.now();
    if (now - _lastZipSearchAt < 400) return;
    _lastZipSearchAt = now;
    try {
      var input = document.getElementById("zipInput");
      var zip = (input && input.value ? String(input.value).trim() : "") || "";
      if (!zip) {
        showToast(t("needZip"));
        if (input) input.focus();
        return;
      }
      var digits = zip.replace(/\D/g, "");
      if (digits.length < 5) {
        showToast(t("zip5"));
        return;
      }
      var newZip = digits.slice(0, 5);
      var prevZip = state.zip || "";
      var hasList = state.stations && state.stations.length > 0;
      var changing = prevZip && prevZip !== newZip && hasList;
      if (state.searching && prevZip === newZip) {
        return;
      }

      state.zip = newZip;
      if (input) input.value = newZip;

      // Feedback inmediato (el usuario ve que el botón SÍ hizo algo)
      try {
        showToast(
          state.lang === "en"
            ? "Searching ZIP " + newZip + "…"
            : "Buscando ZIP " + newZip + "…"
        );
      } catch (_) {}
      setStatus(t("searchingZip", newZip), "loading");

      var btn = document.getElementById("btnZip");
      if (btn) {
        try {
          btn.blur();
        } catch (_) {}
      }

      search({
        zip: newZip,
        soft: !!changing,
        force: !!changing,
        background: false,
      });
    } catch (err) {
      console.error("[GasRadar] runZipSearch", err);
      try {
        showToast(t("searchError"));
        unlockSearchUi({ abortFetch: false });
      } catch (_) {}
    }
  }

  // Expuesto global: respaldo si el listener falla o hay SW viejo
  window.gasradarSearchZip = runZipSearch;

  var btnZipEl = document.getElementById("btnZip");
  if (btnZipEl) {
    btnZipEl.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      try {
        e.currentTarget.blur();
      } catch (_) {}
      runZipSearch();
    });
    btnZipEl.addEventListener(
      "touchend",
      function (e) {
        // No preventDefault aquí (rompe el click en algunos Android);
        // solo soltar aspecto visual
        try {
          e.currentTarget.blur();
        } catch (_) {}
      },
      { passive: true }
    );
  }
  var zipInputEl = document.getElementById("zipInput");
  if (zipInputEl) {
    zipInputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        runZipSearch();
      }
    });
  }
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
    if ($("#donateModal")?.classList.contains("open")) {
      if (e.key === "Escape") {
        closeDonate();
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        payDonate();
        return;
      }
      if (e.key === "Backspace") {
        e.preventDefault();
        donateKey("del");
        return;
      }
      if (e.key === "." || e.key === ",") {
        e.preventDefault();
        donateKey(".");
        return;
      }
      if (/^\d$/.test(e.key)) {
        e.preventDefault();
        donateKey(e.key);
        return;
      }
    }
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
  const ok =
    window.isSecureContext ||
    ["localhost", "127.0.0.1"].includes(location.hostname);
  if (!ok) return;

  const go = () => {
    navigator.serviceWorker
      .register("/sw.js?v=0.9.81", { scope: "/" })
      .then((reg) => {
        try {
          reg.update();
        } catch (_) {}
        if (reg.waiting) {
          reg.waiting.postMessage({ type: "SKIP_WAITING" });
        }
        reg.addEventListener("updatefound", () => {
          const nw = reg.installing;
          if (!nw) return;
          nw.addEventListener("statechange", () => {
            if (nw.state === "installed" && navigator.serviceWorker.controller) {
              nw.postMessage({ type: "SKIP_WAITING" });
            }
          });
        });
      })
      .catch(() => {
        /* ignore: PWA opcional */
      });
  };

  // Registrar SW después de un tick para no pelear con el purge de index
  setTimeout(go, 1500);

  let refreshing = false;
  let hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (!hadController) {
      hadController = true;
      return;
    }
    if (refreshing) return;
    refreshing = true;
    location.reload();
  });
}

bind();
setupPwaInstall();
registerServiceWorker();
trackVisit();
startApp();
