#!/usr/bin/env python3
"""
Generates Apple-inspired Liquid Glass, Dynamic Island, and WatchOS StandBy
dark-mode SVG widgets for NightAI707 using live GitHub GraphQL telemetry.
Zero external dependencies (Python 3 stdlib only).
"""

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
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.24"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.14"/>
    </linearGradient>
    <linearGradient id="meshWarm" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff2d55"/>
      <stop offset="52%" stop-color="#ff6b35"/>
      <stop offset="100%" stop-color="#ffd166"/>
    </linearGradient>
    <linearGradient id="tideArea" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0a84ff" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#0a84ff" stop-opacity="0.0"/>
    </linearGradient>
    <radialGradient id="stackSpot" cx="50%" cy="48%" r="46%">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.34"/>
      <stop offset="55%" stop-color="#1d4ed8" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
"""


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
    w, h = 840, 62
    # Live Activity Dynamic Island pill
    wave_bars = [
        (8, "#ff2d55"), (16, "#ff5e3a"), (24, "#ff9f0a"),
        (14, "#30d158"), (22, "#0a84ff"), (12, "#bf5af2"), (18, "#ff2d55"),
    ]
    bars_svg = []
    for i, (bh, col) in enumerate(wave_bars):
        bx = 400 + i * 7
        by = 31 - bh / 2
        bars_svg.append(
            f'<rect x="{bx}" y="{by:.1f}" width="3.5" height="{bh}" rx="1.75" fill="{col}">'
            f'<animate attributeName="height" values="{bh};{max(6, bh-8)};{bh}" dur="{1.1 + i*0.15:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{by:.1f};{31 - max(6, bh-8)/2:.1f};{by:.1f}" dur="{1.1 + i*0.15:.2f}s" repeatCount="indefinite"/>'
            f'</rect>'
        )

    streak_frac = min(1.0, max(0.15, m["current_streak"] / 14.0))
    r = 12
    circ = 2 * math.pi * r
    dash = circ * streak_frac

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="60" y="5" width="720" height="52" rx="26" fill="#050507" stroke="#ffffff" stroke-opacity="0.16" stroke-width="1.1"/>
  <line x1="90" y1="6" x2="750" y2="6" stroke="#ffffff" stroke-opacity="0.22" stroke-width="0.8"/>

  <!-- Left Live Status -->
  <circle cx="92" cy="31" r="5" fill="#30d158" filter="url(#softGlow)">
    <animate attributeName="opacity" values="1;0.35;1" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  <text x="108" y="28" font-family="{FONT_SANS}" font-size="13" font-weight="600" fill="#f5f5f7">Elera AI</text>
  <text x="108" y="43" font-family="{FONT_MONO}" font-size="10.5" fill="#8e8e93">In Active Development</text>

  <!-- Center Multi-Hue Waveform -->
  {''.join(bars_svg)}

  <!-- Right Live Streak Ring -->
  <text x="708" y="28" text-anchor="end" font-family="{FONT_SANS}" font-size="12.5" font-weight="600" fill="#f5f5f7">{m['current_streak']}d Streak</text>
  <text x="708" y="43" text-anchor="end" font-family="{FONT_MONO}" font-size="10.5" fill="#8e8e93">{m['total']} commits</text>
  <circle cx="740" cy="31" r="{r}" stroke="#1c1c1e" stroke-width="3.5" fill="none"/>
  <circle cx="740" cy="31" r="{r}" stroke="#0a84ff" stroke-width="3.5" stroke-linecap="round" fill="none"
          stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 740 31)"/>
</svg>
"""


def build_bio_widget() -> str:
    w, h = 412, 224
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="url(#cardDark)" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="28" y1="2" x2="{w-28}" y2="2" stroke="#ffffff" stroke-opacity="0.26" stroke-width="0.9"/>

  <text x="26" y="36" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">ABOUT</text>
  <text x="26" y="68" font-family="{FONT_SANS}" font-size="18" font-weight="600" fill="#f5f5f7">Night Edge</text>
  <text x="26" y="96" font-family="{FONT_SANS}" font-size="13.5" fill="#d1d1d6">Student at IIT Patna and founder of Elera AI.</text>
  <text x="26" y="116" font-family="{FONT_SANS}" font-size="13.5" fill="#d1d1d6">Building AI-powered creative tools and</text>
  <text x="26" y="136" font-family="{FONT_SANS}" font-size="13.5" fill="#d1d1d6">intelligent systems across Python, TS, and Lua.</text>

  <!-- Subtle Apple Pill Tags -->
  <g transform="translate(26, 164)">
    <rect width="102" height="28" rx="14" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.16" stroke-width="0.9"/>
    <text x="51" y="18" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#f5f5f7">Gen-AI</text>

    <rect x="110" width="114" height="28" rx="14" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.16" stroke-width="0.9"/>
    <text x="167" y="18" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#f5f5f7">Open Source</text>

    <rect x="232" width="122" height="28" rx="14" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.16" stroke-width="0.9"/>
    <text x="293" y="18" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#f5f5f7">Cybersecurity</text>
  </g>
</svg>
"""


def build_counter_widget(m: dict) -> str:
    # Vibrant Apple Mesh Gradient Widget (Image 1 "38" aesthetic)
    w, h = 204, 224
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="url(#meshWarm)" stroke="#ffffff" stroke-opacity="0.32" stroke-width="1.2"/>
  <line x1="26" y1="2" x2="{w-26}" y2="2" stroke="#ffffff" stroke-opacity="0.55" stroke-width="1"/>
  <text x="22" y="34" font-family="{FONT_SANS}" font-size="11.5" font-weight="600" letter-spacing="0.8" fill="#ffffff" fill-opacity="0.88">COMMITS</text>
  <text x="{w/2:.0f}" y="142" text-anchor="middle" font-family="{FONT_SANS}" font-size="84" font-weight="300" letter-spacing="-3" fill="#ffffff" fill-opacity="0.95">{m['total']}</text>
  <text x="22" y="196" font-family="{FONT_SANS}" font-size="12" font-weight="500" fill="#ffffff" fill-opacity="0.85">Last 365 days</text>
</svg>
"""


def build_rings_widget(m: dict) -> str:
    # Apple Watch / StandBy Activity Rings Widget (Image 3 aesthetic)
    w, h = 204, 224
    cx, cy = 102, 114
    rings = [
        (56, "#fa114f", min(1.0, max(0.16, m["total"] / 100.0))),
        (42, "#92e82a", min(1.0, max(0.16, m["active_days"] / 60.0))),
        (28, "#00d4ff", min(1.0, max(0.16, m["longest_streak"] / 30.0))),
    ]
    ring_svg = []
    for r, col, frac in rings:
        circ = 2 * math.pi * r
        dash = circ * frac
        ring_svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{col}" stroke-opacity="0.16" stroke-width="10" fill="none"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{col}" stroke-width="10" stroke-linecap="round" fill="none" '
            f'stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>'
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
    # Left: StandBy Multi-Hue Pill Bars | Right: Apple Tide Smooth Curve
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
        left_bars.append(
            f'<rect x="{bx}" y="58" width="22" height="78" rx="11" fill="#1c1c1e"/>'
            f'<rect x="{bx}" y="{by}" width="22" height="{bh}" rx="11" fill="{col}" fill-opacity="{0.25 if val == 0 else 0.95}"/>'
            f'<text x="{bx+11}" y="156" text-anchor="middle" font-family="{FONT_MONO}" font-size="10" fill="#8e8e93">{lbl}</text>'
        )

    # Right: Smooth Tide Curve
    weekly = m["weekly_totals"]
    max_w = max([v for _, v in weekly] + [1])
    gx, gy, gw, gh = 446, 58, 362, 78
    pts = []
    for i, (_, v) in enumerate(weekly):
        x = gx + (i / max(1, len(weekly) - 1)) * gw
        y = gy + gh - (v / max_w) * (gh - 8)
        pts.append((x, y))

    line_d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        mx = (x0 + x1) / 2
        line_d += f" C {mx:.1f} {y0:.1f}, {mx:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}"
    area_d = line_d + f" L {pts[-1][0]:.1f} {gy + gh} L {pts[0][0]:.1f} {gy + gh} Z"

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <!-- Left Card: Monthly Pill Bars -->
  <rect x="1" y="1" width="410" height="{h-2}" rx="26" fill="url(#cardDark)" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="28" y1="2" x2="384" y2="2" stroke="#ffffff" stroke-opacity="0.26" stroke-width="0.9"/>
  <text x="26" y="34" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">MONTHLY OUTPUT</text>
  {''.join(left_bars)}

  <!-- Right Card: Apple Tide Pulse -->
  <rect x="427" y="1" width="412" height="{h-2}" rx="26" fill="url(#cardDark)" stroke="url(#cardRim)" stroke-width="1.1"/>
  <line x1="454" y1="2" x2="812" y2="2" stroke="#ffffff" stroke-opacity="0.26" stroke-width="0.9"/>
  <text x="452" y="34" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">CONTRIBUTION PULSE</text>
  <text x="812" y="34" text-anchor="end" font-family="{FONT_SANS}" font-size="12" font-weight="600" fill="#0a84ff">20 Weeks</text>
  <line x1="{gx}" y1="{gy + gh}" x2="{gx + gw}" y2="{gy + gh}" stroke="#ffffff" stroke-opacity="0.08" stroke-width="1"/>
  <path d="{area_d}" fill="url(#tideArea)"/>
  <path d="{line_d}" fill="none" stroke="#0a84ff" stroke-width="2.4" filter="url(#softGlow)"/>
</svg>
"""


def build_stack_spotlight() -> str:
    # Inspired by Image 6: Dark frosted tile grid with central blue/indigo spotlight & real brand logos
    w, h = 840, 232
    tiles = [
        ("Python", '<path fill="#3776AB" d="M11.9 2C7.3 2 7.6 4 7.6 4v2.1h4.4v.6H5.8S2.5 6.3 2.5 11s2.9 4.5 2.9 4.5h1.7v-2.2s-.1-2.9 2.8-2.9h4.6s2.6 0 2.6-2.5V4.4S17.5 2 11.9 2zm-2.5 1.4a.8.8 0 1 1 0 1.6.8.8 0 0 1 0-1.6z"/><path fill="#FFD43B" d="M12.1 22c4.6 0 4.3-2 4.3-2v-2.1H12v-.6h6.2s3.3.4 3.3-4.3-2.9-4.5-2.9-4.5h-1.7v2.2s.1 2.9-2.8 2.9H9.5s-2.6 0-2.6 2.5v3.5S6.5 22 12.1 22zm2.5-1.4a.8.8 0 1 1 0-1.6.8.8 0 0 1 0 1.6z"/>'),
        ("TypeScript", '<rect x="2" y="2" width="20" height="20" rx="3" fill="#3178C6"/><path fill="#ffffff" d="M13.5 12.6H11v6.9H9.1v-6.9H6.6V11h6.9v1.6zm1.1 5.1c.6.4 1.4.6 2.2.6.9 0 1.5-.3 1.5-.9 0-.5-.4-.8-1.4-1.2-1.5-.5-2.4-1.2-2.4-2.5 0-1.5 1.2-2.5 3.1-2.5.9 0 1.7.2 2.2.5l-.5 1.5c-.4-.2-1-.4-1.7-.4-.8 0-1.3.3-1.3.8 0 .5.4.8 1.5 1.2 1.6.6 2.3 1.3 2.3 2.6 0 1.5-1.1 2.6-3.4 2.6-1 0-2-.3-2.6-.7l.5-1.6z"/>'),
        ("JavaScript", '<rect x="2" y="2" width="20" height="20" rx="3" fill="#F7DF1E"/><path fill="#000000" d="M10.8 16.9c0 1.6-.9 2.4-2.3 2.4-1 0-1.7-.5-2.1-1.2l1.3-.8c.2.4.5.6.9.6.5 0 .8-.2.8-1v-5.3h1.4v5.3zm2.6.2c.4.6.9 1 1.7 1 .7 0 1.2-.3 1.2-.8 0-.5-.4-.7-1.2-1.1l-.4-.2c-1.2-.5-2-1.1-2-2.4 0-1.2.9-2.1 2.4-2.1 1 0 1.8.4 2.3 1.3l-1.2.8c-.3-.5-.6-.7-1.1-.7-.5 0-.8.3-.8.7 0 .5.3.7 1.1 1l.4.2c1.4.6 2.2 1.2 2.2 2.5 0 1.4-1.1 2.2-2.6 2.2-1.5 0-2.4-.7-2.9-1.6l1.3-.8z"/>'),
        ("Lua", '<circle cx="12" cy="12.5" r="8.5" fill="#2C2D72"/><circle cx="14.5" cy="9.5" r="2.2" fill="#ffffff"/><circle cx="19.5" cy="5" r="2" fill="#64D2FF"/>'),
        ("PyTorch", '<path fill="#EE4C2C" d="M12 2.2L6.3 7.9a8 8 0 1 0 11.4 0l-1.8 1.8a5.5 5.5 0 1 1-7.8 0L12 5.8V2.2z"/><circle cx="15.5" cy="6.2" r="1.4" fill="#EE4C2C"/>'),
        ("TensorFlow", '<path fill="#FF6F00" d="M12 2L3.5 6.8v3.6l5-2.8v11.6l3.5 2V7.8l5 2.8v3.6l3.5-2V6.8L12 2zm3.5 9.8v3.4l2.8-1.6v-3.4l-2.8 1.6z"/>'),
        ("React", '<circle cx="12" cy="12" r="2.1" fill="#61DAFB"/><ellipse cx="12" cy="12" rx="9.5" ry="3.7" stroke="#61DAFB" stroke-width="1.3" fill="none"/><ellipse cx="12" cy="12" rx="9.5" ry="3.7" transform="rotate(60 12 12)" stroke="#61DAFB" stroke-width="1.3" fill="none"/><ellipse cx="12" cy="12" rx="9.5" ry="3.7" transform="rotate(120 12 12)" stroke="#61DAFB" stroke-width="1.3" fill="none"/>'),
        ("Next.js", '<circle cx="12" cy="12" r="9.5" fill="#000000" stroke="#ffffff" stroke-width="1.3"/><path d="M8.5 16V8l8.2 10.5M15.5 8v4.8" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>'),
        ("Node.js", '<path fill="#539E43" d="M12 2l8.6 5v10L12 22l-8.6-5V7L12 2zm0 2.5L5.6 8.2v7.6L12 19.5l6.4-3.7V8.2L12 4.5z"/><path fill="#539E43" d="M12 8.2l3.8 2.2v3.2L12 15.8l-3.8-2.2v-3.2L12 8.2z"/>'),
        ("Docker", '<path fill="#2496ED" d="M13 8h2v2h-2V8zm-3 0h2v2h-2V8zm0-3h2v2h-2V5zm-3 3h2v2H7V8zm-3 0h2v2H4V8zm3-3h2v2H7V5zm14.5 5.4c-.5-.4-1.6-.5-2.3-.3-.2-1.3-1-2.3-2-2.8l-.4-.2-.2.4c-.3.6-.4 1.5-.1 2.2.2.5.6.9 1 1.2H2.2l-.1.6c-.2 1.8.3 3.7 1.4 5 1.1 1.3 2.8 2 4.9 2 4.4 0 7.7-2 9.4-5.7.6 0 2-.1 2.7-1.3.1-.1.5-.8.2-1.1z"/>'),
        ("Git", '<path fill="#F05032" d="M21.6 11.1L12.9 2.4a1.3 1.3 0 0 0-1.8 0L9.3 4.2l2.3 2.3a1.5 1.5 0 0 1 1.9 1.9l2.2 2.2a1.5 1.5 0 1 1-.9.9l-2.1-2.1v5.5a1.5 1.5 0 1 1-1.2 0V9.3a1.5 1.5 0 0 1-.8-2L8.4 5 2.4 11a1.3 1.3 0 0 0 0 1.8l8.7 8.7a1.3 1.3 0 0 0 1.8 0l8.7-8.7a1.3 1.3 0 0 0 0-1.7z"/>'),
        ("Linux", '<circle cx="12" cy="10" r="5" fill="#FCC624"/><path fill="#111827" d="M9.5 10c0-1.4 1.1-2.5 2.5-2.5s2.5 1.1 2.5 2.5v2.2c1.2 1 2 2.5 2 4.3 0 1.5-.8 2.5-2.2 2.5H9.7c-1.4 0-2.2-1-2.2-2.5 0-1.8.8-3.3 2-4.3V10z"/><circle cx="10.8" cy="9.5" r=".7" fill="#ffffff"/><circle cx="13.2" cy="9.5" r=".7" fill="#ffffff"/><path fill="#FCC624" d="M10.5 11.2h3L12 12.8z"/>'),
    ]
    tile_w, tile_h = 118, 74
    gap_x, gap_y = 12, 12
    sx = (w - (6 * tile_w + 5 * gap_x)) / 2
    sy = 54

    tile_svg = []
    for i, (name, icon_paths) in enumerate(tiles):
        r = i // 6
        c = i % 6
        tx = sx + c * (tile_w + gap_x)
        ty = sy + r * (tile_h + gap_y)
        op = "0.98" if c in (1, 2, 3, 4) else "0.72"
        bg_op = "0.11" if c in (2, 3) else "0.06"
        ix = tx + tile_w / 2 - 14
        iy = ty + 11
        tile_svg.append(
            f'<g opacity="{op}">'
            f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{tile_w}" height="{tile_h}" rx="16" fill="#ffffff" fill-opacity="{bg_op}" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1"/>'
            f'<svg x="{ix:.1f}" y="{iy:.1f}" width="28" height="28" viewBox="0 0 24 24">{icon_paths}</svg>'
            f'<text x="{tx + tile_w/2:.1f}" y="{ty + 57:.1f}" text-anchor="middle" font-family="{FONT_SANS}" font-size="11.5" font-weight="500" fill="#e5e5ea">{esc(name)}</text>'
            f'</g>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="#050507" stroke="url(#cardRim)" stroke-width="1.1"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="26" fill="url(#stackSpot)"/>
  <line x1="28" y1="2" x2="{w-28}" y2="2" stroke="#ffffff" stroke-opacity="0.24" stroke-width="0.9"/>
  <text x="36" y="34" font-family="{FONT_SANS}" font-size="12" font-weight="600" letter-spacing="0.8" fill="#8e8e93">CORE STACK</text>
  <text x="804" y="34" text-anchor="end" font-family="{FONT_SANS}" font-size="12" fill="#636366">AI, Systems &amp; Web</text>
  {''.join(tile_svg)}
</svg>
"""


def build_link_pill(title: str, c_left: str, c_right: str) -> str:
    w, h = 274, 72
    r = h / 2
    uid = "".join(ch for ch in title.lower() if ch.isalnum())
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="clip_{uid}">
      <rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="{r-1.5}"/>
    </clipPath>
    <linearGradient id="horiz_{uid}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_left}"/>
      <stop offset="48%" stop-color="{c_left}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{c_right}"/>
    </linearGradient>
    <linearGradient id="vertFade_{uid}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#050507" stop-opacity="0.88"/>
      <stop offset="28%" stop-color="#050507" stop-opacity="0.45"/>
      <stop offset="60%" stop-color="#050507" stop-opacity="0.0"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.28"/>
    </linearGradient>
    <radialGradient id="btmGlow_{uid}" cx="50%" cy="100%" r="75%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.52"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rim_{uid}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55"/>
      <stop offset="35%" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="75%" stop-color="#ffffff" stop-opacity="0.42"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.92"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#clip_{uid})">
    <rect width="{w}" height="{h}" fill="#050507"/>
    <rect width="{w}" height="{h}" fill="url(#horiz_{uid})"/>
    <rect width="{w}" height="{h}" fill="url(#vertFade_{uid})"/>
    <rect width="{w}" height="{h}" fill="url(#btmGlow_{uid})"/>
  </g>
  <rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="{r-1.5}" fill="none" stroke="url(#rim_{uid})" stroke-width="1.5"/>
  <text x="28" y="42" font-family="{FONT_SANS}" font-size="17" font-weight="500" letter-spacing="-0.2" fill="#f5f5f7">{esc(title)}</text>
  <!-- White Circle + Arrow -->
  <circle cx="{w-36}" cy="{h/2}" r="22" fill="#ffffff"/>
  <path d="M{w-44} {h/2} H{w-28} M{w-34} {h/2-6} L{w-28} {h/2} L{w-34} {h/2+6}" stroke="{c_right}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    local_json = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_github_data(local_json)
    m = compute_metrics(data)

    outputs = {
        "dynamic-island.svg": build_dynamic_island(m),
        "widget-bio.svg": build_bio_widget(),
        "widget-counter.svg": build_counter_widget(m),
        "widget-rings.svg": build_rings_widget(m),
        "widget-telemetry.svg": build_telemetry_row(m),
        "widget-core-stack.svg": build_stack_spotlight(),
        "link-elera.svg": build_link_pill("Elera AI", "#ff5e3a", "#ffd166"),
        "link-linkedin.svg": build_link_pill("LinkedIn", "#0a84ff", "#bf5af2"),
        "link-x.svg": build_link_pill("X  @NightEdge707", "#30d158", "#64d2ff"),
    }

    for fname, svg in outputs.items():
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Generated {fname} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
