"""Build frontend/brand-logos.js with data-URI SVGs (no network needed)."""
from __future__ import annotations

import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
brands = ROOT / "brands"
out = ROOT / "brand-logos.js"

lines = [
    "/** Auto-generated brand logo data URIs — run _embed_brand_logos.py to rebuild */",
    "const BRAND_LOGO_DATA = {",
]
for p in sorted(brands.glob("*.svg")):
    raw = " ".join(p.read_text(encoding="utf-8").split())
    uri = "data:image/svg+xml," + urllib.parse.quote(raw, safe="")
    lines.append(f'  "{p.stem}": "{uri}",')
lines.append("};")
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size} bytes, {len(list(brands.glob('*.svg')))} logos)")
