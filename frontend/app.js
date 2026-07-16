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
  searching: false,
  lastData: null,
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
    if (o.saved_at && Date.now() - o.saved_at > 30 * 24 * 3600 * 1000) return null;
    return o;
  } catch (_) {
    return null;
  }
}

/** Precio en pantalla: $3.68 (2 decimales) */
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
  const el = $("#toast") || (() => {
    const t = document.createElement("div");
    t.id = "toast";
    t.className = "toast";
    document.body.appendChild(t);
    return t;
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
  lines.push(`Contacto: contact@gasradarapp.com`);
  return lines.join("\n");
}

async function sharePrice(station) {
  if (!station || station.lat == null) {
    showToast("No hay precio para compartir");
    return;
  }
  const text = buildShareText(station);
  const title = `Gasolina ${money(station.price)} — ${station.name || "GasRadar"}`;

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
    showToast("Precio copiado — pégalo a tus amigos");
  } catch (_) {
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
  if (!el) return;
  el.className = kind;
  if (kind === "empty") {
    el.innerHTML = `<div class="empty-title">Sin resultados aún</div>${escapeHtml(msg)}`;
  } else {
    el.textContent = msg;
  }
  el.hidden = false;
  const sk = $("#skeleton");
  if (sk) sk.hidden = kind !== "loading";
  if (kind === "loading") {
    setLocDot("loading");
  }
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
    const n = s.reports_count ? ` · ${s.reports_count} rep` : "";
    const age =
      s.price_age_hours != null ? ` · ${s.price_age_hours}h` : "";
    return `<span class="badge user">reportado${n}${age}</span>`;
  }
  // Sin "EIA + marca" — texto simple
  return `<span class="badge estimate">estimado</span>`;
}

function sourceLabel(source) {
  if (source === "user") return "reportado";
  return "estimado";
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
    return `<div class="station-vs">≈ promedio</div>`;
  }
  if (v < 0) {
    return `<div class="station-vs cheaper">−${money(Math.abs(v))}</div>`;
  }
  return `<div class="station-vs pricier">+${money(v)}</div>`;
}

async function search({ lat, lon, zip } = {}) {
  if (state.searching) return;

  setBusy(true);
  setStatus("Buscando estaciones…", "loading");
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
      setStatus("Tardó mucho. Prueba de nuevo o escribe un ZIP.", "error");
    } else {
      setStatus(e.message || "Error de búsqueda. Prueba un ZIP.", "error");
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
  // Solo promedio de estado — sin "EIA oficial" ni fecha
  $("#stateAvg").textContent = `Promedio del estado${st}: ${money(fuelAvg)} · ${fuelLabel(state.fuel)}`;

  // Best card
  if (data.cheapest) {
    const b = data.cheapest;
    state.cheapest = b;
    $("#bestCard").hidden = false;
    $("#bestPrice").textContent = money(b.price);
    $("#bestName").textContent = b.name;
    const conf =
      b.source === "user" ? "precio reportado" : "estimado";
    $("#bestMeta").textContent = `${b.distance_mi} mi · ${conf}`;
    const badge = $("#bestSourceBadge");
    if (badge) {
      // Sin texto EIA/fecha — solo reportado o estimado
      if (b.source === "user") {
        badge.textContent = "reportado";
        badge.className = "badge user";
      } else {
        badge.textContent = "estimado";
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
        saveEl.textContent = `Ahorras ~${money(savings)}/gal vs promedio`;
      } else if (savings != null && savings < -0.004) {
        saveEl.hidden = false;
        saveEl.className = "best-save over";
        saveEl.textContent = `${money(Math.abs(savings))}/gal sobre el promedio`;
      } else {
        saveEl.hidden = true;
      }
    }

    const full =
      state.stations.find((x) => x.id === b.station_id) ||
      state.stations.find((x) => x.name === b.name) ||
      b;
    $("#bestMaps").href = mapsUrl(full);
    $("#bestMaps").textContent = "Cómo llegar";
  } else {
    state.cheapest = null;
    $("#bestCard").hidden = true;
  }

  if (!state.stations.length) {
    setStatus(
      "No hay estaciones reales aquí. Prueba 10 millas u otro ZIP.",
      "empty"
    );
    const head = $("#resultsHead");
    if (head) head.hidden = true;
    $("#disclaimer").textContent = data.disclaimer || "";
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
          ? `${data.count} estaciones · ${ur} con reporte`
          : `${data.count} estaciones · por precio`;
    }
  }

  const html = state.stations
    .map((s, i) => {
      const src = sourceBadgeHtml(s);
      const brandBit =
        s.brand && s.brand !== s.name && s.brand !== "Gasolinera"
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
          <button class="btn-ghost" type="button" data-share="${escapeHtml(s.id)}">Compartir</button>
          <button class="btn-ghost" type="button" data-report="${escapeHtml(s.id)}" data-name="${escapeHtml(s.name)}">Reportar</button>
        </div>
      </article>`;
    })
    .join("");

  $("#results").innerHTML = html;
  $("#disclaimer").textContent = data.disclaimer || "";

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
  $("#reportTitle").textContent = `Reportar · ${name}`;
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
}

async function submitReport() {
  const raw = ($("#reportPrice").value || "").trim();
  const price = parseFloat(raw);
  if (!state.reportStationId || Number.isNaN(price)) {
    showToast("Pon un precio válido");
    return;
  }
  if (price < 1 || price > 12) {
    showToast("Precio fuera de rango (1–12 USD)");
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
      showToast(err.detail || "No se pudo guardar");
      return;
    }
    closeReport();
    showToast(`Precio guardado: ${money(price)}`);
    await search({ lat: state.lat, lon: state.lon, zip: state.zip || undefined });
  } catch (_) {
    showToast("Error de red al guardar");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function useGps() {
  if (!navigator.geolocation) {
    setStatus("GPS no disponible. Usa un ZIP (ej. 80903).", "error");
    return;
  }
  if (
    window.isSecureContext !== true &&
    !["localhost", "127.0.0.1"].includes(location.hostname)
  ) {
    setStatus("GPS solo funciona con HTTPS. Usa un ZIP.", "error");
    return;
  }
  setStatus("Obteniendo tu ubicación…", "loading");
  setLocDot("loading");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      state.zip = null;
      search({ lat: pos.coords.latitude, lon: pos.coords.longitude });
    },
    (err) => {
      setLocDot("off");
      const code = err && err.code;
      if (code === 1) {
        setStatus("Permiso de ubicación denegado. Usa un ZIP.", "error");
      } else if (code === 3) {
        setStatus("GPS tardó mucho. Usa un ZIP (ej. 80903).", "error");
      } else {
        setStatus("Sin GPS. Usa un ZIP (Colorado Springs: 80903).", "error");
      }
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 }
  );
}

function startApp() {
  const saved = loadSavedLocation();
  if (saved) {
    state.zip = saved.zip || null;
    if (saved.zip && $("#zipInput")) $("#zipInput").value = saved.zip;
    setStatus("Cargando tu última zona…", "loading");
    if (saved.zip) {
      search({ zip: saved.zip });
    } else {
      search({ lat: saved.lat, lon: saved.lon });
    }
    return;
  }

  setStatus("Escribe tu ZIP o toca Usar mi ubicación.", "empty");
  $("#locationLabel").textContent = "Sin ubicación";
  $("#stateAvg").textContent = "ZIP o GPS para empezar";
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
      showToast("Escribe un ZIP de USA (ej. 80903)");
      $("#zipInput").focus();
      return;
    }
    const digits = zip.replace(/\D/g, "");
    if (digits.length < 5) {
      showToast("ZIP debe tener 5 dígitos");
      return;
    }
    state.zip = digits.slice(0, 5);
    search({ zip: state.zip });
  });
  $("#zipInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("#btnZip").click();
  });
  // Solo dígitos y guión en ZIP
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
