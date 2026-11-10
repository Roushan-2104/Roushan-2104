"""Render every README card as an animated SVG, in a light and a dark version.

Reads data/contributions.json, data/repos.json, data/portrait-*.txt and the
subset fonts in fonts/, and writes cards/<name>-light.svg and -dark.svg.

GitHub shows README images through <img>, which runs no scripts and loads
nothing external, but does run the SVG's own <style> (CSS keyframes) and SMIL.
So fonts are embedded as base64 WOFF and all motion is CSS or SMIL. Animation
is switched off under prefers-reduced-motion.

    python scripts/render_readme_cards.py            # animated
    STATIC=1 python scripts/render_readme_cards.py   # final frame, for screenshots

Standard library only.
"""
import base64
import json
import os
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

# ---------------------------------------------------------------- content ---
PROFILE = {
    "first": "Roushan",
    "last": "Sharma",
    "status": "B.Tech CSE @ IIIT Bhubaneswar · 2025–29",
    "bio": "Turning ideas into reality.",
}

TILES = [
    {
        "key": "build", "label": "BUILD", "accent": "green",
        "caption": "products & tools",
        "repos": ["Shammy Notch", "Prune", "Internship Alerts",
                  "The Management", "myMoney", "Cooking Ninja"],
        "link_text": "Shammy Notch",
    },
    {
        "key": "ai", "label": "AI", "accent": "orange",
        "caption": "AI-first projects",
        "repos": ["Jeevan Dhara", "Clash of Minds"],
        "link_text": "Jeevan Dhara",
    },
    {
        "key": "create", "label": "CREATE", "accent": "pink",
        "caption": "creative & client sites",
        "repos": ["Lajjha", "ShipZens", "Rechitta",
                  "Urasicous", "Str-atom"],
        "link_text": "Lajjha",
    },
]

FEATURED = {"Shammy-Notch-For-Windows": "Shammy Notch for Windows"}

TECH = [
    ("LANGUAGES", "green", ["C", "C++", "C#", "Python", "JavaScript", "TypeScript", "Dart", "HTML", "CSS"]),
    ("FRONTEND", "orange", ["React", "Next.js", "Vite", "Three.js", "Tailwind", "Bootstrap"]),
    ("BACKEND", "pink", ["Firebase", "Django"]),
    ("TOOLS", "muted", ["Git", "GitHub", "VS Code", "Vercel"]),
]

# (date, title, line 1, line 2, era colour)
JOURNEY = [
    ("JUL 2021", "First webpage", "The World of Games,", "published online", "pink"),
    ("SEP 2021", "First React app", "a Star Wars API", "explorer", "pink"),
    ("OCT 2021", "Hacktoberfest", "plus Ranckin, a JEE", "mentoring site", "pink"),
    ("DEC 2021", "React + Firebase", "Cooking Ninja, myMoney,", "The Management", "pink"),
    ("FEB 2022", "Str-atom", "atoms in pure CSS,", "and my portfolio", "pink"),
    ("JUN–AUG 2025", "Scaler YIIC", "Certificate of", "Excellence", "orange"),
    ("AUG 2025", "IIIT Bhubaneswar", "B.Tech CSE,", "batch of 2025–29", "orange"),
    ("NOV 2025", "Google Cloud", "Compute skill", "badge", "orange"),
    ("JAN 2026", "Clash of Minds", "a local AI debate", "arena on Llama 3.2", "green"),
    ("AUG 2026", "Adobe hackathon", "cleared the DSA +", "SQL online round", "green"),
    ("AUG–SEP 2026", "Rechitta", "a landing page", "for a client", "green"),
    ("OCT 2026", "Lajjha", "real-time 3D jewellery", "in React + Three.js", "green"),
    ("OCT 2026", "Urasicous", "a solar microgrid", "control room", "green"),
    ("OCT 2026", "Prune", "finds hidden gigabytes", "on Android, privately", "green"),
    ("NOV 2026", "ShipZens", "a studio site where", "a 3D bird flies", "green"),
    ("NOV 2026", "Shammy Notch", "a Dynamic Island", "for Windows", "green"),
    ("NOV 2026", "Jeevan Dhara", "voice-first blood finder", "in 11 Indian languages", "green"),
    ("NOW", "What's next?", "let's build", "something together", "ink"),
]

LINKS = [
    {"key": "linkedin", "label": "LINKEDIN", "value": "sroushan2104", "accent": "green", "icon": "in"},
    {"key": "email", "label": "EMAIL", "value": "sroushan2104@gmail.com", "accent": "orange", "icon": "mail"},
    {"key": "x", "label": "X", "value": "@sroushan2104", "accent": "pink", "icon": "x"},
]

# ----------------------------------------------------------------- themes ---
THEMES = {
    "light": {
        "bg": "#F7F2E8", "line": "#E3DACA", "ink": "#1C1A17", "muted": "#6F695E",
        "empty": "#EAE2D3", "bar": "#D9D0BF", "shine": "#FFFFFF", "shine_op": ".55",
        "green": "#1E9E5A", "orange": "#E8681C", "pink": "#D63F7E",
        "pill": "#111111", "pill_text": "#F2EDE3",
    },
    "dark": {
        "bg": "#151413", "line": "#2C2926", "ink": "#F1ECE2", "muted": "#9D978B",
        "empty": "#23211E", "bar": "#3A3632", "shine": "#FFFFFF", "shine_op": ".08",
        "green": "#3FD68A", "orange": "#FF8C42", "pink": "#FF6FAE",
        "pill": "#000000", "pill_text": "#F2EDE3",
    },
}

FONTS = {
    "G7": "grotesk-700.woff",   # Space Grotesk Bold: names, numbers
    "G4": "grotesk-400.woff",   # Space Grotesk Regular: body text
    "M5": "mono-500.woff",      # JetBrains Mono Medium: labels, portrait
}


def font_face(keys):
    css = []
    for k in keys:
        b64 = base64.b64encode((ROOT / "fonts" / FONTS[k]).read_bytes()).decode()
        css.append(f"@font-face{{font-family:{k};src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(css)


BASE_CSS = """
.G7{font-family:G7,'Space Grotesk',sans-serif;font-weight:700}
.G4{font-family:G4,'Space Grotesk',sans-serif}
.M5{font-family:M5,'JetBrains Mono',monospace}
.a{animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.75,.25,1)}
.fb{transform-box:fill-box;transform-origin:center}
.still{display:none}
@keyframes rise{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes show{from{opacity:0}to{opacity:1}}
@keyframes pop{0%{opacity:0;transform:scale(0)}65%{opacity:1;transform:scale(1.3)}100%{opacity:1;transform:scale(1)}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.6)}}
@keyframes ring{0%{opacity:.55;transform:scale(.15)}80%,100%{opacity:0;transform:scale(1.5)}}
@keyframes swing{0%{opacity:0;transform:translateY(150px) rotate(-9deg)}
  55%{opacity:1;transform:translateY(-12px) rotate(2deg)}
  78%{transform:translateY(4px) rotate(-.7deg)}100%{opacity:1;transform:none}}
@keyframes nudge{0%,72%,100%{transform:none}82%{transform:translate(4px,-4px)}91%{transform:none}}
@keyframes sweep{0%{transform:translateX(0)}28%,100%{transform:translateX(520px)}}
@keyframes island{0%{opacity:0;transform:scaleX(.3) scaleY(.7)}60%{opacity:1;transform:scaleX(1.06) scaleY(1.04)}100%{opacity:1;transform:none}}
@keyframes eq{0%,100%{transform:scaleY(.3)}50%{transform:scaleY(1)}}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes type{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
"""

STILL_CSS = "*{animation:none!important}.motion,.frame{display:none}.still{display:inline}"


def svg(w, h, body, fonts, title, defs=""):
    motion = STILL_CSS if STATIC else f"@media (prefers-reduced-motion:reduce){{{STILL_CSS}}}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}" xml:space="preserve">'
        f"<title>{escape(title)}</title>"
        f"<style>{font_face(fonts)}{BASE_CSS}{motion}</style>"
        f"<defs>{defs}</defs>{body}</svg>\n"
    )


def anim(name, delay, dur, extra=""):
    return f'style="animation:{name} {dur}s {delay:.3f}s both{extra}"'


def card_bg(w, h, t, x=0.5, y=0.5, rx=20):
    return (f'<rect x="{x}" y="{y}" width="{w - 2 * x}" height="{h - 2 * y}" rx="{rx}" '
            f'fill="{t["bg"]}" stroke="{t["line"]}"/>')


# ------------------------------------------------------------------- hero ---
def hero(t, theme):
    W, H = 880, 400
    rows = (ROOT / "data" / f"portrait-{theme}.txt").read_text(encoding="utf-8").splitlines()
    fs, lh = 6.4, 7.0
    py0 = (H - len(rows) * lh) / 2 + fs
    # Renderers collapse runs of spaces even with xml:space, so pad with no-break spaces.
    portrait = "".join(
        f'<text x="478" y="{py0 + i * lh:.1f}" class="M5 a" '
        f'{anim("fade", 0.35 + i * 0.018, 0.25)}>{escape(r).replace(" ", chr(0xA0))}</text>'
        for i, r in enumerate(rows)
    )
    defs = (
        f'<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="260" y2="0" '
        f'gradientTransform="translate(-400 0)">'
        f'<stop offset="0" stop-color="{t["ink"]}"/><stop offset=".4" stop-color="{t["ink"]}"/>'
        f'<stop offset=".5" stop-color="{t["green"]}"/><stop offset=".6" stop-color="{t["ink"]}"/>'
        f'<stop offset="1" stop-color="{t["ink"]}"/>'
        + ("" if STATIC else
           '<animateTransform attributeName="gradientTransform" type="translate" '
           'values="-400 0;700 0;700 0" keyTimes="0;.4;1" dur="5s" begin="1.4s" repeatCount="indefinite"/>')
        + "</linearGradient>"
    )
    name = 'font-size="88" letter-spacing="-2.5"'
    body = (
        card_bg(W, H, t)
        + f'<circle cx="47" cy="67" r="5" fill="{t["green"]}" class="fb" '
          f'style="animation:pulse 2s ease-in-out infinite"/>'
        + f'<text x="62" y="72" class="M5 a" font-size="14" fill="{t["muted"]}" {anim("fade", 0.1, 0.6)}>'
          f'{escape(PROFILE["status"])}</text>'
        + f'<text x="38" y="168" class="G7 a" {name} fill="{t["ink"]}" {anim("rise", 0.15, 0.8)}>'
          f'{escape(PROFILE["first"])}</text>'
        + f'<g class="a" {anim("rise", 0.3, 0.8)}>'
          f'<text x="38" y="256" class="G7 motion" {name} fill="url(#shine)">{escape(PROFILE["last"])}</text>'
          f'<text x="38" y="256" class="G7 still" {name} fill="{t["ink"]}">{escape(PROFILE["last"])}</text></g>'
        + f'<text x="41" y="308" class="G4 a" font-size="24" fill="{t["muted"]}" {anim("rise", 0.45, 0.8)}>'
          f'{escape(PROFILE["bio"])}</text>'
        + f'<text x="41" y="352" class="M5 a" font-size="13" letter-spacing="2" {anim("fade", 0.7, 0.8)}>'
          f'<tspan fill="{t["green"]}">BUILD</tspan><tspan fill="{t["muted"]}"> · </tspan>'
          f'<tspan fill="{t["orange"]}">AI</tspan><tspan fill="{t["muted"]}"> · </tspan>'
          f'<tspan fill="{t["pink"]}">CREATE</tspan></text>'
        + f'<g font-size="{fs}" fill="{t["ink"]}" opacity=".88">{portrait}</g>'
    )
    title = f'{PROFILE["first"]} {PROFILE["last"]}: {PROFILE["status"]}. {PROFILE["bio"]}'
    return svg(W, H, body, ["G7", "G4", "M5"], title, defs)


# ---------------------------------------------------------- contributions ---
def load_days():
    data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
    return data, [(date.fromisoformat(d["date"]), d["count"]) for d in data["days"]]


def mix(a, b, f):
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * f):02X}" for x, y in zip(ca, cb))


def heatmap(t, days, total):
    W, H = 880, 236
    nonzero = sorted(c for _, c in days if c)
    q = [nonzero[int(len(nonzero) * p)] for p in (.25, .5, .75)] if nonzero else [1, 2, 3]
    shades = [t["empty"]] + [mix(t["empty"], t["green"], f) for f in (.35, .58, .8, 1)]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > v for v in q)

    first = days[0][0]
    start = first - timedelta(days=(first.weekday() + 1) % 7)   # Sunday on or before
    cell, gap = 12, 3
    cols = (days[-1][0] - start).days // 7 + 1
    x0 = (W - (cols * (cell + gap) - gap)) / 2
    y0 = 92
    rects, months, last_label_x = [], [], -99
    for d, c in days:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        rects.append(
            f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{shades[level(c)]}" '
            f'class="fb a" {anim("pop", 0.45 + col * 0.022 + row * 0.012, 0.45)}/>'
        )
        if d.day <= 7 and row == 0 and x - last_label_x > 40:
            months.append(f'<text x="{x:.1f}" y="{y0 - 12}">{d.strftime("%b")}</text>')
            last_label_x = x
    legend_x = W - x0 - 5 * (cell + gap) + gap
    legend = "".join(
        f'<rect x="{legend_x + i * (cell + gap):.1f}" y="{H - 30}" width="{cell}" height="{cell}" rx="3" fill="{s}"/>'
        for i, s in enumerate(shades)
    )
    body = (
        card_bg(W, H, t)
        + f'<g class="M5" font-size="12" letter-spacing="1.5" fill="{t["muted"]}">'
          f'<text x="{x0:.1f}" y="44" class="a" {anim("fade", 0.3, 0.6)}>CONTRIBUTIONS · LAST 12 MONTHS</text>'
          f'<text x="{W - x0:.1f}" y="44" text-anchor="end" class="a" {anim("fade", 0.3, 0.6)}>'
          f'<tspan fill="{t["green"]}" class="G7" font-size="16" letter-spacing="0">{total}</tspan> CONTRIBUTIONS</text></g>'
        + f'<g class="M5 a" font-size="11" fill="{t["muted"]}" {anim("fade", 0.4, 0.6)}>{"".join(months)}</g>'
        + "".join(rects)
        + f'<g class="a" {anim("fade", 1.6, 0.6)}>'
          f'<text x="{legend_x - 8:.1f}" y="{H - 20}" text-anchor="end" class="M5" font-size="11" fill="{t["muted"]}">less</text>'
          f'{legend}<text x="{legend_x + 5 * (cell + gap) + 5:.1f}" y="{H - 20}" class="M5" font-size="11" '
          f'fill="{t["muted"]}">more</text></g>'
    )
    return svg(W, H, body, ["G7", "M5"], f"{total} contributions in the last 12 months, shown as a calendar heatmap")


def streaks(days):
    counts = [c for _, c in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if counts[i] == 0:          # today may still be empty; the streak is alive until tomorrow
        i -= 1
    current = 0
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    return current, longest


def activity(t, days):
    W, H = 880, 318
    last = days[-1][0]
    months = []
    y, m = last.year, last.month
    for _ in range(12):
        months.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    months.reverse()
    totals = {k: 0 for k in months}
    for d, c in days:
        if (d.year, d.month) in totals:
            totals[(d.year, d.month)] += c
    vals = [totals[k] for k in months]
    best = max(range(12), key=lambda i: vals[i])
    peak = max(vals) or 1
    current, longest = streaks(days)
    busy_d, busy_c = max(days, key=lambda dc: dc[1])

    def days_txt(n):
        return f"{n} day" if n == 1 else f"{n} days"

    stats = [
        ("CURRENT STREAK", days_txt(current)),
        ("LONGEST STREAK", days_txt(longest)),
        ("BUSIEST DAY", f"{busy_c} on {busy_d.day} {busy_d.strftime('%b')}"),
    ]
    stat_svg = "".join(
        f'<g class="a" {anim("rise", 0.9 + i * 0.12, 0.7)}>'
        f'<text x="40" y="{100 + i * 72}" class="M5" font-size="12" letter-spacing="1.5" fill="{t["muted"]}">{label}</text>'
        f'<text x="40" y="{136 + i * 72}" class="G7" font-size="32" letter-spacing="-.5" fill="{t["ink"]}">{escape(v)}</text></g>'
        for i, (label, v) in enumerate(stats)
    )
    bx0, bx1, base, hmax = 340, 840, 262, 168
    slot = (bx1 - bx0) / 12
    bw = 26
    bars = []
    for i, v in enumerate(vals):
        h = max(3, v / peak * hmax)
        x = bx0 + i * slot + (slot - bw) / 2
        fill = t["green"] if i == best else t["bar"]
        bars.append(
            f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="{fill}" '
            f'style="transform-box:fill-box;transform-origin:bottom;animation:grow .7s {1.0 + i * 0.07:.2f}s '
            f'both cubic-bezier(.34,1.5,.6,1)"/>'
        )
        y, m = months[i]
        weight = f'fill="{t["ink"]}"' if i == best else f'fill="{t["muted"]}"'
        bars.append(f'<text x="{x + bw / 2:.1f}" y="{base + 22}" text-anchor="middle" class="M5" '
                    f'font-size="11" {weight}>{date(y, m, 1).strftime("%b")}</text>')
    bh = max(3, vals[best] / peak * hmax)
    bxc = bx0 + best * slot + slot / 2
    bars.append(
        f'<text x="{bxc:.1f}" y="{base - bh - 10:.1f}" text-anchor="middle" class="G7 fb a" font-size="18" '
        f'fill="{t["green"]}" {anim("pop", 1.0 + 12 * 0.07 + 0.3, 0.5)}>{vals[best]}</text>'
    )
    body = (
        card_bg(W, H, t)
        + f'<text x="40" y="44" class="M5 a" font-size="12" letter-spacing="1.5" fill="{t["muted"]}" '
          f'{anim("fade", 0.8, 0.6)}>MONTHLY CONTRIBUTIONS</text>'
        + f'<line x1="{bx0}" y1="{base + .5}" x2="{bx1}" y2="{base + .5}" stroke="{t["line"]}"/>'
        + stat_svg + "".join(bars)
    )
    title = (f"Monthly contributions; best month {date(*months[best], 1).strftime('%B %Y')} with {vals[best]}. "
             f"Current streak {days_txt(current)}, longest {days_txt(longest)}, busiest day {busy_d.isoformat()} with {busy_c}.")
    return svg(W, H, body, ["G7", "M5"], title)


# ------------------------------------------------------------------ tiles ---
def tile(t, spec, index):
    W, H = 300, 330
    accent = t[spec["accent"]]
    n = len(spec["repos"])
    d0 = 1.7 + index * 0.16           # entrance
    c0, cdur = d0 + 0.45, 0.85        # count-up
    step = cdur / max(n, 1)
    frames = "".join(
        f'<text x="30" y="200" class="G7 frame" font-size="140" letter-spacing="-4" fill="{accent}" opacity="0">{k}'
        + ("" if STATIC else f'<set attributeName="opacity" to="1" begin="{c0 + k * step:.3f}s" dur="{step:.3f}s"/>')
        + "</text>"
        for k in range(n)
    )
    clip = f'<clipPath id="c{index}"><rect x="10" y="10" width="280" height="310" rx="20"/></clipPath>'
    body = (
        f'<g class="a" style="transform-box:fill-box;transform-origin:50% 100%;'
        f'animation:swing 1.1s {d0:.2f}s both cubic-bezier(.3,.7,.3,1)">'
        + f'<rect x="10.5" y="10.5" width="279" height="309" rx="20" fill="{t["bg"]}" stroke="{t["line"]}"/>'
        + f'<g clip-path="url(#c{index})">'
          f'<circle cx="290" cy="10" r="90" fill="none" stroke="{accent}" stroke-width="2" class="fb motion" '
          f'style="animation:ring 3.2s {d0 + 1.2:.2f}s ease-out infinite both"/>'
          f'<circle cx="290" cy="10" r="90" fill="none" stroke="{accent}" stroke-width="2" class="fb motion" '
          f'style="animation:ring 3.2s {d0 + 2.8:.2f}s ease-out infinite both"/>'
          f'<g transform="skewX(-18)"><rect x="-110" y="-40" width="70" height="420" fill="{t["shine"]}" '
          f'opacity="{t["shine_op"]}" style="animation:sweep 7s {d0 + 1.6:.2f}s ease-in-out infinite both"/></g></g>'
        + f'<text x="34" y="54" class="M5" font-size="13" letter-spacing="2.5" fill="{accent}">{spec["label"]}</text>'
        + f'<text x="266" y="54" text-anchor="end" class="M5" font-size="12" fill="{t["muted"]}">0{index + 1}</text>'
        + frames
        + f'<text x="30" y="200" class="G7 a" font-size="140" letter-spacing="-4" fill="{accent}" '
          f'style="animation:show .01s {c0 + cdur:.3f}s both">{n}</text>'
        + f'<text x="34" y="240" class="G4" font-size="20" fill="{t["ink"]}">{escape(spec["caption"])}</text>'
        + f'<line x1="34" y1="264.5" x2="266" y2="264.5" stroke="{t["line"]}"/>'
        + f'<text x="34" y="294" class="M5" font-size="13" fill="{t["ink"]}">{escape(spec["link_text"])}</text>'
        + f'<text x="266" y="295" text-anchor="end" class="M5 fb" font-size="16" fill="{accent}" '
          f'style="animation:nudge 2.6s {d0 + 1.4:.2f}s ease-in-out infinite both">↗</text>'
        + "</g>"
    )
    # Repo names stay out of the alt text: some of the counted repos are private.
    title = f'{spec["label"]}: {n} {spec["caption"]}. Opens {spec["link_text"]}.'
    return svg(W, H, body, ["G7", "G4", "M5"], title, clip)


# ------------------------------------------------------------- repo card ---
def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])


def repo_card(t, repo, pretty):
    W = 880
    desc = wrap(repo["description"], 60)
    H = 196 + len(desc) * 25
    d0 = 2.3
    desc_svg = "".join(
        f'<text x="40" y="{132 + i * 25}">{escape(l)}</text>' for i, l in enumerate(desc)
    )
    stats = [s for s in [
        f"{repo['commits']} commits",
        f"{repo['releases']} releases" if repo["releases"] else "",
        f"latest {repo['latest']}" if repo["latest"] else "",
        f"{repo['stars']} star" + ("" if repo["stars"] == 1 else "s"),
    ] if s]
    sy = H - 42
    x = 58 + len(repo["language"]) * 7.8 + 26
    stat_svg = (f'<circle cx="45" cy="{sy - 4.5}" r="5" fill="{repo["language_color"]}"/>'
                f'<text x="58" y="{sy}" fill="{t["ink"]}">{escape(repo["language"])}</text>')
    for s in stats:
        stat_svg += f'<text x="{x:.1f}" y="{sy}">{escape(s)}</text>'
        x += len(s) * 7.8 + 26
    # A small "island" on the right: the project is a Dynamic Island for Windows.
    ix, iy, iw, ih = 612, 92, 228, 58
    eq = "".join(
        f'<rect x="{ix + iw - 74 + i * 10}" y="{iy + 16}" width="5" height="26" rx="2.5" '
        f'fill="{t[c]}" class="fb" style="transform-origin:center;animation:eq {0.7 + i * 0.13:.2f}s '
        f'{d0 + 1 + i * 0.1:.2f}s ease-in-out infinite both"/>'
        for i, c in enumerate(["green", "orange", "pink", "green", "orange"])
    )
    island = (
        f'<g class="fb a" {anim("island", d0 + 0.4, 0.9)}>'
        f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="{ih / 2}" fill="{t["pill"]}" stroke="{t["line"]}"/>'
        f'<circle cx="{ix + 30}" cy="{iy + ih / 2}" r="6" fill="{t["green"]}" class="fb" '
        f'style="animation:pulse 2s ease-in-out infinite"/>'
        f'<text x="{ix + 46}" y="{iy + ih / 2 + 4.5}" class="M5" font-size="13" fill="{t["pill_text"]}">'
        f'{escape(repo["latest"] or "live")}</text>{eq}</g>'
    )
    body = (
        f'<g class="a" {anim("rise", d0, 0.8)}>' + card_bg(W, H, t)
        + f'<text x="40" y="50" class="M5" font-size="12" letter-spacing="1.5" fill="{t["muted"]}">FEATURED REPO</text>'
        + f'<text x="840" y="50" text-anchor="end" class="M5" font-size="12" fill="{t["muted"]}">'
          f'Roushan-2104/{escape(repo["name"])} <tspan fill="{t["green"]}">↗</tspan></text>'
        + f'<text x="38" y="98" class="G7" font-size="36" letter-spacing="-1" fill="{t["ink"]}">{escape(pretty)}</text>'
        + f'<g class="G4" font-size="17" fill="{t["muted"]}">{desc_svg}</g>'
        + f'<line x1="40" y1="{sy - 30.5}" x2="840" y2="{sy - 30.5}" stroke="{t["line"]}"/>'
        + f'<g class="M5" font-size="13" fill="{t["muted"]}">{stat_svg}</g>'
        + island + "</g>"
    )
    title = f'{pretty}: {repo["description"]} {repo["language"]}, ' + ", ".join(stats) + "."
    return svg(W, H, body, ["G7", "G4", "M5"], title)


# ----------------------------------------------------------- now building ---
def building_card(t, b):
    W, H = 880, 96
    msg = b["message"]
    if len(msg) > 58:
        msg = msg[:55].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    when = date.fromisoformat(b["date"][:10])
    fs, cw, tx, d0 = 12, 7.2, 340, 0.7
    n = len(msg) + 2                     # "> " prompt
    dur = round(n * 0.035, 2)
    end = n * cw
    defs = (f'<clipPath id="typed"><rect x="{tx}" y="30" width="{end + 2:.1f}" height="34" '
            f'style="transform-box:fill-box;transform-origin:left;animation:type {dur}s {d0 + .5}s steps({n}) both"/>'
            f'</clipPath>')
    body = (
        f'<style>@keyframes caret{{from{{transform:translateX(-{end:.1f}px)}}to{{transform:none}}}}</style>'
        + f'<g class="a" {anim("rise", d0, 0.7)}>' + card_bg(W, H, t)
        + f'<circle cx="34" cy="48" r="5" fill="{t["green"]}" class="fb" style="animation:pulse 2s ease-in-out infinite"/>'
        + f'<text x="50" y="40" class="M5" font-size="11" letter-spacing="1.8" fill="{t["muted"]}">NOW BUILDING</text>'
        + f'<text x="50" y="66" class="G7" font-size="18" letter-spacing="-.3" fill="{t["ink"]}">{escape(b["repo"])}</text>'
        + f'<line x1="318.5" y1="26" x2="318.5" y2="70" stroke="{t["line"]}"/>'
        + f'<text x="{tx}" y="52" class="M5" font-size="{fs}" clip-path="url(#typed)">'
          f'<tspan fill="{t["green"]}">&gt; </tspan><tspan fill="{t["ink"]}">{escape(msg)}</tspan></text>'
        + f'<rect x="{tx + end + 1:.1f}" y="41" width="7" height="14" fill="{t["green"]}" '
          f'style="animation:caret {dur}s {d0 + .5}s steps({n}) both, blink 1.1s {d0 + .5 + dur:.2f}s infinite"/>'
        + f'<text x="848" y="52" text-anchor="end" class="M5" font-size="12" fill="{t["muted"]}">'
          f'{when.day} {when.strftime("%b")}</text>'
        + "</g>"
    )
    return svg(W, H, body, ["G7", "M5"], f'Now building {b["repo"]}: {b["message"]}', defs)


# ------------------------------------------------------------- tech stack ---
def chip_w(s):
    return len(s) * 7.0 + 34


def tech_layout():
    """Rows of chips per group; returns (height, placed chips)."""
    x0, x1, y, placed = 124, 516, 70, []
    for label, accent, items in TECH:
        x, first = x0, True
        for item in items:
            w = chip_w(item)
            if x + w > x1:
                x, y = x0, y + 36
            placed.append((label if first else None, accent, item, x, y, w))
            first = False
            x += w + 8
        y += 44
    return y + 4, placed


def tech_card(t, H, placed):
    W = 540
    chips = []
    for k, (label, accent, item, x, y, w) in enumerate(placed):
        color = t[accent]
        if label:
            chips.append(f'<text x="32" y="{y + 18.5}" class="M5 a" font-size="10.5" letter-spacing="1.6" '
                         f'fill="{color}" {anim("fade", 0.5 + k * 0.04, 0.5)}>{label}</text>')
        chips.append(
            f'<g class="fb a" {anim("pop", 0.6 + k * 0.045, 0.45)}>'
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="28" rx="14" fill="{t["empty"]}"/>'
            f'<circle cx="{x + 14:.1f}" cy="{y + 14}" r="4" fill="{color}"/>'
            f'<text x="{x + 24:.1f}" y="{y + 18.5}" class="G4" font-size="13" fill="{t["ink"]}">{escape(item)}</text></g>'
        )
    count = sum(len(items) for _, _, items in TECH)
    body = (
        card_bg(W, H, t)
        + f'<text x="32" y="44" class="M5 a" font-size="12" letter-spacing="1.5" fill="{t["muted"]}" '
          f'{anim("fade", 0.4, 0.6)}>TECH STACK</text>'
        + f'<text x="508" y="44" text-anchor="end" class="M5 a" font-size="12" fill="{t["muted"]}" '
          f'{anim("fade", 0.4, 0.6)}>{count} tools</text>'
        + "".join(chips)
    )
    title = "Tech stack. " + " ".join(f"{label.title()}: {', '.join(items)}." for label, _, items in TECH)
    return svg(W, H, body, ["G4", "M5"], title)


# --------------------------------------------------------- language ring ---
def ring_card(t, H, langs):
    W = 330
    counts = list(langs["counts"].items())
    top, rest = counts[:5], sum(c for _, c in counts[5:])
    if rest:
        top.append(("Other", rest))
    total = sum(c for _, c in top)
    colors = [t["green"], t["orange"], t["pink"], t["ink"], t["muted"], t["bar"]]
    cx, cy, r = 98, H / 2 + 14, 62
    segs, start = [], 0.0
    for i, (_, c) in enumerate(top):
        pct = c / total * 100
        segs.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colors[i]}" stroke-width="20" '
                    f'pathLength="100" stroke-dasharray="{max(pct - 0.8, 0.4):.2f} 100" '
                    f'stroke-dashoffset="{-start:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        start += pct
    mask = (f'<mask id="sweep"><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-width="24" '
            f'pathLength="1" stroke-dasharray="1 1" transform="rotate(-90 {cx} {cy})" '
            f'style="animation:draw 1.3s .9s both cubic-bezier(.5,0,.2,1)"/></mask>')
    ly = cy - len(top) * 24 / 2 + 12
    legend = "".join(
        f'<g class="a" {anim("rise", 1.0 + i * 0.1, 0.5)}>'
        f'<rect x="186" y="{ly + i * 24 - 9:.1f}" width="10" height="10" rx="3" fill="{colors[i]}"/>'
        f'<text x="202" y="{ly + i * 24:.1f}" class="M5" font-size="12" fill="{t["ink"]}">{escape(name)}</text>'
        f'<text x="308" y="{ly + i * 24:.1f}" text-anchor="end" class="M5" font-size="12" fill="{t["muted"]}">{c}</text></g>'
        for i, (name, c) in enumerate(top)
    )
    body = (
        card_bg(W, H, t)
        + f'<text x="28" y="44" class="M5 a" font-size="12" letter-spacing="1.5" fill="{t["muted"]}" '
          f'{anim("fade", 0.6, 0.6)}>LANGUAGES · BY REPO</text>'
        + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["empty"]}" stroke-width="20"/>'
        + f'<g mask="url(#sweep)">{"".join(segs)}</g>'
        + f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" class="G7 a" font-size="30" letter-spacing="-1" '
          f'fill="{t["ink"]}" {anim("fade", 1.4, 0.6)}>{total}</text>'
        + f'<text x="{cx}" y="{cy + 24}" text-anchor="middle" class="M5 a" font-size="10" letter-spacing="1.2" '
          f'fill="{t["muted"]}" {anim("fade", 1.5, 0.6)}>REPOS</text>'
        + legend
    )
    title = f"Main language of {total} public repos: " + ", ".join(f"{n} {c}" for n, c in top) + "."
    return svg(W, H, body, ["G7", "M5"], title, mask)


# ---------------------------------------------------------------- journey ---
def journey_card(t):
    W, per, colw, x0 = 880, 5, 160, 44
    rows = [JOURNEY[i:i + per] for i in range(0, len(JOURNEY), per)]
    H = 104 + len(rows) * 128 - 14
    parts = [card_bg(W, H, t),
             f'<text x="40" y="44" class="M5 a" font-size="12" letter-spacing="1.5" fill="{t["muted"]}" '
             f'{anim("fade", 0.3, 0.6)}>JOURNEY · 2021 → NOW</text>']
    for ri, row in enumerate(rows):
        ry = 104 + ri * 128
        rd = 0.5 + ri * 0.9
        x_end = x0 + (len(row) - 1) * colw + 6 if ri == len(rows) - 1 else 840
        parts.append(f'<line x1="{x0}" y1="{ry}" x2="{x_end}" y2="{ry}" stroke="{t["line"]}" stroke-width="2" '
                     f'pathLength="1" stroke-dasharray="1 1" style="animation:draw .9s {rd:.2f}s both ease-out"/>')
        for ci, (when, title, l1, l2, era) in enumerate(row):
            x = x0 + ci * colw
            d = rd + ci * 0.16
            color = t[era]
            last = ri == len(rows) - 1 and ci == len(row) - 1
            dot = f'<circle cx="{x + 6}" cy="{ry}" r="6" fill="{color}" class="fb a" {anim("pop", d, 0.45)}/>'
            if last:
                dot += (f'<circle cx="{x + 6}" cy="{ry}" r="12" fill="none" stroke="{color}" stroke-width="1.5" '
                        f'class="fb motion" style="animation:ring 2.4s {d + .5:.2f}s ease-out infinite both"/>')
            parts.append(
                dot
                + f'<g class="a" {anim("rise", d + 0.08, 0.6)}>'
                f'<text x="{x}" y="{ry - 16}" class="M5" font-size="11" letter-spacing="1.2" fill="{color}">{escape(when)}</text>'
                f'<text x="{x}" y="{ry + 30}" class="G7" font-size="15" letter-spacing="-.2" fill="{t["ink"]}">{escape(title)}</text>'
                f'<text x="{x}" y="{ry + 50}" class="G4" font-size="12.5" fill="{t["muted"]}">{escape(l1)}</text>'
                f'<text x="{x}" y="{ry + 67}" class="G4" font-size="12.5" fill="{t["muted"]}">{escape(l2)}</text></g>'
            )
    title = "Journey: " + "; ".join(f"{w} {ti}, {a} {b}" for w, ti, a, b, _ in JOURNEY) + "."
    return svg(W, H, "".join(parts), ["G7", "G4", "M5"], title)


# ------------------------------------------------------------- link pills ---
def link_icon(kind, x, y, color):
    if kind == "in":
        return (f'<text x="{x + 20}" y="{y + 27}" text-anchor="middle" class="G7" font-size="19" '
                f'letter-spacing="-.5" fill="{color}">in</text>')
    if kind == "mail":
        return (f'<g fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">'
                f'<rect x="{x + 10}" y="{y + 12}" width="20" height="16" rx="3"/>'
                f'<path d="M{x + 11} {y + 14} L{x + 20} {y + 21} L{x + 29} {y + 14}"/></g>')
    return (f'<path d="M{x + 12} {y + 12} L{x + 28} {y + 28} M{x + 28} {y + 12} L{x + 12} {y + 28}" '
            f'stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>')


def link_pill(t, spec, index):
    W, H = 290, 68
    accent = t[spec["accent"]]
    d0 = 0.55 + index * 0.12
    clip = f'<clipPath id="p{index}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{(H - 2) / 2}"/></clipPath>'
    body = (
        f'<g class="a" {anim("rise", d0, 0.7)}>'
        + f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{(H - 1) / 2}" fill="{t["bg"]}" stroke="{t["line"]}"/>'
        + f'<g clip-path="url(#p{index})"><g transform="skewX(-18)">'
          f'<rect x="-90" y="-10" width="46" height="90" fill="{t["shine"]}" opacity="{t["shine_op"]}" class="motion" '
          f'style="animation:sweep 6s {d0 + 1.2 + index * 0.4:.2f}s ease-in-out infinite both"/></g></g>'
        + f'<g class="fb a" {anim("pop", d0 + 0.25, 0.5)}>'
          f'<rect x="14" y="14" width="40" height="40" rx="20" fill="{accent}"/>'
          f'{link_icon(spec["icon"], 14, 14, t["bg"])}</g>'
        + f'<text x="68" y="30" class="M5" font-size="11" letter-spacing="1.8" fill="{accent}">{spec["label"]}</text>'
        + f'<text x="68" y="50" class="G4" font-size="{15 if len(spec["value"]) <= 16 else 13.5}" '
          f'fill="{t["ink"]}">{escape(spec["value"])}</text>'
        + f'<text x="{W - 22}" y="40" text-anchor="end" class="M5 fb" font-size="15" fill="{accent}" '
          f'style="animation:nudge 2.6s {d0 + 1:.2f}s ease-in-out infinite both">↗</text>'
        + "</g>"
    )
    return svg(W, H, body, ["G4", "G7", "M5"], f'{spec["label"].title()}: {spec["value"]}', clip)


# ------------------------------------------------------------------- main ---
def main():
    OUT.mkdir(exist_ok=True)
    data, days = load_days()
    repos = json.loads((ROOT / "data" / "repos.json").read_text(encoding="utf-8"))
    langs = json.loads((ROOT / "data" / "languages.json").read_text(encoding="utf-8"))
    building = json.loads((ROOT / "data" / "building.json").read_text(encoding="utf-8"))
    stack_h, placed = tech_layout()
    for theme, t in THEMES.items():
        cards = {
            "hero": hero(t, theme),
            "heatmap": heatmap(t, days, data["total"]),
            "activity": activity(t, days),
        }
        for i, spec in enumerate(TILES):
            cards[spec["key"]] = tile(t, spec, i)
        for name, pretty in FEATURED.items():
            cards[f"repo-{name.lower()}"] = repo_card(t, repos[name], pretty)
        for i, spec in enumerate(LINKS):
            cards[f"link-{spec['key']}"] = link_pill(t, spec, i)
        if building:
            cards["building"] = building_card(t, building)
        cards["stack"] = tech_card(t, stack_h, placed)
        cards["languages"] = ring_card(t, stack_h, langs)
        cards["journey"] = journey_card(t)
        for name, text in cards.items():
            (OUT / f"{name}-{theme}.svg").write_text(text, encoding="utf-8", newline="\n")
    print(f"rendered {len(cards) * len(THEMES)} cards into cards/" + (" (static)" if STATIC else ""))


if __name__ == "__main__":
    main()
