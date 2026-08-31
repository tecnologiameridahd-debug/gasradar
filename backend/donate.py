"""Donaciones Stripe — el usuario elige el monto."""
from __future__ import annotations

import os
from typing import Any


MIN_USD = 1.0
MAX_USD = 500.0
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


def stripe_secret() -> str:
    return (
        (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
        or _secret_from_local("STRIPE_SECRET_KEY")
    )


def stripe_configured() -> bool:
    k = stripe_secret()
    return k.startswith("sk_test_") or k.startswith("sk_live_")


def stripe_mode() -> str | None:
    k = stripe_secret()
    if k.startswith("sk_live_"):
        return "live"
    if k.startswith("sk_test_"):
        return "test"
    return None


def create_checkout(amount_usd: float) -> dict[str, Any]:
    """Crea una sesión de Stripe Checkout. Devuelve {url, id}."""
    try:
        amount = float(amount_usd)
    except (TypeError, ValueError) as e:
        raise ValueError("Monto inválido") from e
    if amount < MIN_USD or amount > MAX_USD:
        raise ValueError(f"Elige un monto entre ${MIN_USD:.0f} y ${MAX_USD:.0f}")

    secret = stripe_secret()
    if not secret:
        raise RuntimeError("STRIPE_SECRET_KEY no configurada")

    import stripe

    stripe.api_key = secret
    cents = int(round(amount * 100))
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=f"{APP_URL}/?donated=1",
        cancel_url=f"{APP_URL}/?donated=0",
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": cents,
                    "product_data": {
                        "name": "Donación GasRadar",
                        "description": "Ayuda a mantener precios de gasolina en vivo",
                    },
                },
            }
        ],
        submit_type="donate",
        billing_address_collection="auto",
        metadata={"app": "gasradar", "kind": "donation"},
    )
    url = session.url or ""
    if not url:
        raise RuntimeError("Stripe no devolvió URL de pago")
    return {"url": url, "id": session.id, "amount": amount}
