"""
Bot Telegram GasRadar — @GasRadar_bot
Webhook fiable (procesa en la misma petición) + teclado + alertas.
"""
from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote

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


def _normalize_secret(value: str | None) -> str:
    """Quita espacios, comillas y decodifica URL (?key=...)."""
    from urllib.parse import unquote

    if value is None:
        return ""
    s = unquote(str(value)).strip()
    # Render a veces guarda "mi_clave" con comillas
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    # Espacios raros / saltos
    s = s.replace("\r", "").replace("\n", "").strip()
    return s


def alerts_secret() -> str:
    raw = (
        (os.environ.get("ALERTS_SECRET") or os.environ.get("STATS_KEY") or "")
        or _secret_from_local("ALERTS_SECRET", "STATS_KEY")
    )
    return _normalize_secret(raw)


def check_alerts_key(key: str | None) -> bool:
    """True si la clave del URL coincide con ALERTS_SECRET o STATS_KEY."""
    secret = alerts_secret()
    if not secret:
        # Sin secret en servidor: permitir (solo para setup inicial)
        return True
    provided = _normalize_secret(key)
    if not provided:
        return False
    if provided == secret:
        return True
    # Aceptar también la versión “limpia” (solo letras/números) por si copió mal
    clean_secret = re.sub(r"[^A-Za-z0-9_-]", "", secret)
    clean_key = re.sub(r"[^A-Za-z0-9_-]", "", provided)
    if clean_secret and clean_key and clean_secret == clean_key:
        return True
    return False


def key_error_hint(key: str | None) -> str:
    """Mensaje de error sin revelar la clave real."""
    secret = alerts_secret()
    provided = _normalize_secret(key)
    env_a = _normalize_secret(os.environ.get("ALERTS_SECRET"))
    env_s = _normalize_secret(os.environ.get("STATS_KEY"))
    active = "ALERTS_SECRET" if env_a else ("STATS_KEY" if env_s else "ninguna")
    if not secret:
        return (
            "No hay ALERTS_SECRET ni STATS_KEY en Render. "
            "Crea ALERTS_SECRET, Save, espera Live."
        )
    if not provided:
        return (
            "Falta ?key= en la URL. "
            "Ejemplo: /api/telegram/setup?key=TU_ALERTS_SECRET"
        )
    return (
        f"Clave incorrecta. Enviaste {len(provided)} caracteres. "
        f"El servidor usa {active} ({len(secret)} caracteres). "
        f"ALERTS_SECRET={len(env_a) or 0} chars, STATS_KEY={len(env_s) or 0} chars. "
        f"Deben coincidir exactamente. Si cambiaste la variable, Save + espera Live."
    )


def webhook_secret_token() -> str:
    """Telegram solo permite A-Z a-z 0-9 _ - en secret_token."""
    raw = alerts_secret() or "gasradar"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", raw)[:256]
    return cleaned or "gasradar"


def bot_ready() -> bool:
    return bool(telegram_token())


def _api(method: str, **payload: Any) -> dict:
    token = telegram_token()
    if not token:
        return {"ok": False, "error": "no_token"}
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        r = httpx.post(url, json=payload, timeout=30.0)
        data = r.json() if r.content else {"ok": False, "status": r.status_code}
        if not data.get("ok"):
            print(f"[telegram {method}] {data}")
        return data
    except Exception as e:
        print(f"[telegram {method}] {type(e).__name__}: {e}")
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _keyboard(lang: str = "es") -> dict:
    """Botones siempre visibles (más fácil que memorizar comandos)."""
    if lang == "en":
        rows = [
            [{"text": "⛽ Prices now"}, {"text": "📍 Set ZIP"}],
            [{"text": "🔔 My alert"}, {"text": "⚙️ Status"}],
            [{"text": "❓ Help"}, {"text": "🌐 Español"}],
        ]
    else:
        rows = [
            [{"text": "⛽ Precios ahora"}, {"text": "📍 Poner ZIP"}],
            [{"text": "🔔 Mi alerta"}, {"text": "⚙️ Estado"}],
            [{"text": "❓ Ayuda"}, {"text": "🌐 English"}],
        ]
    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


def send_message(
    chat_id: str | int,
    text: str,
    *,
    disable_preview: bool = True,
    lang: str | None = None,
    with_keyboard: bool = True,
) -> dict:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": (text or "")[:4000],
        "disable_web_page_preview": disable_preview,
    }
    if with_keyboard:
        lg = lang or _lang(chat_id)
        payload["reply_markup"] = _keyboard(lg)
    return _api("sendMessage", **payload)


def send_typing(chat_id: str | int) -> None:
    try:
        _api("sendChatAction", chat_id=chat_id, action="typing")
    except Exception:
        pass


def handle_update_safe(update: dict) -> None:
    """Nunca tumba el worker."""
    try:
        handle_update(update if isinstance(update, dict) else {})
    except Exception as e:
        print(f"[telegram] handle_update: {type(e).__name__}: {e}")
        try:
            msg = (update or {}).get("message") or (update or {}).get("edited_message") or {}
            chat_id = (msg.get("chat") or {}).get("id")
            if chat_id is not None:
                lg = _lang(chat_id)
                send_message(
                    chat_id,
                    "⚠️ Error interno. Toca ⛽ Precios ahora o escribe /ahora"
                    if lg != "en"
                    else "⚠️ Internal error. Tap ⛽ Prices now or type /now",
                    lang=lg,
                )
        except Exception:
            pass


def set_webhook(
    public_base: str | None = None,
    *,
    drop_pending: bool = False,
) -> dict:
    """Registra el webhook. Por defecto NO borra mensajes pendientes (evita perder /start en redeploy)."""
    base = (public_base or APP_URL).rstrip("/")
    secret = alerts_secret()
    # URL + key (por si el header no llega) y secret_token oficial de Telegram
    wh = f"{base}/api/telegram/webhook"
    if secret:
        wh = f"{wh}?key={quote(secret, safe='')}"
    return _api(
        "setWebhook",
        url=wh,
        drop_pending_updates=bool(drop_pending),
        allowed_updates=["message"],
        secret_token=webhook_secret_token(),
    )


def delete_webhook() -> dict:
    return _api("deleteWebhook", drop_pending_updates=True)


def get_me() -> dict:
    return _api("getMe")


def get_webhook_info() -> dict:
    return _api("getWebhookInfo")


HELP_ES = """⛽ GasRadar — gasolina barata

Usa los botones de abajo o escribe:

1️⃣ ZIP de 5 dígitos → 80903
2️⃣ Tope de precio → 3.50 o /alerta 3.50
3️⃣ ⛽ Precios ahora → ver las más baratas

Comandos:
/zona 80903 · /alerta 3.50 · /ahora
/donar 5 · /mis · /pausa · /activar · /borrar
/es · /en  (idioma)

App: gasradarapp.com
"""

HELP_EN = """⛽ GasRadar — cheap gas nearby

Use the buttons below or type:

1️⃣ 5-digit ZIP → 80903
2️⃣ Max price → 3.50 or /alert 3.50
3️⃣ ⛽ Prices now → cheapest stations

Commands:
/zip 80903 · /alert 3.50 · /now
/donate 5 · /status · /pause · /resume · /delete
/es · /en  (language)

App: gasradarapp.com
"""

# Mensajes i18n (es / en)
_MSG: dict[str, dict[str, str]] = {
    "empty_text": {
        "es": "Escribe un ZIP (80903) o toca un botón 👇",
        "en": "Type a ZIP (80903) or tap a button 👇",
    },
    "welcome": {
        "es": (
            "¡Hola! ⛽ Soy GasRadar.\n\n"
            "Te ayudo a ver la gasolina más barata y a avisarte si baja.\n\n"
            "👉 Escribe tu ZIP (ej. 80903)\n"
            "o toca un botón abajo."
        ),
        "en": (
            "Hi! ⛽ I'm GasRadar.\n\n"
            "I show the cheapest gas nearby and can alert you when it drops.\n\n"
            "👉 Type your ZIP (e.g. 80903)\n"
            "or tap a button below."
        ),
    },
    "ask_zip": {
        "es": "📍 Escribe tu ZIP de 5 dígitos\nEjemplo: 80903",
        "en": "📍 Type your 5-digit ZIP\nExample: 80903",
    },
    "need_zip_first": {
        "es": "Primero pon tu ZIP (ej. 80903), luego el tope (ej. 3.50)",
        "en": "First set your ZIP (e.g. 80903), then max price (e.g. 3.50)",
    },
    "ask_max": {
        "es": "🔔 Zona {zip}.\nEscribe el precio tope, ej: 3.50\n(Te aviso si baja de ese precio)",
        "en": "🔔 Zone {zip}.\nType max price, e.g. 3.50\n(I'll alert if gas goes under that)",
    },
    "lang_en": {"es": "Language: English ✅", "en": "Language: English ✅"},
    "lang_es": {"es": "Idioma: español ✅", "en": "Idioma: español ✅"},
    "paused": {
        "es": "⏸️ Alerta pausada. /activar para reanudar",
        "en": "⏸️ Alert paused. /resume to turn back on",
    },
    "resumed": {"es": "▶️ Alerta activa.", "en": "▶️ Alert ON."},
    "deleted": {
        "es": "🗑️ Alerta eliminada. Escribe un ZIP para empezar de nuevo.",
        "en": "🗑️ Alert removed. Type a ZIP to start again.",
    },
    "need_zip_prices": {
        "es": "📍 Primero tu ZIP.\nEscribe ej: 80903",
        "en": "📍 First set your ZIP.\nType e.g. 80903",
    },
    "searching": {
        "es": "🔎 Buscando precios en {label}…",
        "en": "🔎 Searching prices in {label}…",
    },
    "timeout": {
        "es": "⏱️ Tardó mucho. Prueba otra vez ⛽ o abre:\n{url}",
        "en": "⏱️ Timed out. Try ⛽ again or open:\n{url}",
    },
    "search_fail": {
        "es": "No pude buscar ahora ({err}).\nAbre la app: {url}",
        "en": "Search failed ({err}).\nOpen the app: {url}",
    },
    "bad_zip": {
        "es": "ZIP de 5 dígitos, ej: 80903",
        "en": "5-digit ZIP, e.g. 80903",
    },
    "zip_not_found": {
        "es": "ZIP {zip} no encontrado. Prueba otro.",
        "en": "ZIP {zip} not found. Try another.",
    },
    "bad_price": {
        "es": "Ejemplo de tope: 3.50",
        "en": "Example max: 3.50",
    },
    "price_range": {
        "es": "Precio entre $1 y $12.",
        "en": "Price between $1 and $12.",
    },
    "unknown": {
        "es": (
            "No entendí 😅\n\n"
            "• ZIP: 80903\n"
            "• Tope: 3.50\n"
            "• O toca ⛽ Precios ahora\n"
            "• Donar: /donar 5\n"
            "• Idioma: /en o /es"
        ),
        "en": (
            "Didn't get that 😅\n\n"
            "• ZIP: 80903\n"
            "• Max: 3.50\n"
            "• Or tap ⛽ Prices now\n"
            "• Donate: /donate 5\n"
            "• Language: /en or /es"
        ),
    },
    "no_prices": {
        "es": (
            "Sin precios en {label} ahora.\n"
            "Prueba de nuevo en unos segundos, sube el radio (/radio 10)\n"
            "o abre la app:\n{url}"
        ),
        "en": (
            "No prices in {label} right now.\n"
            "Try again in a few seconds, widen radius (/radius 10)\n"
            "or open the app:\n{url}"
        ),
    },
}


def _t(key: str, lang: str, **kwargs: Any) -> str:
    block = _MSG.get(key) or {}
    text = block.get("en" if lang == "en" else "es") or block.get("es") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def _lang(chat_id: str | int) -> str:
    row = get_alert(chat_id)
    if row and str(row.get("lang") or "").lower().startswith("en"):
        return "en"
    return "es"


def _detect_lang(language_code: str | None) -> str:
    """Mapea language_code de Telegram a es/en."""
    lc = (language_code or "").lower().replace("_", "-")
    if not lc:
        return "es"
    if lc.startswith("en"):
        return "en"
    # es, es-MX, es-ES, pt, fr… → español por defecto (comunidad GasRadar)
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


def _is_live_price(station: dict) -> bool:
    src = (
        station.get("price_source")
        or station.get("source")
        or ""
    )
    src = str(src).lower()
    if src in ("gasbuddy", "user", "live", "vps", "report"):
        return True
    prices = station.get("prices") or {}
    if isinstance(prices, dict):
        for v in prices.values():
            if isinstance(v, dict) and str(v.get("source") or "").lower() in (
                "gasbuddy",
                "user",
                "live",
                "vps",
            ):
                return True
    return False


def _map_button(text: str, lang: str) -> tuple[str, str] | None:
    """Convierte texto de botón en comando (ES y EN, independientes del idioma guardado)."""
    t = (text or "").strip().lower()
    # Idioma
    if t in ("🌐 english", "english", "idioma english", "language english"):
        return "/en", ""
    if t in ("🌐 español", "español", "espanol", "idioma español", "language español"):
        return "/es", ""
    # ES
    if t in ("⛽ precios ahora", "precios ahora", "precios", "ahora"):
        return "/ahora", ""
    if t in ("📍 poner zip", "poner zip", "zip", "zona"):
        return "/pedir_zip", ""
    if t in ("🔔 mi alerta", "mi alerta", "alerta"):
        return "/pedir_alerta", ""
    if t in ("⚙️ estado", "estado", "mis", "config"):
        return "/mis", ""
    if t in ("❓ ayuda", "ayuda"):
        return "/help", ""
    if t in ("dóname", "doname", "donar", "donate", "donación", "donacion"):
        return "/donar", ""
    # EN
    if t in ("⛽ prices now", "prices now", "prices", "now"):
        return "/ahora", ""
    if t in ("📍 set zip", "set zip"):
        return "/pedir_zip", ""
    if t in ("🔔 my alert", "my alert"):
        return "/pedir_alerta", ""
    if t in ("⚙️ status", "status"):
        return "/mis", ""
    if t in ("❓ help", "help"):
        return "/help", ""
    return None


def _format_now(data: dict, lang: str) -> str:
    center = data.get("center") or {}
    best = data.get("cheapest") or {}
    fuel = data.get("fuel") or "regular"
    n = int(data.get("count") or 0)
    label = center.get("label") or center.get("zip") or "—"
    zip_c = center.get("zip") or ""
    cached = " ⚡" if data.get("cached") else ""
    live_flag = bool(data.get("live_prices"))
    stations = list(data.get("stations") or [])

    if (not best or best.get("price") is None) and stations:
        best = stations[0]
    if not best or best.get("price") is None:
        return _t(
            "no_prices",
            lang,
            label=label,
            url=f"{APP_URL}/?zip={zip_c}" if zip_c else APP_URL,
        )

    price = best.get("price")
    name = best.get("name") or "—"
    dist = best.get("distance_mi")
    maps = ""
    if best.get("lat") is not None and best.get("lon") is not None:
        maps = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&destination={best['lat']},{best['lon']}"
        )
    app = f"{APP_URL}/?zip={zip_c}" if zip_c else APP_URL
    save = best.get("savings_vs_avg")
    best_live = _is_live_price(best) or live_flag

    if lang == "en":
        src_tag = "🟢 live" if best_live else "🟡 estimate"
        lines = [
            f"⛽ GasRadar · {label}{cached}",
            f"Cheapest ({fuel}): {_money(price)}  {src_tag}",
            f"★ {name}" + (f" · ~{float(dist):.1f} mi" if dist is not None else ""),
        ]
        if save is not None and float(save) > 0.01:
            lines.append(f"💰 ~{_money(float(save))}/gal under area avg")
        # Top 3
        extras = []
        for s in stations[:3]:
            if s is best or (
                s.get("name") == name and s.get("price") == price
            ):
                continue
            if s.get("price") is None:
                continue
            tag = "🟢" if _is_live_price(s) else "🟡"
            d = s.get("distance_mi")
            extras.append(
                f"{tag} {_money(s.get('price'))} · {s.get('name') or '—'}"
                + (f" · ~{float(d):.1f} mi" if d is not None else "")
            )
            if len(extras) >= 2:
                break
        if extras:
            lines.append("")
            lines.append("Also nearby:")
            lines.extend(extras)
        lines.append("")
        lines.append(f"{n} station(s)" + (" · live prices" if live_flag else " · ref. prices"))
        if maps:
            lines.append(f"📍 Directions:\n{maps}")
        lines.append(f"🌐 App: {app}")
        lines.append("\n🔔 Alert: type e.g. 3.50")
    else:
        src_tag = "🟢 en vivo" if best_live else "🟡 estimado"
        lines = [
            f"⛽ GasRadar · {label}{cached}",
            f"Más barata ({fuel}): {_money(price)}  {src_tag}",
            f"★ {name}" + (f" · ~{float(dist):.1f} mi" if dist is not None else ""),
        ]
        if save is not None and float(save) > 0.01:
            lines.append(f"💰 Ahorras ~{_money(float(save))}/gal vs promedio")
        extras = []
        for s in stations[:3]:
            if s is best or (
                s.get("name") == name and s.get("price") == price
            ):
                continue
            if s.get("price") is None:
                continue
            tag = "🟢" if _is_live_price(s) else "🟡"
            d = s.get("distance_mi")
            extras.append(
                f"{tag} {_money(s.get('price'))} · {s.get('name') or '—'}"
                + (f" · ~{float(d):.1f} mi" if d is not None else "")
            )
            if len(extras) >= 2:
                break
        if extras:
            lines.append("")
            lines.append("Cerca también:")
            lines.extend(extras)
        lines.append("")
        lines.append(
            f"{n} estación(es)"
            + (" · precios en vivo" if live_flag else " · precios de referencia")
        )
        if maps:
            lines.append(f"📍 Cómo llegar:\n{maps}")
        lines.append(f"🌐 App: {app}")
        lines.append("\n🔔 Alerta: escribe ej. 3.50")
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

    # Respuesta rápida: typing ya (Render free a veces tarda al despertar)
    send_typing(chat_id)

    # Idioma: primera vez desde language_code de Telegram; luego preferencia guardada
    from_user = msg.get("from") or {}
    row0 = get_alert(chat_id)
    if not row0:
        detected = _detect_lang(from_user.get("language_code"))
        upsert_alert(chat_id, lang=detected)

    text = (msg.get("text") or "").strip()
    if not text:
        send_message(chat_id, _t("empty_text", _lang(chat_id)), lang=_lang(chat_id))
        return

    lang = _lang(chat_id)
    mapped = _map_button(text, lang)
    if mapped:
        cmd, arg = mapped
    else:
        cmd, arg = _parse_cmd(text)

    send_typing(chat_id)

    # deep-link /start 80903
    if cmd == "/start":
        payload = (arg or "").strip()
        if payload.startswith("zip_"):
            payload = payload[4:]
        # /start puede traer idioma si el usuario no tenía fila (ya se creó arriba)
        if re.fullmatch(r"\d{5}", payload):
            _cmd_zona(chat_id, payload, lang, auto_prices=True)
            return
        help_txt = HELP_EN if lang == "en" else HELP_ES
        send_message(
            chat_id,
            _t("welcome", lang) + "\n\n" + help_txt,
            lang=lang,
        )
        return

    if cmd in ("/help", "/ayuda"):
        send_message(
            chat_id,
            HELP_EN if lang == "en" else HELP_ES,
            lang=lang,
        )
        return

    if cmd == "/pedir_zip":
        send_message(chat_id, _t("ask_zip", lang), lang=lang)
        return

    if cmd == "/pedir_alerta":
        row = get_alert(chat_id)
        z = (row or {}).get("zip")
        if not z:
            send_message(chat_id, _t("need_zip_first", lang), lang=lang)
            return
        send_message(chat_id, _t("ask_max", lang, zip=z), lang=lang)
        return

    if cmd in ("/en", "/english", "/lang_en"):
        upsert_alert(chat_id, lang="en")
        send_message(chat_id, _t("lang_en", "en"), lang="en")
        return
    if cmd in ("/es", "/espanol", "/español", "/lang_es"):
        upsert_alert(chat_id, lang="es")
        send_message(chat_id, _t("lang_es", "es"), lang="es")
        return
    if cmd in ("/lang", "/idioma", "/language"):
        arg_l = (arg or "").strip().lower()
        if arg_l.startswith("en"):
            upsert_alert(chat_id, lang="en")
            send_message(chat_id, _t("lang_en", "en"), lang="en")
        elif arg_l.startswith("es"):
            upsert_alert(chat_id, lang="es")
            send_message(chat_id, _t("lang_es", "es"), lang="es")
        else:
            send_message(
                chat_id,
                "Language / Idioma:\n/en · English\n/es · Español",
                lang=lang,
            )
        return

    if cmd in ("/zona", "/zip", "/city", "/ciudad"):
        _cmd_zona(chat_id, arg, lang, auto_prices=True)
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
        send_message(chat_id, format_alert_summary(get_alert(chat_id), lang), lang=lang)
        return

    if cmd in ("/pausa", "/pause", "/stop"):
        upsert_alert(chat_id, active=0)
        send_message(chat_id, _t("paused", lang), lang=lang)
        return

    if cmd in ("/activar", "/resume", "/on"):
        upsert_alert(chat_id, active=1)
        send_message(chat_id, _t("resumed", lang), lang=lang)
        return

    if cmd in ("/borrar", "/delete", "/remove"):
        delete_alert(chat_id)
        send_message(chat_id, _t("deleted", lang), lang=lang)
        return

    if cmd in ("/ahora", "/now", "/precios", "/prices"):
        _cmd_ahora(chat_id, lang)
        return

    if cmd in ("/donar", "/donate", "/doname", "/dóname", "/donation"):
        _cmd_donar(chat_id, arg, lang)
        return

    # texto libre: ZIP
    if re.fullmatch(r"\d{5}", text):
        _cmd_zona(chat_id, text, lang, auto_prices=True)
        return

    # precio suelto 3.50 / $3.50
    m = re.fullmatch(r"\$?\s*(\d{1,2}([.,]\d{1,3})?)", text)
    if m:
        _cmd_alerta(chat_id, m.group(1), lang)
        return

    send_message(chat_id, _t("unknown", lang), lang=lang)


def _cmd_donar(chat_id: int, arg: str, lang: str) -> None:
    raw = (arg or "").strip().replace(",", ".").replace("$", "")
    web = f"{APP_URL}/?donate=1"
    if not raw:
        if lang == "en":
            send_message(
                chat_id,
                "💛 Donate any amount.\n\n"
                "• /donate 5\n"
                "• /donate 10\n"
                f"• Or open: {web}",
                lang=lang,
            )
        else:
            send_message(
                chat_id,
                "💛 Dóname lo que quieras.\n\n"
                "• /donar 5\n"
                "• /donar 10\n"
                f"• O abre: {web}",
                lang=lang,
            )
        return
    try:
        amount = float(raw)
    except Exception:
        send_message(
            chat_id,
            "Ej: /donar 5" if lang != "en" else "E.g. /donate 5",
            lang=lang,
        )
        return
    try:
        from backend.donate import create_checkout, stripe_configured

        if not stripe_configured():
            send_message(chat_id, f"💛 {web}", lang=lang)
            return
        sess = create_checkout(amount)
        url = sess.get("url") or web
        if lang == "en":
            send_message(
                chat_id,
                f"💛 Donate ${amount:.2f}\nTap to pay with Stripe:\n{url}",
                lang=lang,
            )
        else:
            send_message(
                chat_id,
                f"💛 Donar ${amount:.2f}\nToca para pagar con Stripe:\n{url}",
                lang=lang,
            )
    except ValueError as e:
        send_message(chat_id, str(e), lang=lang)
    except Exception:
        send_message(chat_id, f"💛 {web}", lang=lang)


def _cmd_zona(
    chat_id: int, arg: str, lang: str, *, auto_prices: bool = False
) -> None:
    raw = (arg or "").strip()
    if raw.startswith("zip_"):
        raw = raw[4:]
    digits = re.sub(r"\D", "", raw)[:5]
    if len(digits) != 5:
        send_message(chat_id, _t("bad_zip", lang), lang=lang)
        return
    g = geocode_zip(digits)
    if not g:
        send_message(chat_id, _t("zip_not_found", lang, zip=digits), lang=lang)
        return
    label = g.get("label") or digits
    upsert_alert(chat_id, zip=digits, label=label, active=1)
    row = get_alert(chat_id)
    mx = row.get("max_price") if row else None

    if lang == "en":
        msg = f"✅ Zone: {label}\nZIP {digits}"
        if mx:
            msg += f"\n🔔 Alert under {_money(float(mx))}"
        else:
            msg += "\n🔔 Optional: type a max price e.g. 3.50"
    else:
        msg = f"✅ Zona: {label}\nZIP {digits}"
        if mx:
            msg += f"\n🔔 Alerta bajo {_money(float(mx))}"
        else:
            msg += "\n🔔 Opcional: escribe un tope ej. 3.50"

    send_message(chat_id, msg, lang=lang)

    # Tras poner ZIP, buscar precios al momento (lo que la gente espera)
    if auto_prices:
        _cmd_ahora(chat_id, lang)


def _cmd_alerta(chat_id: int, arg: str, lang: str) -> None:
    raw = (arg or "").strip().replace(",", ".").replace("$", "")
    try:
        price = float(raw)
    except Exception:
        send_message(chat_id, _t("bad_price", lang), lang=lang)
        return
    if price < 1.0 or price > 12.0:
        send_message(chat_id, _t("price_range", lang), lang=lang)
        return
    row = get_alert(chat_id)
    if not row or not row.get("zip"):
        upsert_alert(chat_id, max_price=round(price, 3), active=1)
        send_message(
            chat_id,
            f"✅ Tope {_money(price)}.\nAhora escribe tu ZIP (ej. 80903)"
            if lang != "en"
            else f"✅ Max {_money(price)}.\nNow type your ZIP (e.g. 80903)",
            lang=lang,
        )
        return
    upsert_alert(chat_id, max_price=round(price, 3), active=1)
    send_message(
        chat_id,
        f"✅ Alerta activa en {row.get('zip')}\n"
        f"Te aviso si el más barato baja de {_money(price)}\n"
        f"(Máx. 1 aviso al día)\n\n"
        f"Toca ⛽ Precios ahora para ver el precio actual"
        if lang != "en"
        else f"✅ Alert ON for {row.get('zip')}\n"
        f"I'll notify if cheapest goes under {_money(price)}\n"
        f"(Max 1 alert/day)\n\n"
        f"Tap ⛽ Prices now for current price",
        lang=lang,
    )


def _cmd_fuel(chat_id: int, arg: str, lang: str) -> None:
    fuel = (arg or "regular").strip().lower()
    if fuel not in ("regular", "mid", "premium", "diesel"):
        send_message(
            chat_id,
            "Usa: /fuel regular|mid|premium|diesel"
            if lang != "en"
            else "Use: /fuel regular|mid|premium|diesel",
            lang=lang,
        )
        return
    upsert_alert(chat_id, fuel=fuel)
    send_message(
        chat_id,
        f"✅ Combustible: {fuel}" if lang != "en" else f"✅ Fuel: {fuel}",
        lang=lang,
    )


def _cmd_radio(chat_id: int, arg: str, lang: str) -> None:
    try:
        r = float((arg or "5").strip())
    except Exception:
        send_message(
            chat_id,
            "Ej: /radio 5" if lang != "en" else "E.g. /radius 5",
            lang=lang,
        )
        return
    r = max(1.0, min(25.0, r))
    upsert_alert(chat_id, radius_mi=r)
    send_message(
        chat_id,
        f"✅ Radio: {r:g} mi" if lang != "en" else f"✅ Radius: {r:g} mi",
        lang=lang,
    )


def _cmd_ahora(chat_id: int, lang: str) -> None:
    row = get_alert(chat_id)
    if not row or not row.get("zip"):
        send_message(chat_id, _t("need_zip_prices", lang), lang=lang)
        return

    label = row.get("label") or row.get("zip")
    send_message(chat_id, _t("searching", lang, label=label), lang=lang)
    send_typing(chat_id)

    zip_c = str(row.get("zip") or "")
    app_url = f"{APP_URL}/?zip={zip_c}" if zip_c else APP_URL

    try:
        from concurrent.futures import ThreadPoolExecutor
        from concurrent.futures import TimeoutError as FuturesTimeout

        from backend.search_core import run_search

        def _job():
            # Radio un poco mayor si el usuario tiene 5: en bot ayuda a encontrar datos
            radius = float(row.get("radius_mi") or 5)
            return run_search(
                zip=zip_c,
                fuel=str(row.get("fuel") or "regular"),
                radius_mi=radius,
                limit=12,
                track=False,
                quick=True,
            )

        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_job)
            try:
                # VPS + OSM: hasta ~22s (antes 18 y a veces cortaba con datos en camino)
                data = fut.result(timeout=22)
            except FuturesTimeout:
                send_message(
                    chat_id,
                    _t("timeout", lang, url=app_url),
                    lang=lang,
                )
                return

        # Si no hay precios con radio actual, un reintento silencioso con 10 mi
        if (
            isinstance(data, dict)
            and not (data.get("cheapest") or {}).get("price")
            and float(row.get("radius_mi") or 5) < 10
        ):
            send_typing(chat_id)
            try:
                data2 = run_search(
                    zip=zip_c,
                    fuel=str(row.get("fuel") or "regular"),
                    radius_mi=10.0,
                    limit=12,
                    track=False,
                    quick=True,
                )
                if (data2.get("cheapest") or {}).get("price") is not None:
                    data = data2
            except Exception as e:
                print(f"[telegram /ahora retry10] {type(e).__name__}: {e}")

        send_message(chat_id, _format_now(data, lang), lang=lang, disable_preview=True)
    except ValueError as e:
        send_message(chat_id, str(e), lang=lang)
    except Exception as e:
        print(f"[telegram /ahora] {type(e).__name__}: {e}")
        send_message(
            chat_id,
            _t("search_fail", lang, err=type(e).__name__, url=app_url),
            lang=lang,
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
        res = send_message(chat_id, header + body, lang=lang, disable_preview=True)
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
