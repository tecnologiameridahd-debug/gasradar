"""
Bot Telegram GasRadar — @GasRadar_bot
Webhook + envío de alertas (sin python-telegram-bot; solo httpx).
"""
from __future__ import annotations

import os
import re
from typing import Any

import httpx

from backend.alerts import (
    delete_alert,
    format_alert_summary,
    get_alert,
    list_active_alerts,
    mark_sent,
    upsert_alert,
)
from backend.geo import geocode_zip

BOT_USERNAME = "GasRadar_bot"
APP_URL = (os.environ.get("PUBLIC_APP_URL") or "https://gasradarapp.com").rstrip("/")


def _secret_from_local(*names: str) -> str:
    try:
        import config_local as cfg  # type: ignore

        for n in names:
            v = getattr(cfg, n, None)
            if v:
                return str(v).strip()
    except Exception:
        pass
    return ""


def telegram_token() -> str:
    return (
        (os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or "")
        .strip()
        or _secret_from_local("TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN")
    )


def alerts_secret() -> str:
    return (
        (os.environ.get("ALERTS_SECRET") or os.environ.get("STATS_KEY") or "")
        .strip()
        or _secret_from_local("ALERTS_SECRET", "STATS_KEY")
    )


def bot_ready() -> bool:
    return bool(telegram_token())


def _api(method: str, **payload: Any) -> dict:
    token = telegram_token()
    if not token:
        return {"ok": False, "error": "no_token"}
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        r = httpx.post(url, json=payload, timeout=25.0)
        return r.json() if r.content else {"ok": False, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def send_message(chat_id: str | int, text: str, *, disable_preview: bool = False) -> dict:
    return _api(
        "sendMessage",
        chat_id=chat_id,
        text=text[:4000],
        disable_web_page_preview=disable_preview,
    )


def send_typing(chat_id: str | int) -> None:
    try:
        _api("sendChatAction", chat_id=chat_id, action="typing")
    except Exception:
        pass


def handle_update_safe(update: dict) -> None:
    """Wrapper para BackgroundTasks: nunca tumba el worker."""
    try:
        handle_update(update if isinstance(update, dict) else {})
    except Exception as e:
        print(f"[telegram] handle_update: {type(e).__name__}: {e}")
        try:
            msg = (update or {}).get("message") or (update or {}).get("edited_message") or {}
            chat_id = (msg.get("chat") or {}).get("id")
            if chat_id is not None:
                send_message(
                    chat_id,
                    "⚠️ Error interno. Prueba /ahora de nuevo o /help",
                )
        except Exception:
            pass


def set_webhook(public_base: str | None = None) -> dict:
    base = (public_base or APP_URL).rstrip("/")
    secret = alerts_secret()
    wh = f"{base}/api/telegram/webhook"
    if secret:
        wh = f"{wh}?key={secret}"
    return _api("setWebhook", url=wh, drop_pending_updates=True)


def delete_webhook() -> dict:
    return _api("deleteWebhook", drop_pending_updates=True)


def get_me() -> dict:
    return _api("getMe")


HELP_ES = """⛽ GasRadar — alertas de gasolina

1) Elige zona (ZIP USA)
   /zona 80903

2) Precio tope (Regular)
   /alerta 3.50
   → te aviso si el más barato baja de $3.50

Otros
/fuel regular|mid|premium|diesel
/radio 5
/ahora — precios ya
/mis — tu configuración
/pausa · /activar
/borrar — quitar alerta
/help — esta ayuda

App: https://gasradarapp.com
Bot: t.me/GasRadar_bot
"""

HELP_EN = """⛽ GasRadar — gas price alerts

1) Set zone (US ZIP)
   /zona 80903

2) Max price (Regular)
   /alerta 3.50
   → alert when cheapest is under $3.50

Other
/fuel regular|mid|premium|diesel
/radio 5
/ahora — prices now
/mis — your settings
/pausa · /activar
/borrar — remove alert
/help

App: https://gasradarapp.com
"""


def _lang(chat_id: str | int) -> str:
    row = get_alert(chat_id)
    if row and row.get("lang") == "en":
        return "en"
    return "es"


def _parse_cmd(text: str) -> tuple[str, str]:
    t = (text or "").strip()
    if not t.startswith("/"):
        return "", t
    parts = t.split(maxsplit=1)
    cmd = parts[0].split("@")[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    return cmd, arg


def _money(p: float | None) -> str:
    if p is None:
        return "$—"
    return f"${float(p):.2f}"


def _format_now(data: dict, lang: str) -> str:
    center = data.get("center") or {}
    best = data.get("cheapest") or {}
    fuel = data.get("fuel") or "regular"
    n = data.get("count") or 0
    label = center.get("label") or center.get("zip") or "—"
    zip_c = center.get("zip") or ""
    if not best:
        return (
            f"Sin estaciones en {label}. Prueba /radio 10"
            if lang != "en"
            else f"No stations in {label}. Try /radio 10"
        )
    price = best.get("price")
    name = best.get("name") or "—"
    dist = best.get("distance_mi")
    maps = ""
    if best.get("lat") is not None and best.get("lon") is not None:
        maps = f"https://www.google.com/maps/dir/?api=1&destination={best['lat']},{best['lon']}"
    app = f"{APP_URL}/?zip={zip_c}" if zip_c else APP_URL
    if lang == "en":
        lines = [
            f"⛽ GasRadar · {label}",
            f"Cheapest {fuel}: {_money(price)}",
            f"★ {name}" + (f" · {float(dist):.1f} mi" if dist is not None else ""),
            f"{n} stations nearby",
        ]
        if maps:
            lines.append(f"📍 {maps}")
        lines.append(f"🌐 {app}")
    else:
        lines = [
            f"⛽ GasRadar · {label}",
            f"Más barata ({fuel}): {_money(price)}",
            f"★ {name}" + (f" · {float(dist):.1f} mi" if dist is not None else ""),
            f"{n} estaciones cerca",
        ]
        if maps:
            lines.append(f"📍 {maps}")
        lines.append(f"🌐 {app}")
    return "\n".join(lines)


def handle_update(update: dict) -> None:
    """Procesa un update de Telegram (webhook)."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return
    text = msg.get("text") or ""
    cmd, arg = _parse_cmd(text)
    lang = _lang(chat_id)
    send_typing(chat_id)

    # deep-link /start 80903
    if cmd == "/start":
        if arg and re.fullmatch(r"\d{5}", arg.strip()):
            _cmd_zona(chat_id, arg.strip(), lang)
            return
        send_message(chat_id, HELP_ES if lang != "en" else HELP_EN)
        return

    if cmd in ("/help", "/ayuda", "/start"):
        send_message(chat_id, HELP_ES if lang != "en" else HELP_EN)
        return

    if cmd in ("/en",):
        upsert_alert(chat_id, lang="en")
        send_message(chat_id, "Language: English. /help for commands.")
        return
    if cmd in ("/es",):
        upsert_alert(chat_id, lang="es")
        send_message(chat_id, "Idioma: español. /help para comandos.")
        return

    if cmd in ("/zona", "/zip", "/city", "/ciudad"):
        _cmd_zona(chat_id, arg, lang)
        return

    if cmd in ("/alerta", "/alert", "/tope", "/max"):
        _cmd_alerta(chat_id, arg, lang)
        return

    if cmd in ("/fuel", "/gas", "/combustible"):
        _cmd_fuel(chat_id, arg, lang)
        return

    if cmd in ("/radio", "/radius"):
        _cmd_radio(chat_id, arg, lang)
        return

    if cmd in ("/mis", "/me", "/status", "/config"):
        send_message(chat_id, format_alert_summary(get_alert(chat_id), lang))
        return

    if cmd in ("/pausa", "/pause", "/stop"):
        upsert_alert(chat_id, active=0)
        send_message(
            chat_id,
            "⏸️ Alerta pausada. /activar para reanudar"
            if lang != "en"
            else "⏸️ Alert paused. /activar to resume",
        )
        return

    if cmd in ("/activar", "/resume", "/on"):
        upsert_alert(chat_id, active=1)
        send_message(
            chat_id,
            "▶️ Alerta activa." if lang != "en" else "▶️ Alert ON.",
        )
        return

    if cmd in ("/borrar", "/delete", "/remove"):
        delete_alert(chat_id)
        send_message(
            chat_id,
            "🗑️ Alerta eliminada." if lang != "en" else "🗑️ Alert removed.",
        )
        return

    if cmd in ("/ahora", "/now", "/precios", "/prices"):
        _cmd_ahora(chat_id, lang)
        return

    # texto libre: si parece ZIP
    if re.fullmatch(r"\d{5}", text.strip()):
        _cmd_zona(chat_id, text.strip(), lang)
        return

    # precio suelto tipo 3.50
    m = re.fullmatch(r"\$?\s*(\d{1,2}([.,]\d{1,3})?)", text.strip())
    if m:
        _cmd_alerta(chat_id, m.group(1), lang)
        return

    send_message(
        chat_id,
        "No entendí. Prueba /help\nEj: /zona 80903  ·  /alerta 3.50  ·  /ahora"
        if lang != "en"
        else "Didn't get that. Try /help\nEx: /zona 80903  ·  /alerta 3.50  ·  /ahora",
    )


def _cmd_zona(chat_id: int, arg: str, lang: str) -> None:
    raw = (arg or "").strip()
    # deep link payload
    if raw.startswith("zip_"):
        raw = raw[4:]
    digits = re.sub(r"\D", "", raw)[:5]
    if len(digits) != 5:
        send_message(
            chat_id,
            "Usa un ZIP de 5 dígitos.\nEj: /zona 80903"
            if lang != "en"
            else "Use a 5-digit US ZIP.\nEx: /zona 80903",
        )
        return
    g = geocode_zip(digits)
    if not g:
        send_message(
            chat_id,
            f"ZIP {digits} no encontrado." if lang != "en" else f"ZIP {digits} not found.",
        )
        return
    label = g.get("label") or digits
    upsert_alert(chat_id, zip=digits, label=label, active=1)
    row = get_alert(chat_id)
    mx = row.get("max_price") if row else None
    if lang == "en":
        msg = f"✅ Zone set: {label} ({digits})"
        if mx:
            msg += f"\nMax price: ${_money(float(mx)).lstrip('$')}\n/ahora for prices now."
        else:
            msg += "\nNow set max price: /alerta 3.50"
    else:
        msg = f"✅ Zona: {label} ({digits})"
        if mx:
            msg += f"\nTope: {_money(float(mx))}\n/ahora para ver precios."
        else:
            msg += "\nAhora pon el tope: /alerta 3.50"
    send_message(chat_id, msg)


def _cmd_alerta(chat_id: int, arg: str, lang: str) -> None:
    raw = (arg or "").strip().replace(",", ".").replace("$", "")
    try:
        price = float(raw)
    except Exception:
        send_message(
            chat_id,
            "Ejemplo: /alerta 3.50" if lang != "en" else "Example: /alerta 3.50",
        )
        return
    if price < 1.0 or price > 12.0:
        send_message(
            chat_id,
            "Precio entre 1 y 12 USD." if lang != "en" else "Price between $1 and $12.",
        )
        return
    row = get_alert(chat_id)
    if not row or not row.get("zip"):
        upsert_alert(chat_id, max_price=round(price, 3), active=1)
        send_message(
            chat_id,
            f"✅ Tope {_money(price)}. Falta la zona: /zona 80903"
            if lang != "en"
            else f"✅ Max {_money(price)}. Set zone: /zona 80903",
        )
        return
    upsert_alert(chat_id, max_price=round(price, 3), active=1)
    send_message(
        chat_id,
        f"✅ Te aviso si el más barato en {row.get('zip')} baja de {_money(price)}.\n"
        f"(Máx. 1 aviso por día)\n/ahora · /mis · /pausa"
        if lang != "en"
        else f"✅ Alert if cheapest in {row.get('zip')} goes under {_money(price)}.\n"
        f"(Max 1 alert/day)\n/ahora · /mis · /pausa",
    )


def _cmd_fuel(chat_id: int, arg: str, lang: str) -> None:
    fuel = (arg or "regular").strip().lower()
    if fuel not in ("regular", "mid", "premium", "diesel"):
        send_message(
            chat_id,
            "Usa: /fuel regular|mid|premium|diesel",
        )
        return
    upsert_alert(chat_id, fuel=fuel)
    send_message(
        chat_id,
        f"✅ Combustible: {fuel}" if lang != "en" else f"✅ Fuel: {fuel}",
    )


def _cmd_radio(chat_id: int, arg: str, lang: str) -> None:
    try:
        r = float((arg or "5").strip())
    except Exception:
        send_message(chat_id, "Ej: /radio 5")
        return
    r = max(1.0, min(25.0, r))
    upsert_alert(chat_id, radius_mi=r)
    send_message(
        chat_id,
        f"✅ Radio: {r:g} mi" if lang != "en" else f"✅ Radius: {r:g} mi",
    )


def _cmd_ahora(chat_id: int, lang: str) -> None:
    row = get_alert(chat_id)
    if not row or not row.get("zip"):
        send_message(
            chat_id,
            "Primero /zona 80903" if lang != "en" else "First /zona 80903",
        )
        return
    send_message(
        chat_id,
        "🔎 Buscando precios… (unos segundos)"
        if lang != "en"
        else "🔎 Searching prices… (a few seconds)",
    )
    send_typing(chat_id)
    try:
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

        from backend.search_core import run_search

        def _job():
            return run_search(
                zip=str(row["zip"]),
                fuel=str(row.get("fuel") or "regular"),
                radius_mi=float(row.get("radius_mi") or 5),
                limit=12,
                track=False,
                quick=True,
            )

        # Evita colgar el bot más de 25s (Render free + Zyla)
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_job)
            try:
                data = fut.result(timeout=25)
            except FuturesTimeout:
                send_message(
                    chat_id,
                    "⏱️ Tardó mucho. Prueba de nuevo /ahora o otro ZIP."
                    if lang != "en"
                    else "⏱️ Timed out. Try /ahora again or another ZIP.",
                )
                return
        send_message(chat_id, _format_now(data, lang), disable_preview=True)
    except ValueError as e:
        send_message(chat_id, str(e))
    except Exception as e:
        print(f"[telegram /ahora] {type(e).__name__}: {e}")
        send_message(
            chat_id,
            f"Error al buscar: {type(e).__name__}. Prueba /ahora otra vez."
            if lang != "en"
            else f"Search error: {type(e).__name__}. Try /ahora again.",
        )


def run_alert_checks(*, force: bool = False) -> dict:
    """
    Revisa suscriptores activos y envía si cheapest <= max_price.
    Máx. 1 aviso por día por chat (salvo force=True).
    """
    from datetime import datetime, timezone

    from backend.search_core import run_search

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = list_active_alerts()
    # cache por (zip, fuel, radius)
    cache: dict[tuple, dict] = {}
    sent = 0
    skipped = 0
    errors = 0
    checked = 0

    for row in rows:
        checked += 1
        chat_id = row["chat_id"]
        zip_c = str(row.get("zip") or "")
        fuel = str(row.get("fuel") or "regular")
        radius = float(row.get("radius_mi") or 5)
        max_p = row.get("max_price")
        lang = row.get("lang") or "es"
        if max_p is None:
            skipped += 1
            continue
        if not force and row.get("last_sent_day") == today:
            skipped += 1
            continue

        key = (zip_c, fuel, round(radius, 1))
        try:
            if key not in cache:
                cache[key] = run_search(
                    zip=zip_c,
                    fuel=fuel,
                    radius_mi=radius,
                    limit=12,
                    track=False,
                    quick=True,
                )
            data = cache[key]
        except Exception as e:
            print(f"[alerts] search {zip_c}: {e}")
            errors += 1
            continue

        best = data.get("cheapest") or {}
        price = best.get("price")
        if price is None:
            skipped += 1
            continue
        if float(price) > float(max_p):
            skipped += 1
            continue

        body = _format_now(data, lang)
        if lang == "en":
            header = f"🚨 Price alert!\nYour max: {_money(float(max_p))}\n\n"
        else:
            header = f"🚨 ¡Alerta de precio!\nTu tope: {_money(float(max_p))}\n\n"
        res = send_message(chat_id, header + body, disable_preview=True)
        if res.get("ok"):
            mark_sent(chat_id, float(price))
            sent += 1
        else:
            errors += 1
            print(f"[alerts] send {chat_id}: {res}")

    return {
        "ok": True,
        "checked": checked,
        "sent": sent,
        "skipped": skipped,
        "errors": errors,
        "unique_searches": len(cache),
    }
