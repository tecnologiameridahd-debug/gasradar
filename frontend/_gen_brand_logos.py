"""Generate stylized brand badge SVGs for GasRadar station list."""
from pathlib import Path

out = Path(__file__).resolve().parent / "brands"
out.mkdir(exist_ok=True)


def badge(bg: str, content: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40" role="img">
  <rect width="40" height="40" rx="10" fill="{bg}"/>
  {content}
</svg>
"""


svgs: dict[str, str] = {}

svgs["generic"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40" role="img">
  <rect width="40" height="40" rx="10" fill="#2d3748"/>
  <rect x="11" y="10" width="14" height="18" rx="2" fill="#68d391"/>
  <rect x="13" y="12" width="10" height="6" rx="1" fill="#1a202c"/>
  <path d="M25 14h2a2 2 0 0 1 2 2v8a2 2 0 0 0 2 2h1" stroke="#a0aec0" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <rect x="14" y="28" width="8" height="2" rx="1" fill="#68d391"/>
</svg>"""

svgs["shell"] = badge(
    "#DD1D21",
    """
  <ellipse cx="20" cy="22" rx="11" ry="10" fill="#F7D117"/>
  <path d="M12 18c2-6 6-9 8-9s6 3 8 9c-2 1-5 2-8 2s-6-1-8-2z" fill="#DD1D21"/>
  <text x="20" y="26" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#DD1D21">S</text>
""",
)

svgs["chevron"] = badge(
    "#0066B3",
    """
  <path d="M8 28 L20 10 L32 28 L26 28 L20 18 L14 28 Z" fill="#fff"/>
  <path d="M12 28 L20 16 L28 28 L24 28 L20 22 L16 28 Z" fill="#E31837"/>
""",
)

svgs["exxon"] = badge(
    "#ED1C24",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="11" font-weight="800" fill="#fff">EX</text>
""",
)

svgs["mobil"] = badge(
    "#CC0000",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="12" font-weight="800" fill="#fff">M</text>
  <circle cx="28" cy="12" r="3" fill="#002F6C"/>
""",
)

svgs["bp"] = badge(
    "#00965E",
    """
  <circle cx="20" cy="20" r="11" fill="#A8CF45"/>
  <circle cx="20" cy="20" r="7" fill="#00965E"/>
  <text x="20" y="24" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="10" font-weight="800" fill="#fff">bp</text>
""",
)

svgs["arco"] = badge(
    "#0033A0",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#FFD100">ARCO</text>
""",
)

svgs["costco"] = badge(
    "#E31837",
    """
  <text x="20" y="24" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">COSTCO</text>
""",
)

svgs["walmart"] = badge(
    "#0071CE",
    """
  <g fill="#FFC220" transform="translate(20,20)">
    <ellipse cx="0" cy="-7" rx="2.2" ry="4.5"/>
    <ellipse cx="0" cy="-7" rx="2.2" ry="4.5" transform="rotate(60)"/>
    <ellipse cx="0" cy="-7" rx="2.2" ry="4.5" transform="rotate(120)"/>
    <ellipse cx="0" cy="-7" rx="2.2" ry="4.5" transform="rotate(180)"/>
    <ellipse cx="0" cy="-7" rx="2.2" ry="4.5" transform="rotate(240)"/>
    <ellipse cx="0" cy="-7" rx="2.2" ry="4.5" transform="rotate(300)"/>
  </g>
""",
)

svgs["sams-club"] = badge(
    "#0067A0",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="800" fill="#fff">SAM'S</text>
  <text x="20" y="28" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="700" fill="#F2A900">CLUB</text>
""",
)

svgs["circle-k"] = badge(
    "#E31837",
    """
  <circle cx="20" cy="20" r="12" fill="none" stroke="#fff" stroke-width="2"/>
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="14" font-weight="800" fill="#fff">K</text>
""",
)

svgs["7-eleven"] = badge(
    "#F57C00",
    """
  <rect x="6" y="10" width="28" height="20" rx="3" fill="#fff"/>
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="11" font-weight="800" fill="#00703C">7-11</text>
""",
)

svgs["quiktrip"] = badge(
    "#C8102E",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="12" font-weight="800" fill="#fff">QT</text>
""",
)

svgs["phillips-66"] = badge(
    "#D52B1E",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="7" font-weight="800" fill="#fff">PHILLIPS</text>
  <text x="20" y="30" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="12" font-weight="800" fill="#fff">66</text>
""",
)

svgs["conoco"] = badge(
    "#ED1C24",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">CONOCO</text>
""",
)

svgs["sinclair"] = badge(
    "#006B3F",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="16" font-weight="800" fill="#A8E010">D</text>
""",
)

svgs["valero"] = badge(
    "#0033A0",
    """
  <path d="M20 8 L30 28 L10 28 Z" fill="#F15A22"/>
  <text x="20" y="26" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">V</text>
""",
)

svgs["diamond-shamrock"] = badge(
    "#006B3F",
    """
  <path d="M20 8 L28 16 L20 32 L12 16 Z" fill="#fff"/>
  <path d="M20 12 L24 16 L20 26 L16 16 Z" fill="#006B3F"/>
""",
)

svgs["maverik"] = badge(
    "#C8102E",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="10" font-weight="800" fill="#fff">MAV</text>
""",
)

svgs["holiday"] = badge(
    "#E31837",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#fff">HOL</text>
""",
)

svgs["cenex"] = badge(
    "#FF6600",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">CENEX</text>
""",
)

svgs["texaco"] = badge(
    "#000000",
    """
  <circle cx="20" cy="20" r="12" fill="#E31837"/>
  <path d="M20 10 L22.5 17 H30 L24 21.5 L26.5 29 L20 24.5 L13.5 29 L16 21.5 L10 17 H17.5 Z" fill="#fff"/>
""",
)

svgs["kroger"] = badge(
    "#0066B3",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">KROGER</text>
""",
)

svgs["king-soopers"] = badge(
    "#E31837",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">KING</text>
  <text x="20" y="28" text-anchor="middle" font-family="Arial,sans-serif" font-size="6" font-weight="700" fill="#fff">SOOPERS</text>
""",
)

svgs["safeway"] = badge(
    "#E31837",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="7" font-weight="800" fill="#fff">SAFEWAY</text>
""",
)

svgs["murphy"] = badge(
    "#E31837",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="7" font-weight="800" fill="#fff">MURPHY</text>
  <text x="20" y="28" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="700" fill="#FFD100">USA</text>
""",
)

svgs["speedway"] = badge(
    "#FFD100",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#1a1a1a">SPEED</text>
""",
)

svgs["loves"] = badge(
    "#C8102E",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#fff">LOVE'S</text>
""",
)

svgs["pilot"] = badge(
    "#E87722",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="10" font-weight="800" fill="#fff">PILOT</text>
""",
)

svgs["flying-j"] = badge(
    "#0033A0",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">FLYING</text>
  <text x="20" y="30" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="14" font-weight="800" fill="#FFD100">J</text>
""",
)

svgs["kum-go"] = badge(
    "#E31837",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#fff">KUM</text>
  <text x="20" y="29" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#fff">&amp; GO</text>
""",
)

svgs["loaf-n-jug"] = badge(
    "#0033A0",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">LOAF</text>
  <text x="20" y="29" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="700" fill="#FFD100">'N JUG</text>
""",
)

svgs["marathon"] = badge(
    "#0066B3",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="7" font-weight="800" fill="#fff">MARATHON</text>
""",
)

svgs["caseys"] = badge(
    "#E31837",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">CASEY'S</text>
""",
)

svgs["sunoco"] = badge(
    "#0033A0",
    """
  <circle cx="20" cy="20" r="10" fill="#FFD100"/>
  <text x="20" y="24" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="6" font-weight="800" fill="#0033A0">SUNOCO</text>
""",
)

svgs["racetrac"] = badge(
    "#E31837",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="6" font-weight="800" fill="#fff">RACETRAC</text>
""",
)

svgs["wawa"] = badge(
    "#C8102E",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="10" font-weight="800" fill="#fff">WAWA</text>
""",
)

svgs["sheetz"] = badge(
    "#E31837",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="8" font-weight="800" fill="#fff">SHEETZ</text>
""",
)

svgs["citgo"] = badge(
    "#0033A0",
    """
  <path d="M8 28 L20 8 L32 28 Z" fill="#E31837"/>
  <text x="20" y="27" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="6" font-weight="800" fill="#fff">CITGO</text>
""",
)

svgs["getgo"] = badge(
    "#E31837",
    """
  <text x="20" y="25" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="9" font-weight="800" fill="#fff">GetGo</text>
""",
)

svgs["u-pump-it"] = badge(
    "#2d3748",
    """
  <text x="20" y="18" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="10" font-weight="800" fill="#68d391">U</text>
  <text x="20" y="28" text-anchor="middle" font-family="Arial,sans-serif" font-size="6" font-weight="700" fill="#fff">PUMP IT</text>
""",
)

for name, svg in svgs.items():
    (out / f"{name}.svg").write_text(svg.strip() + "\n", encoding="utf-8")

print(f"Wrote {len(svgs)} logos → {out}")
