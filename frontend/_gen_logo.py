"""Genera logo GasRadar nítido (icono + marca completa)."""
from __future__ import annotations

import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent


def rounded_rect_mask(size: tuple[int, int], radius: int) -> Image.Image:
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def make_icon(size: int = 1024, with_text: bool = False) -> Image.Image:
    # Fondo con glows
    bg = Image.new("RGBA", (size, size), (11, 18, 36, 255))
    for i in range(12, 0, -1):
        alpha = int(18 * i / 12)
        r = int(size * 0.55 * i / 12)
        cx, cy = int(size * 0.35), int(size * 0.32)
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).ellipse(
            [cx - r, cy - r, cx + r, cy + r], fill=(30, 80, 140, alpha)
        )
        bg = Image.alpha_composite(bg, overlay)
    for i in range(8, 0, -1):
        alpha = int(22 * i / 8)
        r = int(size * 0.4 * i / 8)
        cx, cy = int(size * 0.72), int(size * 0.78)
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).ellipse(
            [cx - r, cy - r, cx + r, cy + r], fill=(16, 100, 70, alpha)
        )
        bg = Image.alpha_composite(bg, overlay)

    radius = int(size * 0.22)
    mask = rounded_rect_mask((size, size), radius)
    out_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out_img.paste(bg, (0, 0))
    out_img.putalpha(mask)

    cx = size // 2
    if with_text:
        cy = int(size * 0.40)
        pin_h = size * 0.36
    else:
        cy = int(size * 0.50)
        pin_h = size * 0.50

    # Anillos radar
    for i, scale in enumerate([0.48, 0.36, 0.24]):
        r = pin_h * scale * 1.25
        a = 50 + i * 28
        ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        w = max(2, int(size * 0.011))
        ImageDraw.Draw(ring).ellipse(
            [cx - r, cy - r * 0.95, cx + r, cy + r * 0.95],
            outline=(56, 189, 248, a),
            width=w,
        )
        out_img = Image.alpha_composite(out_img, ring)

    # Barrido radar (cuña)
    sweep = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sweep)
    r = pin_h * 0.58
    pts = [(cx, cy)]
    for deg in range(-30, 55, 2):
        rad = math.radians(deg)
        pts.append((cx + r * math.cos(rad), cy - r * math.sin(rad)))
    sd.polygon(pts, fill=(34, 197, 94, 40))
    out_img = Image.alpha_composite(out_img, sweep)

    # Pin
    pin_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pin_layer)
    pin_w = pin_h * 0.70
    top = cy - pin_h * 0.46
    bottom = cy + pin_h * 0.50
    ew = pin_w * 0.98
    eh = pin_w * 0.98
    left = cx - ew / 2
    right = cx + ew / 2
    etop = top
    color = (14, 165, 233, 255)
    color2 = (56, 189, 248, 255)
    pd.ellipse([left, etop, right, etop + eh], fill=color2)
    pd.polygon(
        [
            (left + ew * 0.10, etop + eh * 0.58),
            (right - ew * 0.10, etop + eh * 0.58),
            (cx, bottom),
        ],
        fill=color2,
    )
    # highlight
    hl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(
        [left + ew * 0.16, etop + eh * 0.10, left + ew * 0.58, etop + eh * 0.48],
        fill=(255, 255, 255, 50),
    )
    pin_layer = Image.alpha_composite(pin_layer, hl)

    # Gota + $
    drop_cx = cx
    drop_cy = etop + eh * 0.46
    drop_r = ew * 0.20
    pd = ImageDraw.Draw(pin_layer)
    dark = (7, 16, 32, 255)
    pd.ellipse(
        [
            drop_cx - drop_r,
            drop_cy - drop_r * 0.7,
            drop_cx + drop_r,
            drop_cy + drop_r * 1.15,
        ],
        fill=dark,
    )
    pd.polygon(
        [
            (drop_cx - drop_r * 0.72, drop_cy - drop_r * 0.15),
            (drop_cx + drop_r * 0.72, drop_cy - drop_r * 0.15),
            (drop_cx, drop_cy - drop_r * 1.45),
        ],
        fill=dark,
    )

    try:
        font = ImageFont.truetype("arialbd.ttf", int(drop_r * 1.45))
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", int(drop_r * 1.45))
        except Exception:
            font = ImageFont.load_default()
    text = "$"
    # measure with temp draw
    tmp = ImageDraw.Draw(pin_layer)
    bbox = tmp.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tmp.text(
        (drop_cx - tw / 2, drop_cy - th / 2 - drop_r * 0.12),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )

    # sombra suave del pin
    alpha = pin_layer.split()[3].point(lambda a: int(a * 0.30))
    black = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    black.putalpha(alpha)
    shifted = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shifted.paste(black, (0, int(size * 0.012)))
    out_img = Image.alpha_composite(out_img, shifted)
    out_img = Image.alpha_composite(out_img, pin_layer)

    if with_text:
        draw = ImageDraw.Draw(out_img)
        try:
            f_big = ImageFont.truetype("arialbd.ttf", int(size * 0.092))
            f_small = ImageFont.truetype("arial.ttf", int(size * 0.036))
        except Exception:
            try:
                f_big = ImageFont.truetype("arial.ttf", int(size * 0.092))
                f_small = ImageFont.truetype("arial.ttf", int(size * 0.036))
            except Exception:
                f_big = ImageFont.load_default()
                f_small = f_big
        y = int(size * 0.76)
        gas, radar = "Gas", "Radar"
        bgas = draw.textbbox((0, 0), gas, font=f_big)
        brad = draw.textbbox((0, 0), radar, font=f_big)
        wgas = bgas[2] - bgas[0]
        wrad = brad[2] - brad[0]
        x0 = (size - (wgas + wrad)) / 2
        draw.text((x0, y), gas, font=f_big, fill=(238, 243, 255, 255))
        draw.text((x0 + wgas, y), radar, font=f_big, fill=(56, 189, 248, 255))
        tag = "MEJORES PRECIOS CERCA DE TI"
        bt = draw.textbbox((0, 0), tag, font=f_small)
        tw = bt[2] - bt[0]
        draw.text(
            ((size - tw) / 2, y + int(size * 0.105)),
            tag,
            font=f_small,
            fill=(154, 171, 199, 230),
        )

    return out_img


def main() -> None:
    old = OUT / "logo.png"
    if old.exists():
        bak = OUT / "logo_before_icon.png"
        if not bak.exists():
            shutil.copy2(old, bak)

    icon = make_icon(1024, with_text=False)
    icon.save(OUT / "logo.png", "PNG", optimize=True)
    icon.resize((192, 192), Image.Resampling.LANCZOS).save(OUT / "logo-192.png", "PNG")
    icon.resize((64, 64), Image.Resampling.LANCZOS).save(OUT / "favicon-64.png", "PNG")
    icon.resize((32, 32), Image.Resampling.LANCZOS).save(OUT / "favicon-32.png", "PNG")

    full = make_icon(1024, with_text=True)
    full.save(OUT / "logo-full.png", "PNG", optimize=True)

    # SVG nítido para header (vector)
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="GasRadar">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#152a4a"/>
      <stop offset="55%" stop-color="#0b1220"/>
      <stop offset="100%" stop-color="#0d1f1a"/>
    </linearGradient>
    <linearGradient id="pin" x1="30%" y1="10%" x2="70%" y2="90%">
      <stop offset="0%" stop-color="#7dd3fc"/>
      <stop offset="45%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0ea5e9"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.35"/>
    </filter>
  </defs>
  <rect width="128" height="128" rx="28" fill="url(#bg)"/>
  <!-- radar rings -->
  <circle cx="64" cy="62" r="46" fill="none" stroke="#38bdf8" stroke-opacity="0.18" stroke-width="2"/>
  <circle cx="64" cy="62" r="34" fill="none" stroke="#38bdf8" stroke-opacity="0.28" stroke-width="2"/>
  <circle cx="64" cy="62" r="22" fill="none" stroke="#38bdf8" stroke-opacity="0.40" stroke-width="2"/>
  <!-- sweep -->
  <path d="M64 62 L64 20 A42 42 0 0 1 100 48 Z" fill="#22c55e" fill-opacity="0.16"/>
  <!-- pin -->
  <g filter="url(#soft)">
    <path d="M64 28c-15.5 0-28 12.3-28 27.5 0 18.5 28 44.5 28 44.5s28-26 28-44.5C92 40.3 79.5 28 64 28z" fill="url(#pin)"/>
    <ellipse cx="56" cy="48" rx="10" ry="8" fill="#fff" fill-opacity="0.18"/>
    <!-- fuel drop -->
    <path d="M64 44c-6 8-9 12-9 16a9 9 0 0 0 18 0c0-4-3-8-9-16z" fill="#071020"/>
    <text x="64" y="64" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="700" fill="#fff">$</text>
  </g>
</svg>
"""
    (OUT / "logo.svg").write_text(svg, encoding="utf-8")
    print("OK logo.png, logo-full.png, logo.svg, favicons")


if __name__ == "__main__":
    main()
