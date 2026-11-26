#!/usr/bin/env python3
"""
Generates unified Dark Titanium / Smoked Liquid Glass + Electric Cyan SVGs
for NightAI707's GitHub profile README using live GitHub GraphQL telemetry.
Zero external dependencies (Python 3 stdlib only).
"""

import json
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, date, timedelta

USERNAME = os.environ.get("GITHUB_USERNAME", "NightAI707")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# 5x7 Dot-Matrix Font for Header OLED
FONT_5X7 = {
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}

# 7-Segment Digit Map (a, b, c, d, e, f, g)
SEG_MAP = {
    "0": (1, 1, 1, 1, 1, 1, 0),
    "1": (0, 1, 1, 0, 0, 0, 0),
    "2": (1, 1, 0, 1, 1, 0, 1),
    "3": (1, 1, 1, 1, 0, 0, 1),
    "4": (0, 1, 1, 0, 0, 1, 1),
    "5": (1, 0, 1, 1, 0, 1, 1),
    "6": (1, 0, 1, 1, 1, 1, 1),
    "7": (1, 1, 1, 0, 0, 0, 0),
    "8": (1, 1, 1, 1, 1, 1, 1),
    "9": (1, 1, 1, 1, 0, 1, 1),
    " ": (0, 0, 0, 0, 0, 0, 0),
}

COMMON_DEFS = """
  <defs>
    <linearGradient id="chassisGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#141923"/>
      <stop offset="50%" stop-color="#0d1118"/>
      <stop offset="100%" stop-color="#080b10"/>
    </linearGradient>
    <linearGradient id="chassisRim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="40%" stop-color="#22d3ee" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.06"/>
    </linearGradient>
    <linearGradient id="oledGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#020305"/>
      <stop offset="100%" stop-color="#06090e"/>
    </linearGradient>
    <filter id="cyanGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="softGlow" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="1.4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
"""

FONT_SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Inter, sans-serif"
FONT_MONO = "'SF Mono', 'JetBrains Mono', Consolas, monospace"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def corner_screws(w: int, h: int, pad: int = 12) -> str:
    pts = [(pad, pad), (w - pad, pad), (pad, h - pad), (w - pad, h - pad)]
    out = []
    for cx, cy in pts:
        out.append(
            f'<g transform="translate({cx},{cy})">'
            f'<circle r="4.2" fill="#07090d" stroke="#263040" stroke-width="0.9"/>'
            f'<line x1="-2.2" y1="-2.2" x2="2.2" y2="2.2" stroke="#364358" stroke-width="0.9" stroke-linecap="round"/>'
            f"</g>"
        )
    return "\n  ".join(out)


def render_7seg_display(x: int, y: int, value: int, digits: int = 3) -> str:
    """Render a recessed 7-segment LED counter box (width=82, height=34)."""
    s = str(value).rjust(digits)
    if len(s) > digits:
        s = s[-digits:]
    box_w = digits * 22 + 16
    box_h = 34
    parts = [
        f'<g transform="translate({x},{y})">',
        f'<rect width="{box_w}" height="{box_h}" rx="6" fill="#030508" stroke="#1b2330" stroke-width="1"/>',
    ]
    for idx, ch in enumerate(s):
        segs = SEG_MAP.get(ch, SEG_MAP[" "])
        ox = 10 + idx * 22
        oy = 6
        # Polygon coordinates for 7 segments in 14x22 digit cell
        polys = [
            f"{ox+2},{oy} {ox+12},{oy} {ox+10},{oy+2.2} {ox+4},{oy+2.2}",            # a (top)
            f"{ox+12.5},{oy+0.8} {ox+12.5},{oy+10.2} {ox+10.3},{oy+8.8} {ox+10.3},{oy+2.5}",  # b (top-right)
            f"{ox+12.5},{oy+11.8} {ox+12.5},{oy+21.2} {ox+10.3},{oy+19.5} {ox+10.3},{oy+13.2}", # c (bot-right)
            f"{ox+2},{oy+22} {ox+12},{oy+22} {ox+10},{oy+19.8} {ox+4},{oy+19.8}",       # d (bottom)
            f"{ox+1.5},{oy+11.8} {ox+3.7},{oy+13.2} {ox+3.7},{oy+19.5} {ox+1.5},{oy+21.2}",  # e (bot-left)
            f"{ox+1.5},{oy+0.8} {ox+3.7},{oy+2.5} {ox+3.7},{oy+8.8} {ox+1.5},{oy+10.2}",     # f (top-left)
            f"{ox+2.5},{oy+11} {ox+4},{oy+9.8} {ox+10},{oy+9.8} {ox+11.5},{oy+11} {ox+10},{oy+12.2} {ox+4},{oy+12.2}", # g (mid)
        ]
        for on, pts in zip(segs, polys):
            if on:
                parts.append(f'<polygon points="{pts}" fill="#00e5ff" filter="url(#softGlow)"/>')
            else:
                parts.append(f'<polygon points="{pts}" fill="#0f1724"/>')
    parts.append("</g>")
    return "\n  ".join(parts)


def fetch_github_data(local_json_path: str | None = None) -> dict:
    if local_json_path and os.path.exists(local_json_path):
        with open(local_json_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN environment variable and no local JSON provided.")

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
        repositories(first: 6, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
          nodes {
            name
            description
            stargazerCount
            primaryLanguage { name color }
            isPrivate
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "NightAI707-Profile-Generator",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def compute_metrics(data: dict) -> dict:
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    weeks = cal["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))

    # Monthly sums (last 7 months)
    monthly = defaultdict(int)
    for dt_str, cnt in days:
        ym = dt_str[:7]
        monthly[ym] += cnt

    sorted_months = sorted(monthly.keys())[-7:]
    month_bars = [(datetime.strptime(m, "%Y-%m").strftime("%b"), monthly[m]) for m in sorted_months]

    # Active days & busiest day
    active_days = sum(1 for _, c in days if c > 0)
    busiest_date, busiest_cnt = max(days, key=lambda x: x[1]) if days else ("", 0)
    busiest_label = (
        f"on {datetime.strptime(busiest_date, '%Y-%m-%d').strftime('%b %d')}"
        if busiest_cnt > 0
        else "no activity yet"
    )

    # Longest streak & current streak
    longest = 0
    run = 0
    for _, c in days:
        if c > 0:
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0

    current_streak = 0
    if days:
        # Check from today backwards (allow today to be 0 if yesterday was > 0)
        idx = len(days) - 1
        if days[idx][1] == 0 and idx > 0 and days[idx - 1][1] > 0:
            idx -= 1
        while idx >= 0 and days[idx][1] > 0:
            current_streak += 1
            idx -= 1

    repos = [r for r in data["data"]["user"]["repositories"]["nodes"] if not r.get("isPrivate")]

    return {
        "total": total,
        "weeks": weeks,
        "days": days,
        "month_bars": month_bars,
        "active_days": active_days,
        "total_days": len(days),
        "busiest_cnt": busiest_cnt,
        "busiest_label": busiest_label,
        "longest_streak": longest,
        "current_streak": current_streak,
        "repos": repos,
    }


def build_header_svg() -> str:
    w, h = 840, 210
    # Render 5x7 dot matrix for "NIGHT EDGE" inside OLED screen
    text = "NIGHT EDGE"
    dot_r = 4.3
    pitch = 11.5
    oled_x, oled_y, oled_w, oled_h = 28, 22, 784, 112

    # Total columns: 10 chars * 5 + 9 gaps * 2 = 68 cols; center horizontally
    total_cols = len(text) * 5 + (len(text) - 1) * 2
    grid_w = total_cols * pitch
    start_x = oled_x + (oled_w - grid_w) / 2 + pitch / 2
    start_y = oled_y + (oled_h - 7 * pitch) / 2 + pitch / 2

    dots = []
    # Background unlit matrix grid across entire OLED
    bg_cols = 66
    bg_rows = 7
    bg_sx = oled_x + (oled_w - bg_cols * pitch) / 2 + pitch / 2
    for r in range(bg_rows):
        for c in range(bg_cols):
            cx = bg_sx + c * pitch
            cy = start_y + r * pitch
            dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#0f1724"/>')

    # Lit cyan matrix text
    col_offset = 0
    for ch in text:
        glyph = FONT_5X7[ch]
        for r in range(7):
            for c in range(5):
                if glyph[r][c] == "1":
                    cx = start_x + (col_offset + c) * pitch
                    cy = start_y + r * pitch
                    dots.append(
                        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#00e5ff" filter="url(#cyanGlow)"/>'
                    )
        col_offset += 7

    # Speaker grille dots on bottom right
    grille = []
    for gr in range(3):
        for gc in range(14):
            gx = 636 + gc * 9.5
            gy = 160 + gr * 8.5
            grille.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="2.1" fill="#1e293b"/>')

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="url(#chassisGrad)" stroke="url(#chassisRim)" stroke-width="1.2"/>
  <line x1="20" y1="1.8" x2="{w-20}" y2="1.8" stroke="#ffffff" stroke-opacity="0.22" stroke-width="0.9"/>
  {corner_screws(w, h)}

  <!-- Recessed Smoked-Glass OLED Display -->
  <rect x="{oled_x}" y="{oled_y}" width="{oled_w}" height="{oled_h}" rx="12" fill="url(#oledGrad)" stroke="#1a2433" stroke-width="1.2"/>
  <line x1="{oled_x+12}" y1="{oled_y+1}" x2="{oled_x+oled_w-12}" y2="{oled_y+1}" stroke="#22d3ee" stroke-opacity="0.16" stroke-width="1"/>
  {''.join(dots)}

  <!-- Bottom Nameplate Info -->
  <text x="32" y="164" font-family="{FONT_SANS}" font-size="16" font-weight="600" fill="#f1f5f9" letter-spacing="-0.2">I build AI products, creative tools, and intelligent systems.</text>
  <text x="32" y="186" font-family="{FONT_MONO}" font-size="12" fill="#7d8590" letter-spacing="0.4">IIT Patna  /  Founder @ Elera AI  /  Python, TypeScript, Lua</text>

  <!-- Speaker Grille + Pulsing Cyan Status LED -->
  {''.join(grille)}
  <circle cx="792" cy="168.5" r="6" fill="#05080d" stroke="#1e293b" stroke-width="1"/>
  <circle cx="792" cy="168.5" r="3.8" fill="#00e5ff" filter="url(#cyanGlow)">
    <animate attributeName="opacity" values="1;0.35;1" dur="2.6s" repeatCount="indefinite"/>
  </circle>
</svg>
"""


def build_action_tile(title: str, subtitle: str, accent: str, glow: bool = False) -> str:
    w, h = 272, 74
    fill_top = "#082f3a" if glow else "#141a24"
    fill_bot = "#04161c" if glow else "#0a0e14"
    rim = "#22d3ee" if glow else "#ffffff"
    rim_op = "0.42" if glow else "0.18"
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="tg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{fill_top}"/>
      <stop offset="100%" stop-color="{fill_bot}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="url(#tg)" stroke="{rim}" stroke-opacity="{rim_op}" stroke-width="1.1"/>
  <line x1="16" y1="2" x2="{w-16}" y2="2" stroke="#ffffff" stroke-opacity="0.28" stroke-width="0.9"/>
  <rect x="1" y="14" width="3" height="{h-28}" rx="1.5" fill="{accent}"/>
  <text x="20" y="33" font-family="{FONT_SANS}" font-size="16" font-weight="700" fill="#f8fafc">{esc(title)}</text>
  <text x="20" y="53" font-family="{FONT_MONO}" font-size="11.5" fill="#94a3b8">{esc(subtitle)}</text>
  <path d="M{w-30} 25 H{w-20} V35 M{w-20} 25 L{w-31} 36" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def build_telemetry_svg(m: dict) -> str:
    w, h = 840, 236
    # Left OLED: Contributions per month VU-meter bars
    oled_x, oled_y, oled_w, oled_h = 28, 46, 496, 166
    bars = m["month_bars"]
    max_val = max([v for _, v in bars] + [1])
    num_segs = 11
    seg_h = 8.5
    seg_gap = 2.6
    bar_w = 42
    bar_gap = 20
    start_bx = oled_x + (oled_w - (len(bars) * bar_w + (len(bars) - 1) * bar_gap)) / 2
    base_y = oled_y + 136

    vu_elems = []
    for idx, (label, val) in enumerate(bars):
        bx = start_bx + idx * (bar_w + bar_gap)
        lit_segs = 0 if val == 0 else max(1, round((val / max_val) * num_segs))
        for s in range(num_segs):
            sy = base_y - (s + 1) * (seg_h + seg_gap)
            if s < lit_segs:
                color = "#a5f3fc" if s >= num_segs - 2 else "#00e5ff"
                vu_elems.append(
                    f'<rect x="{bx:.1f}" y="{sy:.1f}" width="{bar_w}" height="{seg_h}" rx="2" fill="{color}" filter="url(#softGlow)"/>'
                )
            else:
                vu_elems.append(
                    f'<rect x="{bx:.1f}" y="{sy:.1f}" width="{bar_w}" height="{seg_h}" rx="2" fill="#0f1724"/>'
                )
        # Value label above top lit or bottom
        if val > 0:
            top_y = base_y - lit_segs * (seg_h + seg_gap) - 5
            vu_elems.append(
                f'<text x="{bx + bar_w/2:.1f}" y="{top_y:.1f}" text-anchor="middle" font-family="{FONT_MONO}" font-size="10.5" fill="#94a3b8">{val}</text>'
            )
        vu_elems.append(
            f'<text x="{bx + bar_w/2:.1f}" y="{oled_y + 154}" text-anchor="middle" font-family="{FONT_MONO}" font-size="10.5" fill="#64748b">{label}</text>'
        )

    # Right 3 7-Segment Counters
    rx = 548
    counters = [
        ("Current streak", f"longest {m['longest_streak']} days", m["current_streak"], 58),
        ("Active days", f"of the last {m['total_days']}", m["active_days"], 114),
        ("Busiest day", m["busiest_label"], m["busiest_cnt"], 170),
    ]
    right_elems = []
    for title, sub, val, cy in counters:
        right_elems.append(render_7seg_display(rx, cy, val, digits=3))
        right_elems.append(
            f'<text x="{rx + 96}" y="{cy + 14}" font-family="{FONT_SANS}" font-size="13.5" font-weight="600" fill="#e2e8f0">{esc(title)}</text>'
        )
        right_elems.append(
            f'<text x="{rx + 96}" y="{cy + 30}" font-family="{FONT_MONO}" font-size="11" fill="#64748b">{esc(sub)}</text>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="url(#chassisGrad)" stroke="url(#chassisRim)" stroke-width="1.2"/>
  <line x1="20" y1="1.8" x2="{w-20}" y2="1.8" stroke="#ffffff" stroke-opacity="0.22" stroke-width="0.9"/>
  {corner_screws(w, h)}

  <text x="30" y="32" font-family="{FONT_SANS}" font-size="13.5" font-weight="600" fill="#cbd5e1">Contributions per month</text>
  <text x="810" y="32" text-anchor="end" font-family="{FONT_MONO}" font-size="11" fill="#475569">TELEMETRY // LIVE</text>

  <rect x="{oled_x}" y="{oled_y}" width="{oled_w}" height="{oled_h}" rx="12" fill="url(#oledGrad)" stroke="#1a2433" stroke-width="1.2"/>
  {''.join(vu_elems)}
  {''.join(right_elems)}
</svg>
"""


def build_projects_svg(m: dict) -> str:
    # Curated featured strips: Elera AI + top public repos
    items = [
        {
            "name": "elera-ai",
            "desc": "AI-powered creative editing platform built around generative workflows and fast visual tooling.",
            "lang": "Python",
            "lang_color": "#00e5ff",
            "accent": "#00e5ff",
            "stars": 0,
            "badge": "FLAGSHIP",
        }
    ]
    accents = ["#38bdf8", "#818cf8", "#22d3ee"]
    for idx, r in enumerate(m["repos"][:2]):
        lang = (r.get("primaryLanguage") or {}).get("name") or "Markdown"
        lcol = (r.get("primaryLanguage") or {}).get("color") or "#7dd3fc"
        desc = r.get("description") or "Personal developer profile and automated telemetry system."
        if len(desc) > 84:
            desc = desc[:81] + "..."
        items.append(
            {
                "name": r["name"],
                "desc": desc,
                "lang": lang,
                "lang_color": lcol,
                "accent": accents[idx % len(accents)],
                "stars": r.get("stargazerCount", 0),
                "badge": "",
            }
        )

    w = 840
    row_h = 74
    gap = 10
    h = len(items) * row_h + (len(items) - 1) * gap
    rows = []
    for i, it in enumerate(items):
        ry = i * (row_h + gap)
        seg = render_7seg_display(742, ry + 20, it["stars"], digits=2)
        rows.append(
            f'<g>'
            f'<rect x="1" y="{ry+1}" width="{w-2}" height="{row_h-2}" rx="14" fill="url(#chassisGrad)" stroke="url(#chassisRim)" stroke-width="1.1"/>'
            f'<line x1="18" y1="{ry+2}" x2="{w-18}" y2="{ry+2}" stroke="#ffffff" stroke-opacity="0.18" stroke-width="0.8"/>'
            f'<rect x="1" y="{ry+10}" width="4" height="{row_h-20}" rx="2" fill="{it["accent"]}"/>'
            f'<text x="26" y="{ry+30}" font-family="{FONT_SANS}" font-size="16" font-weight="700" fill="#f8fafc">{esc(it["name"])}</text>'
            f'<text x="26" y="{ry+51}" font-family="{FONT_MONO}" font-size="11.5" fill="#7d8590">{esc(it["desc"])}</text>'
            f'<circle cx="622" cy="{ry+37}" r="4.5" fill="{it["lang_color"]}"/>'
            f'<text x="634" y="{ry+41}" font-family="{FONT_SANS}" font-size="12.5" fill="#cbd5e1">{esc(it["lang"])}</text>'
            f'<polygon points="724,{ry+31} 726,{ry+35} 730,{ry+35.5} 727,{ry+38.5} 727.8,{ry+42.5} 724,{ry+40.5} 720.2,{ry+42.5} 721,{ry+38.5} 718,{ry+35.5} 722,{ry+35}" fill="#64748b"/>'
            f'{seg}'
            f'</g>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  {''.join(rows)}
</svg>
"""


def build_heatmap_svg(m: dict) -> str:
    w, h = 840, 178
    oled_x, oled_y, oled_w, oled_h = 28, 46, 784, 110
    weeks = m["weeks"][-52:]
    dot_r = 4.2
    step_x = 14.2
    step_y = 11.8
    start_x = oled_x + (oled_w - len(weeks) * step_x) / 2 + step_x / 2
    start_y = oled_y + 30

    dots = []
    month_labels = []
    seen_months = set()
    for wi, wk in enumerate(weeks):
        cx = start_x + wi * step_x
        days = wk["contributionDays"]
        if days:
            dt = datetime.strptime(days[0]["date"], "%Y-%m-%d")
            ym = dt.strftime("%Y-%m")
            if ym not in seen_months and wi < len(weeks) - 2:
                seen_months.add(ym)
                month_labels.append(
                    f'<text x="{cx:.1f}" y="{oled_y + 18}" font-family="{FONT_MONO}" font-size="10" fill="#64748b">{dt.strftime("%b")}</text>'
                )
        for di, d in enumerate(days):
            cy = start_y + di * step_y
            cnt = d["contributionCount"]
            if cnt == 0:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#0f1724"/>')
            elif cnt <= 2:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#0e7490"/>')
            elif cnt <= 5:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#06b6d4"/>')
            elif cnt <= 9:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#22d3ee" filter="url(#softGlow)"/>')
            else:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_r}" fill="#a5f3fc" filter="url(#cyanGlow)"/>')

    # Legend pill top-right
    legend_colors = ["#0f1724", "#0e7490", "#06b6d4", "#22d3ee", "#a5f3fc"]
    legend_dots = "".join(
        f'<circle cx="{726 + i * 11}" cy="27" r="3.6" fill="{col}"/>'
        for i, col in enumerate(legend_colors)
    )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="url(#chassisGrad)" stroke="url(#chassisRim)" stroke-width="1.2"/>
  <line x1="20" y1="1.8" x2="{w-20}" y2="1.8" stroke="#ffffff" stroke-opacity="0.22" stroke-width="0.9"/>
  {corner_screws(w, h)}

  <text x="30" y="31" font-family="{FONT_SANS}" font-size="13.5" font-weight="600" fill="#cbd5e1">{m['total']} contributions in the last year</text>
  <text x="708" y="30" text-anchor="end" font-family="{FONT_MONO}" font-size="10.5" fill="#64748b">Less</text>
  <rect x="716" y="18" width="64" height="18" rx="9" fill="#040608" stroke="#1a2433" stroke-width="1"/>
  {legend_dots}
  <text x="788" y="30" font-family="{FONT_MONO}" font-size="10.5" fill="#64748b">More</text>

  <rect x="{oled_x}" y="{oled_y}" width="{oled_w}" height="{oled_h}" rx="12" fill="url(#oledGrad)" stroke="#1a2433" stroke-width="1.2"/>
  {''.join(month_labels)}
  {''.join(dots)}
</svg>
"""


def build_stack_svg() -> str:
    w, h = 840, 118
    oled_x, oled_y, oled_w, oled_h = 28, 42, 784, 56
    items = [
        ("Python", "#00e5ff"),
        ("TypeScript", "#38bdf8"),
        ("JavaScript", "#7dd3fc"),
        ("Lua", "#a5f3fc"),
        ("PyTorch", "#22d3ee"),
        ("TensorFlow", "#06b6d4"),
        ("React", "#00e5ff"),
        ("Next.js", "#e2e8f0"),
        ("Docker", "#38bdf8"),
        ("Git", "#7dd3fc"),
        ("Linux", "#a5f3fc"),
    ]
    # Center pills inside OLED
    pill_w = 64
    gap = 6
    total_w = len(items) * pill_w + (len(items) - 1) * gap
    sx = oled_x + (oled_w - total_w) / 2
    pills = []
    for i, (name, col) in enumerate(items):
        px = sx + i * (pill_w + gap)
        pills.append(
            f'<rect x="{px:.1f}" y="{oled_y + 13}" width="{pill_w}" height="30" rx="8" fill="#0d131d" stroke="#1e293b" stroke-width="1"/>'
            f'<circle cx="{px + 10:.1f}" cy="{oled_y + 28}" r="2.6" fill="{col}"/>'
            f'<text x="{px + 17:.1f}" y="{oled_y + 31.5}" font-family="{FONT_MONO}" font-size="9" fill="#cbd5e1">{esc(name[:7])}</text>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="url(#chassisGrad)" stroke="url(#chassisRim)" stroke-width="1.2"/>
  <line x1="20" y1="1.8" x2="{w-20}" y2="1.8" stroke="#ffffff" stroke-opacity="0.22" stroke-width="0.9"/>
  {corner_screws(w, h)}

  <text x="30" y="29" font-family="{FONT_SANS}" font-size="13.5" font-weight="600" fill="#cbd5e1">Core Stack</text>
  <text x="810" y="29" text-anchor="end" font-family="{FONT_MONO}" font-size="11" fill="#475569">AI  /  SYSTEMS  /  WEB</text>

  <rect x="{oled_x}" y="{oled_y}" width="{oled_w}" height="{oled_h}" rx="10" fill="url(#oledGrad)" stroke="#1a2433" stroke-width="1.2"/>
  {''.join(pills)}
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    local_json = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_github_data(local_json)
    metrics = compute_metrics(data)

    outputs = {
        "header-unit.svg": build_header_svg(),
        "tile-elera.svg": build_action_tile("Elera AI", "creative-ai platform", "#00e5ff", glow=True),
        "tile-linkedin.svg": build_action_tile("LinkedIn", "Night Edge", "#38bdf8", glow=False),
        "tile-x.svg": build_action_tile("X", "@NightEdge707", "#94a3b8", glow=False),
        "telemetry-unit.svg": build_telemetry_svg(metrics),
        "stack-unit.svg": build_stack_svg(),
        "projects-unit.svg": build_projects_svg(metrics),
        "heatmap-unit.svg": build_heatmap_svg(metrics),
    }

    for fname, svg in outputs.items():
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Generated {fname} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
