#!/usr/bin/env python3
"""
Generates an original Dark Apple Liquid Glass + Cyan Bento SVG system
for NightAI707's GitHub profile README using live GitHub GraphQL telemetry.
Zero external dependencies (Python 3 stdlib only).
"""

import json
import math
import os
import sys
import urllib.request
from datetime import datetime

USERNAME = os.environ.get("GITHUB_USERNAME", "NightAI707")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

FONT_SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Inter, sans-serif"
FONT_MONO = "'SF Mono', 'JetBrains Mono', Consolas, monospace"

COMMON_DEFS = """
  <defs>
    <linearGradient id="glassBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#111824" stop-opacity="0.95"/>
      <stop offset="50%" stop-color="#080c12" stop-opacity="0.98"/>
      <stop offset="100%" stop-color="#040609" stop-opacity="1"/>
    </linearGradient>
    <linearGradient id="glassRim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.32"/>
      <stop offset="45%" stop-color="#22d3ee" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.08"/>
    </linearGradient>
    <radialGradient id="cyanAura" cx="80%" cy="30%" r="60%">
      <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.16"/>
      <stop offset="60%" stop-color="#0891b2" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="waveGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.38"/>
      <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.0"/>
    </linearGradient>
    <filter id="cyanGlow" x="-30%" y="-30%" width="160%" height="160%">
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

    repos = [r for r in data["data"]["user"]["repositories"]["nodes"] if not r.get("isPrivate")]
    return {
        "total": total,
        "weeks": weeks,
        "weekly_totals": weekly_totals[-26:],
        "active_days": active_days,
        "total_days": len(days),
        "longest_streak": longest,
        "current_streak": current_streak,
        "repos": repos,
    }


def build_hero_svg() -> str:
    w, h = 840, 196
    # Subtle sinusoidal neural wave lines on the right side
    wave_paths = []
    for k, (amp, freq, phase, op) in enumerate([(22, 0.025, 0.0, 0.55), (15, 0.032, 1.4, 0.30), (28, 0.018, 2.6, 0.18)]):
        pts = []
        for x in range(470, 812, 6):
            y = 98 + amp * math.sin((x - 470) * freq + phase) * math.sin((x - 470) / 340 * math.pi)
            pts.append(f"{x},{y:.1f}")
        col = "#00e5ff" if k == 0 else "#38bdf8"
        filt = ' filter="url(#cyanGlow)"' if k == 0 else ""
        wave_paths.append(
            f'<polyline fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{1.8 - k*0.4:.1f}" points="{" ".join(pts)}"{filt}/>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="url(#glassBg)" stroke="url(#glassRim)" stroke-width="1.2"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="url(#cyanAura)"/>
  <line x1="28" y1="2" x2="{w-28}" y2="2" stroke="#ffffff" stroke-opacity="0.32" stroke-width="1"/>

  <!-- Subtle Traffic / Window Indicator Dots -->
  <circle cx="34" cy="28" r="3.5" fill="#22d3ee" fill-opacity="0.85"/>
  <circle cx="48" cy="28" r="3.5" fill="#ffffff" fill-opacity="0.22"/>
  <circle cx="62" cy="28" r="3.5" fill="#ffffff" fill-opacity="0.12"/>
  <text x="80" y="31.5" font-family="{FONT_MONO}" font-size="10.5" fill="#64748b" letter-spacing="1.2">night-edge // profile</text>

  <!-- Main Identity -->
  <text x="34" y="88" font-family="{FONT_SANS}" font-size="38" font-weight="700" letter-spacing="-1.2" fill="#f8fafc">Night Edge</text>
  <text x="36" y="116" font-family="{FONT_SANS}" font-size="15" font-weight="400" fill="#94a3b8">AI Engineer and Founder at <tspan fill="#22d3ee" font-weight="600">Elera AI</tspan>. Studying at <tspan fill="#e2e8f0" font-weight="500">IIT Patna</tspan>.</text>

  <!-- Frosted Glass Pills -->
  <g transform="translate(34, 138)">
    <rect width="124" height="28" rx="14" fill="#00e5ff" fill-opacity="0.09" stroke="#22d3ee" stroke-opacity="0.38" stroke-width="1"/>
    <circle cx="16" cy="14" r="3.5" fill="#00e5ff" filter="url(#cyanGlow)">
      <animate attributeName="opacity" values="1;0.3;1" dur="2.4s" repeatCount="indefinite"/>
    </circle>
    <text x="28" y="18" font-family="{FONT_MONO}" font-size="11" font-weight="600" fill="#cffafe">ELERA AI</text>

    <rect x="134" width="126" height="28" rx="14" fill="#ffffff" fill-opacity="0.05" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1"/>
    <text x="197" y="18" text-anchor="middle" font-family="{FONT_MONO}" font-size="11" fill="#cbd5e1">GENERATIVE AI</text>

    <rect x="270" width="120" height="28" rx="14" fill="#ffffff" fill-opacity="0.05" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1"/>
    <text x="330" y="18" text-anchor="middle" font-family="{FONT_MONO}" font-size="11" fill="#cbd5e1">OPEN SOURCE</text>
  </g>

  <!-- Right Neural Waveform -->
  <line x1="470" y1="98" x2="810" y2="98" stroke="#ffffff" stroke-opacity="0.06" stroke-width="1"/>
  {''.join(wave_paths)}
</svg>
"""


def build_about_bento() -> str:
    w, h = 480, 230
    stack = ["Python", "TypeScript", "JavaScript", "Lua", "PyTorch", "TensorFlow", "React", "Next.js", "Docker", "Git"]
    pills = []
    px, py = 26, 152
    for i, s in enumerate(stack):
        pw = len(s) * 6.8 + 20
        if px + pw > w - 24:
            px = 26
            py += 30
        pills.append(
            f'<rect x="{px:.1f}" y="{py}" width="{pw:.1f}" height="23" rx="11.5" fill="#ffffff" fill-opacity="0.05" stroke="#22d3ee" stroke-opacity="0.24" stroke-width="0.9"/>'
            f'<text x="{px + pw/2:.1f}" y="{py + 15}" text-anchor="middle" font-family="{FONT_MONO}" font-size="10" fill="#cbd5e1">{esc(s)}</text>'
        )
        px += pw + 7

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="url(#glassBg)" stroke="url(#glassRim)" stroke-width="1.2"/>
  <line x1="24" y1="2" x2="{w-24}" y2="2" stroke="#ffffff" stroke-opacity="0.28" stroke-width="0.9"/>

  <text x="26" y="34" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="1.8" fill="#22d3ee">ABOUT</text>
  <text x="26" y="62" font-family="{FONT_SANS}" font-size="14" fill="#e2e8f0">Building <tspan fill="#ffffff" font-weight="600">Elera AI</tspan>, an AI-powered creative editing</text>
  <text x="26" y="82" font-family="{FONT_SANS}" font-size="14" fill="#e2e8f0">platform. Previously shipped AI tools, Roblox</text>
  <text x="26" y="102" font-family="{FONT_SANS}" font-size="14" fill="#e2e8f0">experiences, and research prototypes.</text>
  <text x="26" y="132" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="1.8" fill="#64748b">STACK</text>
  {''.join(pills)}
</svg>
"""


def build_rings_bento(m: dict) -> str:
    w, h = 344, 230
    # Apple-style concentric glowing cyan activity rings
    cx, cy = 104, 128
    rings = [
        (64, "#00e5ff", min(1.0, max(0.12, m["total"] / 100.0))),
        (48, "#38bdf8", min(1.0, max(0.12, m["active_days"] / 60.0))),
        (32, "#a5f3fc", min(1.0, max(0.12, m["longest_streak"] / 30.0))),
    ]
    ring_elems = []
    for r, col, frac in rings:
        circ = 2 * math.pi * r
        dash = circ * frac
        ring_elems.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="#ffffff" stroke-opacity="0.06" stroke-width="9" fill="none"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{col}" stroke-width="9" stroke-linecap="round" fill="none" '
            f'stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})" filter="url(#cyanGlow)"/>'
        )

    stats = [
        ("CONTRIBUTIONS", str(m["total"]), "#00e5ff", 78),
        ("ACTIVE DAYS", str(m["active_days"]), "#38bdf8", 128),
        ("BEST STREAK", f"{m['longest_streak']}d", "#a5f3fc", 178),
    ]
    stat_elems = []
    for label, val, col, sy in stats:
        stat_elems.append(
            f'<circle cx="204" cy="{sy-4}" r="3.5" fill="{col}"/>'
            f'<text x="215" y="{sy}" font-family="{FONT_MONO}" font-size="9.5" letter-spacing="1.2" fill="#64748b">{label}</text>'
            f'<text x="215" y="{sy+22}" font-family="{FONT_SANS}" font-size="22" font-weight="700" fill="#f8fafc">{val}</text>'
        )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="url(#glassBg)" stroke="url(#glassRim)" stroke-width="1.2"/>
  <line x1="24" y1="2" x2="{w-24}" y2="2" stroke="#ffffff" stroke-opacity="0.28" stroke-width="0.9"/>

  <text x="24" y="34" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="1.8" fill="#22d3ee">ACTIVITY RINGS</text>
  {''.join(ring_elems)}
  {''.join(stat_elems)}
</svg>
"""


def build_wave_bento(m: dict) -> str:
    w, h = 840, 176
    weekly = m["weekly_totals"]
    max_v = max([v for _, v in weekly] + [1])
    gx, gy, gw, gh = 28, 52, 784, 96
    pts = []
    for i, (_, v) in enumerate(weekly):
        x = gx + (i / max(1, len(weekly) - 1)) * gw
        y = gy + gh - (v / max_v) * (gh - 12)
        pts.append((x, y, v))

    # Build smooth SVG path
    line_d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0, y0, _ = pts[i - 1]
        x1, y1, _ = pts[i]
        mx = (x0 + x1) / 2
        line_d += f" C {mx:.1f} {y0:.1f}, {mx:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}"

    area_d = line_d + f" L {pts[-1][0]:.1f} {gy + gh} L {pts[0][0]:.1f} {gy + gh} Z"
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#00e5ff" filter="url(#cyanGlow)"/>'
        for x, y, v in pts if v > 0
    )

    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="url(#glassBg)" stroke="url(#glassRim)" stroke-width="1.2"/>
  <line x1="24" y1="2" x2="{w-24}" y2="2" stroke="#ffffff" stroke-opacity="0.28" stroke-width="0.9"/>

  <text x="28" y="34" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="1.8" fill="#22d3ee">CONTRIBUTION PULSE // 26 WEEKS</text>
  <text x="812" y="34" text-anchor="end" font-family="{FONT_MONO}" font-size="11" fill="#64748b">CURRENT STREAK: <tspan fill="#e2e8f0">{m['current_streak']}d</tspan></text>

  <line x1="{gx}" y1="{gy + gh}" x2="{gx + gw}" y2="{gy + gh}" stroke="#ffffff" stroke-opacity="0.08" stroke-width="1"/>
  <path d="{area_d}" fill="url(#waveGrad)"/>
  <path d="{line_d}" fill="none" stroke="#00e5ff" stroke-width="2.2" filter="url(#cyanGlow)"/>
  {dots}
</svg>
"""


def build_link_pill(label: str, handle: str, accent: str) -> str:
    w, h = 272, 62
    return f"""<svg fill="none" viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {COMMON_DEFS}
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16" fill="url(#glassBg)" stroke="url(#glassRim)" stroke-width="1.1"/>
  <line x1="18" y1="2" x2="{w-18}" y2="2" stroke="#ffffff" stroke-opacity="0.28" stroke-width="0.9"/>
  <circle cx="24" cy="31" r="4" fill="{accent}" filter="url(#cyanGlow)"/>
  <text x="38" y="28" font-family="{FONT_SANS}" font-size="14" font-weight="600" fill="#f8fafc">{esc(label)}</text>
  <text x="38" y="45" font-family="{FONT_MONO}" font-size="11" fill="#64748b">{esc(handle)}</text>
  <path d="M{w-28} 25 H{w-19} V34 M{w-19} 25 L{w-29} 35" stroke="{accent}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    local_json = sys.argv[1] if len(sys.argv) > 1 else None
    data = fetch_github_data(local_json)
    metrics = compute_metrics(data)

    outputs = {
        "vision-hero.svg": build_hero_svg(),
        "bento-about.svg": build_about_bento(),
        "bento-rings.svg": build_rings_bento(metrics),
        "bento-wave.svg": build_wave_bento(metrics),
        "pill-github.svg": build_link_pill("GitHub", "@NightAI707", "#00e5ff"),
        "pill-linkedin.svg": build_link_pill("LinkedIn", "Night Edge", "#38bdf8"),
        "pill-x.svg": build_link_pill("X", "@NightEdge707", "#a5f3fc"),
    }

    for fname, svg in outputs.items():
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Generated {fname} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
