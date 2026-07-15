const $ = (sel) => document.querySelector(sel);

const state = {
  lat: null,
  lon: null,
  label: "Denver, CO",
  fuel: "regular",
  radius: 5,
  stations: [],
  reportStationId: null,
};

function money(n) {
  if (n == null || Number.isNaN(n)) return "—";
  return `$${Number(n).toFixed(2)}`;
}

function mapsUrl(lat, lon, name) {
  const q = encodeURIComponent(`${name || "Gas"} @ ${lat},${lon}`);
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}&destination_place_id=&travelmode=driving&q=${q}`;
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
    render(data);
  } catch (e) {
    setStatus(e.message || "Error de búsqueda", "error");
  }
}

function render(data) {
  $("#locationLabel").textContent = data.center.label;
  const avg = data.state_avg || {};
  $("#stateAvg").textContent = `Promedio estado (~): ${money(avg[state.fuel] || avg.regular)}`;

  if (data.cheapest) {
    const b = data.cheapest;
    $("#bestCard").style.display = "block";
    $("#bestPrice").textContent = money(b.price);
    $("#bestName").textContent = b.name;
    $("#bestMeta").textContent = `${b.distance_mi} mi · ${b.source === "user" ? "reportado" : "estimado"}`;
    $("#bestMaps").href = mapsUrl(b.lat, b.lon, b.name);
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
      const src =
        s.price_source === "user"
          ? `<span class="badge user">reportado${s.price_age_hours != null ? ` · ${s.price_age_hours}h` : ""}</span>`
          : `<span class="badge estimate">estimado</span>`;
      const addr = s.address ? `<p class="station-sub">${s.address}</p>` : "";
      return `
      <article class="station" data-id="${s.id}">
        <div class="station-top">
          <div>
            <p class="station-name"><span class="${rankClass}">${i + 1}</span>${escapeHtml(s.name)}</p>
            <p class="station-sub">${escapeHtml(s.brand || "")} · ${s.distance_mi} mi ${src}</p>
            ${addr}
          </div>
          <div class="station-price">${money(s.price)}</div>
        </div>
        <div class="station-actions">
          <a class="btn-ghost" href="${mapsUrl(s.lat, s.lon, s.name)}" target="_blank" rel="noopener">Cómo llegar</a>
          <button class="btn-ghost" data-report="${s.id}" data-name="${escapeHtml(s.name)}">Reportar precio</button>
        </div>
      </article>`;
    })
    .join("");

  $("#results").innerHTML = html;
  $("#disclaimer").textContent = data.disclaimer || "";

  $("#results").querySelectorAll("[data-report]").forEach((btn) => {
    btn.addEventListener("click", () => openReport(btn.dataset.report, btn.dataset.name));
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
    setStatus("GPS no disponible. Usa un ZIP.", "error");
    return;
  }
  if (window.isSecureContext !== true && !["localhost", "127.0.0.1"].includes(location.hostname)) {
    setStatus("GPS no disponible aquí. Usa un ZIP.", "error");
    return;
  }
  setStatus("Obteniendo ubicación…", "loading");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      search({ lat: pos.coords.latitude, lon: pos.coords.longitude });
    },
    () => {
      setStatus("Sin GPS. Usa un ZIP.", "error");
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
  );
}

function bind() {
  $("#btnGps").addEventListener("click", useGps);
  $("#btnZip").addEventListener("click", () => {
    const zip = $("#zipInput").value.trim();
    if (!zip) {
      alert("Escribe un ZIP de USA");
      return;
    }
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
// Carga inicial: Denver
search({ lat: 39.7392, lon: -104.9903 });
