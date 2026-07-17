"""
GasRadar — API + web app
Radar de precios de gasolina USA. Precio más barato cerca de ti.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.prices import report_price

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

APP_VERSION = "0.7.0"

app = FastAPI(title="GasRadar", version=APP_VERSION)


@app.middleware("http")
async def add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-App"] = "GasRadar"
    response.headers["X-App-Version"] = APP_VERSION
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    # HTML/CSS/JS sin cache agresivo (beta: los cambios se ven al recargar)
    path = request.url.path
    if path.startswith("/static/"):
        if path.endswith((".png", ".svg", ".jpg", ".webp", ".ico")):
            response.headers["Cache-Control"] = "public, max-age=86400"
        elif path.endswith((".css", ".js")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
    elif path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


class ReportBody(BaseModel):
    station_id: str
    fuel: str = "regular"
    price: float = Field(..., gt=1.0, lt=12.0)
    note: str | None = None


@app.get("/api/health")
def health():
    """Healthcheck para Render y keep-alive (cron / script)."""
    from datetime import datetime, timezone

    from backend.db import db_status
    from backend.prices import _zyla_api_key, _zyla_gas_url, _zyla_station_url
    from backend.telegram_bot import bot_ready

    zkey = _zyla_api_key()
    zurl = _zyla_gas_url()
    zst = _zyla_station_url()
    return {
        "ok": True,
        "app": "gasradar",
        "version": APP_VERSION,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "alive",
        "db": db_status(),
        "telegram_bot": bot_ready(),
        "zyla": {
            "key": bool(zkey),
            "key_len": len(zkey) if zkey else 0,
            "gas_url": bool(zurl),
            "station_url": bool(zst),
            "ready": bool(zkey and zurl and zst),
        },
    }


@app.get("/api/geo/zip/{zip_code}")
def api_geocode(zip_code: str):
    g = geocode_zip(zip_code)
    if not g:
        raise HTTPException(404, "ZIP no encontrado")
    return g


@app.get("/api/zyla/test")
def api_zyla_test(zip: str = Query("80903")):
    """Diagnóstico Zyla (sin exponer la key)."""
    import httpx

    from backend.prices import (
        _zyla_api_key,
        _zyla_gas_url,
        _zyla_headers,
        _zyla_station_url,
        fetch_zyla_zip_prices,
    )

    key = _zyla_api_key()
    gas_url = _zyla_gas_url()
    st_url = _zyla_station_url()
    out: dict = {
        "key_ok": bool(key),
        "key_len": len(key),
        "key_has_pipe": ("|" in key) if key else False,
        "gas_url": gas_url,
        "station_url": st_url,
    }
    if not key or not gas_url:
        out["error"] = "Falta ZYLA_API_KEY o URL"
        return out
    z = "".join(c for c in zip if c.isdigit())[:5] or "80903"
    try:
        r = httpx.get(
            gas_url,
            params={"zip": z, "type": "regular"},
            headers=_zyla_headers(),
            timeout=20.0,
        )
        out["http_status"] = r.status_code
        out["body_preview"] = (r.text or "")[:300]
        if r.status_code == 200:
            prices = fetch_zyla_zip_prices(z, "regular")
            out["parsed"] = prices
    except Exception as e:
        out["exception"] = f"{type(e).__name__}: {e}"
    return out


@app.get("/api/search")
def api_search(
    lat: float | None = None,
    lon: float | None = None,
    zip: str | None = Query(None, alias="zip"),
    radius_mi: float = Query(5.0, ge=1.0, le=25.0),
    fuel: str = Query("regular", pattern="^(regular|mid|premium|diesel)$"),
    limit: int = Query(30, ge=5, le=60),
):
    from backend.search_core import run_search

    try:
        return run_search(
            lat=lat,
            lon=lon,
            zip=zip,
            radius_mi=radius_mi,
            fuel=fuel,
            limit=limit,
            track=True,
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/api/report")
def api_report(body: ReportBody):
    try:
        return report_price(body.station_id, body.fuel, body.price, body.note)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/telegram/webhook")
async def api_telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    key: str | None = None,
):
    """
    Recibe updates de Telegram.
    Responde YA (ok) y procesa en segundo plano — evita bot 'pegado'
    cuando la búsqueda de precios tarda.
    """
    from backend.telegram_bot import alerts_secret, bot_ready, handle_update_safe

    if not bot_ready():
        raise HTTPException(503, "TELEGRAM_BOT_TOKEN no configurado")
    secret = alerts_secret()
    if secret and key != secret:
        raise HTTPException(401, "Clave webhook incorrecta")
    try:
        update = await request.json()
    except Exception as e:
        raise HTTPException(400, f"JSON inválido: {e}") from e
    # No bloquear la respuesta a Telegram (timeout ~60s; en free se corta antes)
    background_tasks.add_task(
        handle_update_safe, update if isinstance(update, dict) else {}
    )
    return {"ok": True}


@app.get("/api/telegram/setup")
def api_telegram_setup(key: str | None = None, base: str | None = None):
    """Registra el webhook en Telegram. ?key=ALERTS_SECRET"""
    from backend.telegram_bot import alerts_secret, bot_ready, get_me, set_webhook

    if not bot_ready():
        raise HTTPException(503, "Falta TELEGRAM_BOT_TOKEN en Render")
    secret = alerts_secret()
    if secret and key != secret:
        raise HTTPException(401, "Clave incorrecta (ALERTS_SECRET o STATS_KEY)")
    me = get_me()
    wh = set_webhook(base)
    return {
        "ok": bool(wh.get("ok")),
        "bot": me,
        "webhook": wh,
        "hint": "Abre t.me/GasRadar_bot y envía /start",
    }


@app.get("/api/alerts/run")
def api_alerts_run(key: str | None = None, force: bool = False):
    """
    Cron: revisa alertas y envía Telegram si el precio <= tope.
    Protegido con ALERTS_SECRET o STATS_KEY.
    """
    from backend.telegram_bot import alerts_secret, bot_ready, run_alert_checks

    if not bot_ready():
        raise HTTPException(503, "TELEGRAM_BOT_TOKEN no configurado")
    secret = alerts_secret()
    if not secret:
        raise HTTPException(
            503,
            "Configura ALERTS_SECRET (o STATS_KEY) para proteger el cron de alertas",
        )
    if key != secret:
        raise HTTPException(401, "Clave incorrecta")
    return run_alert_checks(force=force)


class VisitBody(BaseModel):
    path: str | None = "/"
    referrer: str | None = None
    lang: str | None = None


@app.post("/api/visit")
def api_visit(body: VisitBody):
    """Registro anónimo de visita (sin IP ni nombre)."""
    from backend.analytics import track_event

    track_event(
        "pageview",
        path=body.path or "/",
        referrer=body.referrer,
        lang=body.lang,
    )
    return {"ok": True}


@app.get("/api/stats")
def api_stats(key: str | None = None, days: int = Query(14, ge=1, le=90)):
    """Resumen de visitas — requiere ?key=STATS_KEY."""
    from backend.analytics import check_stats_key, summary

    if not check_stats_key(key):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")
    return summary(days=days)


# Static frontend
if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        return {"msg": "Frontend missing"}
    return FileResponse(index_path)


@app.get("/robots.txt")
def robots_txt():
    path = FRONTEND / "robots.txt"
    if not path.exists():
        raise HTTPException(404, "robots.txt missing")
    return FileResponse(path, media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap_xml():
    path = FRONTEND / "sitemap.xml"
    if not path.exists():
        raise HTTPException(404, "sitemap missing")
    return FileResponse(path, media_type="application/xml")


@app.get("/manifest.webmanifest")
def web_manifest():
    """Manifest PWA (iconos + modo standalone)."""
    path = FRONTEND / "manifest.webmanifest"
    if not path.exists():
        raise HTTPException(404, "Manifest missing")
    return FileResponse(
        path,
        media_type="application/manifest+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/sw.js")
def service_worker():
    """Service worker en la raíz para scope /."""
    path = FRONTEND / "sw.js"
    if not path.exists():
        raise HTTPException(404, "Service worker missing")
    return FileResponse(
        path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, must-revalidate",
            "Service-Worker-Allowed": "/",
        },
    )


@app.get("/privacy")
def privacy():
    """Política de privacidad (App Store / pie de página)."""
    path = FRONTEND / "privacy.html"
    if not path.exists():
        raise HTTPException(404, "Privacy page missing")
    return FileResponse(path)


@app.get("/stats")
def stats_page():
    """Panel de visitas (protegido en el JS con la clave)."""
    path = FRONTEND / "stats.html"
    if not path.exists():
        raise HTTPException(404, "Stats page missing")
    return FileResponse(path)
