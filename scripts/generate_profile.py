#!/usr/bin/env python3
"""
Generates Apple-inspired Liquid Glass, Dynamic Island, WatchOS StandBy,
and App Store Mesh-Squircle SVG widgets for NightAI707 with smooth SMIL/CSS
animations and live GitHub GraphQL telemetry.
Zero external dependencies (Python 3 stdlib only).
"""

import base64
import json
import math
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime

USERNAME = os.environ.get("GITHUB_USERNAME", "NightAI707")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

FONT_SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif"
FONT_MONO = "'SF Mono', 'JetBrains Mono', Menlo, monospace"

COMMON_DEFS = """
  <defs>
    <linearGradient id="cardDark" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#16161a"/>
      <stop offset="100%" stop-color="#0b0b0d"/>
    </linearGradient>
    <linearGradient id="cardRim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.26"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.16"/>
    </linearGradient>
    <linearGradient id="tideArea" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0a84ff" stop-opacity="0.48"/>
      <stop offset="100%" stop-color="#0a84ff" stop-opacity="0.0"/>
    </linearGradient>
    <linearGradient id="sheenSweep" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
"""

PRO_DIGITS = {
    "0": "M22,10 L118,10 L130,22 L130,78 L118,90 L22,90 L10,78 L10,22 Z M36,30 L36,70 L104,70 L104,30 Z",
    "1": "M36,10 L84,10 L84,90 L58,90 L58,30 L36,30 Z",
    "2": "M12,10 L118,10 L130,22 L130,48 L118,60 L38,60 L38,70 L130,70 L130,90 L12,90 L12,50 L24,38 L104,38 L104,30 L12,30 Z",
    "3": "M12,10 L118,10 L130,22 L130,42 L118,50 L130,58 L130,78 L118,90 L12,90 L12,70 L102,70 L102,59 L40,59 L40,41 L102,41 L102,30 L12,30 Z",
    "4": "M10,10 L38,10 L38,44 L98,44 L98,10 L126,10 L126,90 L98,90 L98,64 L22,64 L10,52 Z",
    "5": "M12,10 L128,10 L128,30 L38,30 L38,40 L118,40 L130,52 L130,78 L118,90 L12,90 L12,70 L102,70 L102,60 L24,60 L12,48 Z",
    "6": "M22,10 L126,10 L126,30 L38,30 L38,40 L118,40 L130,52 L130,78 L118,90 L22,90 L10,78 L10,22 Z M38,59 L38,71 L102,71 L102,59 Z",
    "7": "M12,10 L130,10 L130,30 L84,90 L54,90 L98,30 L12,30 Z",
    "8": "M22,10 L118,10 L130,22 L130,42 L118,50 L130,58 L130,78 L118,90 L22,90 L10,78 L10,58 L22,50 L10,42 L10,22 Z M38,29 L38,41 L102,41 L102,29 Z M38,59 L38,71 L102,71 L102,59 Z",
    "9": "M22,10 L118,10 L130,22 L130,78 L118,90 L14,90 L14,70 L102,70 L102,60 L22,60 L10,48 L10,22 Z M38,29 L38,41 L102,41 L102,29 Z",
}


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


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
    weekly_totals = []
    for w in weeks:
        w_sum = 0
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
            w_sum += d["contributionCount"]
        weekly_totals.append((w["contributionDays"][0]["date"] if w["contributionDays"] else "", w_sum))

    monthly = defaultdict(int)
    for dt_str, cnt in days:
        monthly[dt_str[:7]] += cnt
    sorted_months = sorted(monthly.keys())[-8:]
    month_bars = [(datetime.strptime(m, "%Y-%m").strftime("%b").upper(), monthly[m]) for m in sorted_months]

    active_days = sum(1 for _, c in days if c > 0)
    longest = 0
    run = 0
    for _, c in days:
        if c > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    current_streak = 0
    if days:
        idx = len(days) - 1
        if days[idx][1] == 0 and idx > 0 and days[idx - 1][1] > 0:
            idx -= 1
        while idx >= 0 and days[idx][1] > 0:
            current_streak += 1
            idx -= 1

    return {
        "total": total,
        "month_bars": month_bars,
        "weekly_totals": weekly_totals[-20:],
        "active_days": active_days,
        "total_days": len(days),
        "longest_streak": longest,
        "current_streak": current_streak,
    }


def build_dynamic_island(m: dict) -> str:
    w, h = 840, 72
    pw, ph = 460, 56
    px, py = (w - pw) / 2, (h - ph) / 2
    r = ph / 2

    logo_path = os.path.join(OUT_DIR, "elera-logo.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as lf:
            logo_b64 = base64.b64encode(lf.read()).decode("ascii")

    wave_bars = [
        (8, "#ff2d55"), (16, "#ff5e3a"), (24, "#ff9f0a"),
        (14, "#30d158"), (22, "#0a84ff"), (16, "#bf5af2"), (10, "#ff2d55"),
    ]
    bars_svg = []
    wx0 = px + 188
    for i, (bh, col) in enumerate(wave_bars):
        bx = wx0 + i * 7.5
        by = h / 2 - bh / 2
        bars_svg.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="3.6" height="{bh}" rx="1.8" fill="{col}">'
            f'<animate attributeName="height" values="{bh};{max(6, bh-10)};{bh}" dur="{1.05 + i*0.14:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{by:.1f};{h/2 - max(6, bh-10)/2:.1f};{by:.1f}" dur="{1.05 + i*0.14:.2f}s" repeatCount="indefinite"/>'
            f'</rect>'
        )

    streak_frac = min(1.0, max(0.18, m["current_streak"] / 14.0))
    ring_r = 12
    circ = 2 * math.pi * ring_r
    dash = circ * streak_frac

    logo_elem = (
        f'<image href="data:image/png;base64,{logo_b64}" x="{px + 42:.1f}" y="{h/2 - 12:.1f}" width="60" height="24"/>'
        if logo_b64
        else f'<text x="{px + 42:.1f}" y="{h/2 + 5:.1f}" font-family="{FONT_SANS}" font-size="14" font-weight="600" fill="#ffffff">Elera</text>'
    )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <defs>
    <clipPath id="diClipV5">
      <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{r}"/>
    </clipPath>
  </defs>
  <g clip-path="url(#diClipV5)">
    <rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#000000"/>
    <rect x="{px - 140}" y="{py}" width="120" height="{ph}" fill="url(#sheenSweep)" transform="skewX(-20)">
      <animate attributeName="x" values="{px - 160};{px + pw + 80}" dur="5.5s" repeatCount="indefinite"/>
    </rect>
  </g>
  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{r}" fill="none" stroke="#1c1c1e" stroke-width="1.5"/>

  <circle cx="{px + 26}" cy="{h/2}" r="4.2" fill="#30d158" filter="url(#softGlow)">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="r" values="4.2;5.0;4.2" dur="2s" repeatCount="indefinite"/>
  </circle>
  {logo_elem}
  <text x="{px + 110}" y="{h/2 + 4:.1f}" font-family="{FONT_MONO}" font-size="10.5" fill="#636366">dev</text>

  {''.join(bars_svg)}

  <text x="{px + pw - 46}" y="{h/2 + 4.5:.1f}" text-anchor="end" font-family="{FONT_MONO}" font-size="11.5" font-weight="500" fill="#d1d1d6">{m['total']} commits</text>
  <circle cx="{px + pw - 24}" cy="{h/2}" r="{ring_r}" stroke="#1c1c1e" stroke-width="3.4" fill="none"/>
  <circle cx="{px + pw - 24}" cy="{h/2}" r="{ring_r}" stroke="#0a84ff" stroke-width="3.4" stroke-linecap="round" fill="none"
          stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 {px + pw - 24} {h/2})">
    <animateTransform attributeName="transform" type="rotate" from="-90 {px + pw - 24} {h/2}" to="270 {px + pw - 24} {h/2}" dur="9s" repeatCount="indefinite"/>
  </circle>
</svg>
"""


def build_bio_widget() -> str:
    w, h = 412, 224
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <defs>
    <clipPath id="bioClip"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26"/></clipPath>
  </defs>
  <g clip-path="url(#bioClip)">
    <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="url(#cardDark)"/>
    <rect x="-150" y="0" width="140" height="{h}" fill="url(#sheenSweep)" transform="skewX(-18)">
      <animate attributeName="x" values="-180;{w + 120}" dur="7.5s" repeatCount="indefinite"/>
    </rect>
  </g>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="none" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="28" y1="2" x2="{w-28}" y2="2" stroke="#ffffff" stroke-opacity="0.28" stroke-width="0.9"/>

  <text x="26" y="36" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">ABOUT</text>
  <text x="26" y="68" font-family="{FONT_SANS}" font-size="18" font-weight="600" fill="#f5f5f7">Night Edge</text>
  <text x="26" y="96" font-family="{FONT_SANS}" font-size="13.5" fill="#d1d1d6">Student at IIT Patna and founder of Elera AI.</text>
  <text x="26" y="116" font-family="{FONT_SANS}" font-size="13.5" fill="#d1d1d6">Building AI-powered creative tools and</text>
  <text x="26" y="136" font-family="{FONT_SANS}" font-size="13.5" fill="#d1d1d6">intelligent systems across Python, TS, and Lua.</text>

  <g transform="translate(26, 164)">
    <rect width="102" height="28" rx="14" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.18" stroke-width="0.9">
      <animate attributeName="fill-opacity" values="0.07;0.14;0.07" dur="4s" repeatCount="indefinite"/>
    </rect>
    <text x="51" y="18" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#f5f5f7">Gen-AI</text>

    <rect x="110" width="114" height="28" rx="14" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.18" stroke-width="0.9">
      <animate attributeName="fill-opacity" values="0.07;0.14;0.07" dur="4s" begin="1.2s" repeatCount="indefinite"/>
    </rect>
    <text x="167" y="18" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#f5f5f7">Open Source</text>

    <rect x="232" width="122" height="28" rx="14" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.18" stroke-width="0.9">
      <animate attributeName="fill-opacity" values="0.07;0.14;0.07" dur="4s" begin="2.4s" repeatCount="indefinite"/>
    </rect>
    <text x="293" y="18" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#f5f5f7">Cybersecurity</text>
  </g>
</svg>
"""


def build_counter_widget(m: dict) -> str:
    # Animated drifting Apple Mesh Gradient + Korataki Extra Bold glowing numeral
    w, h = 204, 224
    num_str = str(m["total"])
    n = len(num_str)
    scale = 0.96 if n == 1 else (0.58 if n == 2 else 0.40)
    digit_w = 140 * scale
    gap = 6 * scale
    total_w = n * digit_w + (n - 1) * gap
    start_x = (w - total_w) / 2
    start_y = (h - 100 * scale) / 2 + 4

    digit_paths = []
    for i, ch in enumerate(num_str):
        d = PRO_DIGITS.get(ch, PRO_DIGITS["0"])
        dx = start_x + i * (digit_w + gap)
        digit_paths.append(
            f'<g transform="translate({dx:.1f},{start_y:.1f}) scale({scale:.3f})">'
            f'<path d="{d}" fill="#ffffff" fill-opacity="0.32" fill-rule="evenodd" filter="url(#softGlow)">'
            f'<animate attributeName="fill-opacity" values="0.22;0.48;0.22" dur="3.5s" repeatCount="indefinite"/>'
            f'</path>'
            f'<path d="{d}" fill="#ffffff" fill-opacity="0.97" fill-rule="evenodd"/>'
            f'</g>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <defs>
    <clipPath id="meshClipV2">
      <rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="25"/>
    </clipPath>
    <linearGradient id="meshBaseV2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff6b4a"/>
      <stop offset="50%" stop-color="#ff9a44"/>
      <stop offset="100%" stop-color="#f472b6"/>
    </linearGradient>
    <radialGradient id="blobOrangeV2" cx="20%" cy="22%" r="62%">
      <stop offset="0%" stop-color="#ff5e3a" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#ff5e3a" stop-opacity="0"/>
      <animate attributeName="cx" values="18%;36%;18%" dur="8s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="20%;35%;20%" dur="7s" repeatCount="indefinite"/>
    </radialGradient>
    <radialGradient id="blobBlueV2" cx="46%" cy="82%" r="54%">
      <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.95"/>
      <stop offset="55%" stop-color="#93c5fd" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#60a5fa" stop-opacity="0"/>
      <animate attributeName="cx" values="42%;64%;42%" dur="9s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="84%;68%;84%" dur="8s" repeatCount="indefinite"/>
    </radialGradient>
    <radialGradient id="blobPinkV2" cx="85%" cy="85%" r="55%">
      <stop offset="0%" stop-color="#f472b6" stop-opacity="0.92"/>
      <stop offset="100%" stop-color="#f472b6" stop-opacity="0"/>
      <animate attributeName="cx" values="88%;70%;88%" dur="10s" repeatCount="indefinite"/>
    </radialGradient>
    <linearGradient id="meshRimV2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.62"/>
      <stop offset="40%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.75"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#meshClipV2)">
    <rect width="{w}" height="{h}" fill="url(#meshBaseV2)"/>
    <rect width="{w}" height="{h}" fill="url(#blobOrangeV2)"/>
    <rect width="{w}" height="{h}" fill="url(#blobBlueV2)"/>
    <rect width="{w}" height="{h}" fill="url(#blobPinkV2)"/>
    <rect x="-120" y="0" width="90" height="{h}" fill="url(#sheenSweep)" transform="skewX(-18)">
      <animate attributeName="x" values="-140;{w + 100}" dur="6s" repeatCount="indefinite"/>
    </rect>
  </g>
  <rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="25" fill="none" stroke="url(#meshRimV2)" stroke-width="1.4"/>
  <text x="22" y="32" font-family="{FONT_SANS}" font-size="11.5" font-weight="600" letter-spacing="0.8" fill="#ffffff" fill-opacity="0.92">COMMITS</text>
  {''.join(digit_paths)}
  <text x="22" y="200" font-family="{FONT_SANS}" font-size="12" font-weight="500" fill="#ffffff" fill-opacity="0.90">Last 365 days</text>
</svg>
"""


def build_rings_widget(m: dict) -> str:
    w, h = 204, 224
    cx, cy = 102, 114
    rings = [
        (56, "#fa114f", min(1.0, max(0.18, m["total"] / 100.0)), "0s"),
        (42, "#92e82a", min(1.0, max(0.18, m["active_days"] / 60.0)), "0.2s"),
        (28, "#00d4ff", min(1.0, max(0.18, m["longest_streak"] / 30.0)), "0.4s"),
    ]
    ring_svg = []
    for r, col, frac, delay in rings:
        circ = 2 * math.pi * r
        dash = circ * frac
        ring_svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{col}" stroke-opacity="0.16" stroke-width="10" fill="none"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{col}" stroke-width="10" stroke-linecap="round" fill="none" '
            f'stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})">'
            f'<animate attributeName="stroke-dasharray" from="0 {circ:.1f}" to="{dash:.1f} {circ:.1f}" dur="1.4s" begin="{delay}" fill="freeze"/>'
            f'<animate attributeName="stroke-opacity" values="0.85;1;0.85" dur="3.5s" begin="{delay}" repeatCount="indefinite"/>'
            f'</circle>'
        )
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="url(#cardDark)" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="26" y1="2" x2="{w-26}" y2="2" stroke="#ffffff" stroke-opacity="0.26" stroke-width="0.9"/>
  <text x="22" y="34" font-family="{FONT_SANS}" font-size="11.5" font-weight="600" letter-spacing="0.8" fill="#8e8e93">ACTIVITY</text>
  {''.join(ring_svg)}
  <text x="34" y="198" font-family="{FONT_MONO}" font-size="10.5" fill="#fa114f">{m['total']}c</text>
  <text x="102" y="198" text-anchor="middle" font-family="{FONT_MONO}" font-size="10.5" fill="#92e82a">{m['active_days']}d</text>
  <text x="170" y="198" text-anchor="end" font-family="{FONT_MONO}" font-size="10.5" fill="#00d4ff">{m['longest_streak']}s</text>
</svg>
"""


def build_telemetry_row(m: dict) -> str:
    w, h = 840, 184
    bars = m["month_bars"]
    max_v = max([v for _, v in bars] + [1])
    bar_colors = ["#30d158", "#ffd60a", "#ff9f0a", "#ff6b35", "#ff2d55", "#bf5af2", "#5e5ce6", "#0a84ff"]

    left_bars = []
    bx0 = 32
    for i, (lbl, val) in enumerate(bars):
        bx = bx0 + i * 44
        bh = 10 if val == 0 else max(14, round((val / max_v) * 78))
        by = 136 - bh
        col = bar_colors[i % len(bar_colors)]
        pulse = (
            f'<animate attributeName="height" values="{bh};{max(12, bh-8)};{bh}" dur="2.6s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{by};{136 - max(12, bh-8)};{by}" dur="2.6s" repeatCount="indefinite"/>'
            if val > 0 else ""
        )
        left_bars.append(
            f'<rect x="{bx}" y="58" width="22" height="78" rx="11" fill="#1c1c1e"/>'
            f'<rect x="{bx}" y="{by}" width="22" height="{bh}" rx="11" fill="{col}" fill-opacity="{0.25 if val == 0 else 0.95}">{pulse}</rect>'
            f'<text x="{bx+11}" y="156" text-anchor="middle" font-family="{FONT_MONO}" font-size="10" fill="#8e8e93">{lbl}</text>'
        )

    weekly = m["weekly_totals"]
    max_w = max([v for _, v in weekly] + [1])
    gx, gy, gw, gh = 446, 58, 362, 78
    pts = []
    for i, (_, v) in enumerate(weekly):
        x = gx + (i / max(1, len(weekly) - 1)) * gw
        y = gy + gh - (v / max_w) * (gh - 8)
        pts.append((x, y, v))

    line_d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0, y0, _ = pts[i - 1]
        x1, y1, _ = pts[i]
        mx = (x0 + x1) / 2
        line_d += f" C {mx:.1f} {y0:.1f}, {mx:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}"
    area_d = line_d + f" L {pts[-1][0]:.1f} {gy + gh} L {pts[0][0]:.1f} {gy + gh} Z"

    peak = max(pts, key=lambda p: p[2])
    peak_dot = (
        f'<circle cx="{peak[0]:.1f}" cy="{peak[1]:.1f}" r="4.5" fill="#0a84ff" filter="url(#softGlow)">'
        f'<animate attributeName="r" values="4;6.5;4" dur="2.2s" repeatCount="indefinite"/>'
        f'</circle>'
        if peak[2] > 0 else ""
    )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="410" height="{h-2}" rx="26" fill="url(#cardDark)" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="28" y1="2" x2="384" y2="2" stroke="#ffffff" stroke-opacity="0.26" stroke-width="0.9"/>
  <text x="26" y="34" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">MONTHLY OUTPUT</text>
  {''.join(left_bars)}

  <rect x="427" y="1" width="412" height="{h-2}" rx="26" fill="url(#cardDark)" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="454" y1="2" x2="812" y2="2" stroke="#ffffff" stroke-opacity="0.26" stroke-width="0.9"/>
  <text x="452" y="34" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">CONTRIBUTION PULSE</text>
  <text x="812" y="34" text-anchor="end" font-family="{FONT_SANS}" font-size="12" font-weight="600" fill="#0a84ff">20 Weeks</text>
  <line x1="{gx}" y1="{gy + gh}" x2="{gx + gw}" y2="{gy + gh}" stroke="#ffffff" stroke-opacity="0.08" stroke-width="1"/>
  <path d="{area_d}" fill="url(#tideArea)"/>
  <path d="{line_d}" fill="none" stroke="#0a84ff" stroke-width="2.4" filter="url(#softGlow)" stroke-dasharray="600" stroke-dashoffset="0">
    <animate attributeName="stroke-dashoffset" from="600" to="0" dur="1.8s" fill="freeze"/>
  </path>
  {peak_dot}
</svg>
"""


def build_stack_spotlight() -> str:
    # Apple Liquid Glass Mesh-Orb Squircles (modeled on the 6 uploaded mesh squircles) + smooth floating animation
    w, h = 840, 316

    # 6 Liquid Mesh presets matching user's uploaded reference:
    # (base_dark, blob1_col, blob1_xy, blob2_col, blob2_xy, mode)
    MESH_PRESETS = [
        ("#140402", "#ff3b1d", ("50%", "85%"), "#ff7b3a", ("15%", "65%"), "dark_top"),   # Red-Orange with dark top
        ("#1f2e03", "#d4ff00", ("18%", "15%"), "#6d28d9", ("68%", "78%"), "dual"),       # Lime-Yellow + Violet
        ("#03170b", "#22c55e", ("50%", "78%"), "#6ee7b7", ("50%", "90%"), "dark_top"),   # Forest-Mint
        ("#081018", "#38bdf8", ("22%", "22%"), "#f472b6", ("78%", "76%"), "dual"),       # Cyan + Pink
        ("#2a0633", "#e879f9", ("10%", "15%"), "#c026d3", ("88%", "85%"), "dark_core"),  # Magenta ring + dark center
        ("#0c1445", "#2563eb", ("50%", "50%"), "#7dd3fc", ("50%", "50%"), "core_glow"),  # Cobalt + Ice Blue core
    ]

    icons = [
        '<path fill="#ffffff" d="M11.9 2C7.3 2 7.6 4 7.6 4v2.1h4.4v.6H5.8S2.5 6.3 2.5 11s2.9 4.5 2.9 4.5h1.7v-2.2s-.1-2.9 2.8-2.9h4.6s2.6 0 2.6-2.5V4.4S17.5 2 11.9 2zm-2.5 1.4a.8.8 0 1 1 0 1.6.8.8 0 0 1 0-1.6z"/><path fill="#ffffff" fill-opacity="0.78" d="M12.1 22c4.6 0 4.3-2 4.3-2v-2.1H12v-.6h6.2s3.3.4 3.3-4.3-2.9-4.5-2.9-4.5h-1.7v2.2s.1 2.9-2.8 2.9H9.5s-2.6 0-2.6 2.5v3.5S6.5 22 12.1 22zm2.5-1.4a.8.8 0 1 1 0-1.6.8.8 0 0 1 0-1.6z"/>',
        '<path fill="#ffffff" d="M13.5 12.6H11v6.9H9.1v-6.9H6.6V11h6.9v1.6zm1.1 5.1c.6.4 1.4.6 2.2.6.9 0 1.5-.3 1.5-.9 0-.5-.4-.8-1.4-1.2-1.5-.5-2.4-1.2-2.4-2.5 0-1.5 1.2-2.5 3.1-2.5.9 0 1.7.2 2.2.5l-.5 1.5c-.4-.2-1-.4-1.7-.4-.8 0-1.3.3-1.3.8 0 .5.4.8 1.5 1.2 1.6.6 2.3 1.3 2.3 2.6 0 1.5-1.1 2.6-3.4 2.6-1 0-2-.3-2.6-.7l.5-1.6z"/>',
        '<path fill="#09090b" d="M10.8 16.9c0 1.6-.9 2.4-2.3 2.4-1 0-1.7-.5-2.1-1.2l1.3-.8c.2.4.5.6.9.6.5 0 .8-.2.8-1v-5.3h1.4v5.3zm2.6.2c.4.6.9 1 1.7 1 .7 0 1.2-.3 1.2-.8 0-.5-.4-.7-1.2-1.1l-.4-.2c-1.2-.5-2-1.1-2-2.4 0-1.2.9-2.1 2.4-2.1 1 0 1.8.4 2.3 1.3l-1.2.8c-.3-.5-.6-.7-1.1-.7-.5 0-.8.3-.8.7 0 .5.3.7 1.1 1l.4.2c1.4.6 2.2 1.2 2.2 2.5 0 1.4-1.1 2.2-2.6 2.2-1.5 0-2.4-.7-2.9-1.6l1.3-.8z"/>',
        '<path fill="#ffffff" d="M12 2.2L6.3 7.9a8 8 0 1 0 11.4 0l-1.8 1.8a5.5 5.5 0 1 1-7.8 0L12 5.8V2.2z"/><circle cx="15.5" cy="6.2" r="1.5" fill="#ffffff"/>',
        '<path fill="#ffffff" d="M12 2L3.5 6.8v3.6l5-2.8v11.6l3.5 2V7.8l5 2.8v3.6l3.5-2V6.8L12 2zm3.5 9.8v3.4l2.8-1.6v-3.4l-2.8 1.6z"/>',
        '<circle cx="12" cy="12" r="2.2" fill="#ffffff"/><ellipse cx="12" cy="12" rx="9.5" ry="3.7" stroke="#ffffff" stroke-width="1.4" fill="none"/><ellipse cx="12" cy="12" rx="9.5" ry="3.7" transform="rotate(60 12 12)" stroke="#ffffff" stroke-width="1.4" fill="none"/><ellipse cx="12" cy="12" rx="9.5" ry="3.7" transform="rotate(120 12 12)" stroke="#ffffff" stroke-width="1.4" fill="none"/>',
        '<circle cx="12" cy="12" r="9.5" fill="none" stroke="#ffffff" stroke-width="1.5"/><path d="M8.5 16V8l8.2 10.5M15.5 8v4.8" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>',
        '<path fill="#ffffff" d="M12 2l8.6 5v10L12 22l-8.6-5V7L12 2zm0 2.5L5.6 8.2v7.6L12 19.5l6.4-3.7V8.2L12 4.5z"/><path fill="#ffffff" d="M12 8.2l3.8 2.2v3.2L12 15.8l-3.8-2.2v-3.2L12 8.2z"/>',
        '<path fill="#ffffff" d="M13 8h2v2h-2V8zm-3 0h2v2h-2V8zm0-3h2v2h-2V5zm-3 3h2v2H7V8zm-3 0h2v2H4V8zm3-3h2v2H7V5zm14.5 5.4c-.5-.4-1.6-.5-2.3-.3-.2-1.3-1-2.3-2-2.8l-.4-.2-.2.4c-.3.6-.4 1.5-.1 2.2.2.5.6.9 1 1.2H2.2l-.1.6c-.2 1.8.3 3.7 1.4 5 1.1 1.3 2.8 2 4.9 2 4.4 0 7.7-2 9.4-5.7.6 0 2-.1 2.7-1.3.1-.1.5-.8.2-1.1z"/>',
        '<path fill="#ffffff" d="M21.6 11.1L12.9 2.4a1.3 1.3 0 0 0-1.8 0L9.3 4.2l2.3 2.3a1.5 1.5 0 0 1 1.9 1.9l2.2 2.2a1.5 1.5 0 1 1-.9.9l-2.1-2.1v5.5a1.5 1.5 0 1 1-1.2 0V9.3a1.5 1.5 0 0 1-.8-2L8.4 5 2.4 11a1.3 1.3 0 0 0 0 1.8l8.7 8.7a1.3 1.3 0 0 0 1.8 0l8.7-8.7a1.3 1.3 0 0 0 0-1.7z"/>',
        '<circle cx="12" cy="12.5" r="8" fill="#ffffff" fill-opacity="0.18" stroke="#ffffff" stroke-width="1.5"/><circle cx="14.5" cy="9.5" r="2.2" fill="#ffffff"/><circle cx="19" cy="5.5" r="2" fill="#ffffff"/>',
        '<path fill="#ffffff" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.5h-2v-2h2zm0-4h-2V7h2z"/>',
        '<path fill="#ffffff" d="M12 6c-3 0-4.8 1.5-5.5 4.5 1.1-1.5 2.4-2 3.8-1.7.8.2 1.4.8 2.1 1.5 1.1 1.1 2.3 2.4 5.1 2.4 3 0 4.8-1.5 5.5-4.5-1.1 1.5-2.4 2-3.8 1.7-.8-.2-1.4-.8-2.1-1.5C16 7.3 14.8 6 12 6zm-5.5 6.8c-3 0-4.8 1.5-5.5 4.5 1.1-1.5 2.4-2 3.8-1.7.8.2 1.4.8 2.1 1.5 1.1 1.1 2.3 2.4 5.1 2.4 3 0 4.8-1.5 5.5-4.5-1.1 1.5-2.4 2-3.8 1.7-.8-.2-1.4-.8-2.1-1.5-1.1-1.1-2.3-2.4-5.1-2.4z"/>',
        '<path fill="#ffffff" d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.5L19.5 8.5 12 12.5 4.5 8.5 12 4.5z"/>',
        '<circle cx="12" cy="12" r="8" fill="#09090b" fill-opacity="0.75"/><circle cx="9.5" cy="10.5" r="1.3" fill="#ffffff"/><circle cx="14.5" cy="10.5" r="1.3" fill="#ffffff"/><path d="M8.5 14.5c1 1.5 2.2 2 3.5 2s2.5-.5 3.5-2" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>',
        '<path fill="#ffffff" d="M21 4L12 21 3 4l9 3 9-3z"/>',
        '<path fill="#ffffff" d="M21 3.5L16.8 1.5 9.2 8.8 5.2 5.8 3.2 7.2l4.2 3.8-4.2 3.8 2 1.4 4-3 7.6 7.3 4.2-2V3.5zm-4.2 11.7L12.5 12l4.3-3.2v6.4z"/>',
        '<path fill="#ffffff" d="M12 2a10 10 0 0 0-3.2 19.5c.5.1.7-.2.7-.5v-1.8c-2.8.6-3.4-1.2-3.4-1.2-.5-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.6.3-1.1.6-1.3-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.6 0 0 .8-.3 2.7 1a9.4 9.4 0 0 1 5 0c1.9-1.3 2.7-1 2.7-1 .5 1.3.2 2.3.1 2.6.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9V21c0 .3.2.6.7.5A10 10 0 0 0 12 2z"/>',
        '<circle cx="9.5" cy="7.5" r="2.5" fill="#ffffff"/><circle cx="14.5" cy="7.5" r="2.5" fill="#ffffff" fill-opacity="0.7"/><circle cx="9.5" cy="12.5" r="2.5" fill="#ffffff" fill-opacity="0.85"/><circle cx="14.5" cy="12.5" r="2.5" fill="#ffffff"/><circle cx="9.5" cy="17.5" r="2.5" fill="#ffffff"/>',
        '<path fill="#ffffff" d="M18.5 10.5A6.5 6.5 0 0 0 6.2 8.2 5 5 0 0 0 6.5 18h11.5a4 4 0 0 0 .5-7.5z"/>',
    ]

    sq = 72
    gap_x = 12
    gap_y = 12
    total_w = 10 * sq + 9 * gap_x
    sx = (w - total_w) / 2
    col_offsets = [24, 6, 32, 10, 26, 2, 22, 8, 28, 14]

    defs_extra = []
    cols_svg = []
    for col in range(10):
        tx = sx + col * (sq + gap_x)
        base_y = 110 + col_offsets[col]
        dur = 5.0 + (col % 4) * 0.9
        begin = (col * 0.35) % 2.5
        col_items = []
        for row in range(2):
            idx = col + row * 10
            base_c, b1c, (b1x, b1y), b2c, (b2x, b2y), mode = MESH_PRESETS[idx % len(MESH_PRESETS)]
            ipath = icons[idx]
            ty = base_y + row * (sq + gap_y)
            uid = f"mesh_{idx}"

            if mode == "dark_core":
                grad = (
                    f'<radialGradient id="{uid}_a" cx="50%" cy="50%" r="65%">'
                    f'<stop offset="0%" stop-color="#09020e" stop-opacity="0.96"/>'
                    f'<stop offset="55%" stop-color="{b2c}" stop-opacity="0.75"/>'
                    f'<stop offset="100%" stop-color="{b1c}" stop-opacity="0.98"/>'
                    f'</radialGradient>'
                )
            elif mode == "core_glow":
                grad = (
                    f'<radialGradient id="{uid}_a" cx="50%" cy="50%" r="55%">'
                    f'<stop offset="0%" stop-color="{b2c}" stop-opacity="0.98"/>'
                    f'<stop offset="48%" stop-color="{b1c}" stop-opacity="0.88"/>'
                    f'<stop offset="100%" stop-color="{base_c}" stop-opacity="0.98"/>'
                    f'</radialGradient>'
                )
            else:
                grad = (
                    f'<radialGradient id="{uid}_a" cx="{b1x}" cy="{b1y}" r="68%">'
                    f'<stop offset="0%" stop-color="{b1c}" stop-opacity="0.96"/>'
                    f'<stop offset="100%" stop-color="{base_c}" stop-opacity="0"/>'
                    f'</radialGradient>'
                    f'<radialGradient id="{uid}_b" cx="{b2x}" cy="{b2y}" r="62%">'
                    f'<stop offset="0%" stop-color="{b2c}" stop-opacity="0.92"/>'
                    f'<stop offset="100%" stop-color="{base_c}" stop-opacity="0"/>'
                    f'</radialGradient>'
                )
            defs_extra.append(grad)
            defs_extra.append(f'<clipPath id="cp_{idx}"><rect x="{tx:.1f}" y="{ty:.1f}" width="{sq}" height="{sq}" rx="18"/></clipPath>')

            ix = tx + (sq - 38) / 2
            iy = ty + (sq - 38) / 2
            fill_layers = (
                f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{sq}" height="{sq}" fill="url(#{uid}_a)"/>'
                if mode in ("dark_core", "core_glow")
                else f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{sq}" height="{sq}" fill="url(#{uid}_a)"/><rect x="{tx:.1f}" y="{ty:.1f}" width="{sq}" height="{sq}" fill="url(#{uid}_b)"/>'
            )
            col_items.append(
                f'<g clip-path="url(#cp_{idx})">'
                f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{sq}" height="{sq}" fill="{base_c}"/>'
                f'{fill_layers}'
                f'</g>'
                f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{sq}" height="{sq}" rx="18" fill="none" stroke="#ffffff" stroke-opacity="0.28" stroke-width="1.1"/>'
                f'<svg x="{ix:.1f}" y="{iy:.1f}" width="38" height="38" viewBox="0 0 24 24">{ipath}</svg>'
            )

        # Smooth Liquid Glass column levitation
        cols_svg.append(
            f'<g>'
            f'<animateTransform attributeName="transform" type="translate" values="0,0; 0,-7; 0,0" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'{"".join(col_items)}'
            f'</g>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <defs>
    <clipPath id="stackClipV2">
      <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="28"/>
    </clipPath>
    <linearGradient id="bottomFadeV2" x1="0%" y1="76%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.88"/>
    </linearGradient>
    {''.join(defs_extra)}
  </defs>
  <g clip-path="url(#stackClipV2)">
    <rect width="{w}" height="{h}" fill="#000000"/>
    <text x="{w/2}" y="66" text-anchor="middle" font-family="{FONT_SANS}" font-size="36" font-weight="700" letter-spacing="-1" fill="#ffffff">Core Stack</text>
    {''.join(cols_svg)}
    <rect width="{w}" height="{h}" fill="url(#bottomFadeV2)"/>
  </g>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="28" fill="none" stroke="url(#cardRim)" stroke-width="1.2"/>
</svg>
"""


def build_link_pill(title: str, c_left: str, c_right: str) -> str:
    w, h = 274, 72
    r = h / 2
    uid = "".join(ch for ch in title.lower() if ch.isalnum())
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <defs>
    <clipPath id="clip_{uid}_v2">
      <rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="{r-1.5}"/>
    </clipPath>
    <linearGradient id="horiz_{uid}_v2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_left}"/>
      <stop offset="48%" stop-color="{c_left}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{c_right}"/>
    </linearGradient>
    <linearGradient id="vertFade_{uid}_v2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#050507" stop-opacity="0.88"/>
      <stop offset="28%" stop-color="#050507" stop-opacity="0.45"/>
      <stop offset="60%" stop-color="#050507" stop-opacity="0.0"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.28"/>
    </linearGradient>
    <radialGradient id="btmGlow_{uid}_v2" cx="50%" cy="100%" r="75%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.52"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
      <animate attributeName="cx" values="35%;65%;35%" dur="6s" repeatCount="indefinite"/>
    </radialGradient>
    <linearGradient id="rim_{uid}_v2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55"/>
      <stop offset="35%" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="75%" stop-color="#ffffff" stop-opacity="0.42"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.92"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#clip_{uid}_v2)">
    <rect width="{w}" height="{h}" fill="#050507"/>
    <rect width="{w}" height="{h}" fill="url(#horiz_{uid}_v2)"/>
    <rect width="{w}" height="{h}" fill="url(#vertFade_{uid}_v2)"/>
    <rect width="{w}" height="{h}" fill="url(#btmGlow_{uid}_v2)"/>
    <rect x="-120" y="0" width="90" height="{h}" fill="url(#sheenSweep)" transform="skewX(-20)">
      <animate attributeName="x" values="-140;{w + 100}" dur="5s" repeatCount="indefinite"/>
    </rect>
  </g>
  <rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="{r-1.5}" fill="none" stroke="url(#rim_{uid}_v2)" stroke-width="1.5"/>
  <text x="28" y="42" font-family="{FONT_SANS}" font-size="17" font-weight="500" letter-spacing="-0.2" fill="#f5f5f7">{esc(title)}</text>
  <circle cx="{w-36}" cy="{h/2}" r="22" fill="#ffffff"/>
  <path d="M{w-44} {h/2} H{w-28} M{w-34} {h/2-6} L{w-28} {h/2} L{w-34} {h/2+6}" stroke="{c_right}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <animateTransform attributeName="transform" type="translate" values="0,0; 2.5,0; 0,0" dur="2.4s" repeatCount="indefinite"/>
  </path>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    local_json = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_github_data(local_json)
    m = compute_metrics(data)

    outputs = {
        "dynamic-island-v5.svg": build_dynamic_island(m),
        "widget-bio-v2.svg": build_bio_widget(),
        "widget-commits-v2.svg": build_counter_widget(m),
        "widget-rings-v2.svg": build_rings_widget(m),
        "widget-telemetry-v2.svg": build_telemetry_row(m),
        "widget-mesh-stack.svg": build_stack_spotlight(),
        "link-elera-v2.svg": build_link_pill("Elera AI", "#ff5e3a", "#ffd166"),
        "link-linkedin-v2.svg": build_link_pill("LinkedIn", "#0a84ff", "#bf5af2"),
        "link-x-v2.svg": build_link_pill("X  @NightEdge707", "#30d158", "#64d2ff"),
    }

    for fname, svg in outputs.items():
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Generated {fname} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
