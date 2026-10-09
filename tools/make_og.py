#!/usr/bin/env python3
"""
Generates the social share images (Open Graph, 1200x630) in src/assets/og/ using headless Chrome.
Re-run after adding a page or changing a headline:

    python3 tools/make_og.py

build.py uses src/assets/og/<slug>.jpg when it exists (slug "home" for /), otherwise home.jpg.
"""
import json
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = SRC / "assets" / "og"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# slug: (kicker, headline, optional channel logo in src/assets/integrations/)
PAGES = {
    "home": ("Ecommerce fulfillment & 3PL", "A full-service shipping department for growing brands", None),
    "utah-fulfillment-center": ("Springville, Utah", "Utah fulfillment center & ecommerce 3PL", None),
    "florida-fulfillment-center": ("Jacksonville, Florida", "Florida fulfillment center & ecommerce 3PL", None),
    "services": ("3PL services", "Pick, pack & ship, storage, kitting and B2B", None),
    "integrations": ("65+ integrations", "Connect Shopify, Amazon, Walmart, TikTok Shop & more", None),
    "about": ("About Boxio", "Fulfillment partner designed for growth", None),
    "request-a-quote": ("Free quote", "Get a free 3PL fulfillment quote", None),
    "contact": ("Contact", "Talk to the Boxio fulfillment team", None),
    "shopify-fulfillment": ("Shopify fulfillment", "Shopify fulfillment from Utah & Florida", "shopify.webp"),
    "amazon-fulfillment": ("Amazon fulfillment", "Amazon FBA prep & FBM fulfillment", "amazon.webp"),
    "walmart-fulfillment": ("Walmart fulfillment", "Walmart Marketplace fulfillment", "walmart.webp"),
    "tiktok-shop-fulfillment": ("TikTok Shop fulfillment", "TikTok Shop fulfillment, built for viral", "tiktok-shop.webp"),
    "b2b-fulfillment": ("B2B fulfillment", "B2B & wholesale fulfillment from one inventory", None),
    "what-is-a-3pl": ("3PL guide", "What is a 3PL? Ecommerce fulfillment explained", None),
    "3pl-pricing": ("3PL guide", "3PL pricing explained: what fulfillment really costs", None),
    "3pl-vs-in-house-fulfillment": ("3PL guide", "3PL vs. in-house fulfillment: when to outsource", None),
}

# Warehouse pins in the 975x610 Albers frame of src/assets/us-states.json
HUBS = {"Springville": (230.5, 249.4), "Jacksonville": (774.6, 475.6)}


def page_html(kicker, headline, logo, states):
    paths = "".join(f'<path d="{s["d"]}" class="{"hub" if s["id"] in ("UT", "FL") else ""}"/>' for s in states)
    (x1, y1), (x2, y2) = HUBS["Springville"], HUBS["Jacksonville"]
    link = f"M{x1},{y1} Q{(x1 + x2) / 2},{(y1 + y2) / 2 - 220} {x2},{y2}"
    pins = "".join(f'<g transform="translate({x} {y})"><circle r="40" class="glow"/><circle r="15" class="halo"/><circle r="7" class="dot"/></g>' for x, y in HUBS.values())
    badge = f'<div class="badge"><img src="integrations/{logo}"></div>' if logo else ""
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Manrope; font-weight: 600 800; src: url('fonts/manrope-latin.woff2') format('woff2'); }}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{ font-family: Manrope, sans-serif; color: #fff; position: relative;
  background: radial-gradient(700px 520px at 85% 40%, #3b3577 0%, transparent 70%), #1b1836; }}
body::before {{ content: ""; position: absolute; inset: 0; background-image: radial-gradient(rgba(255,255,255,.07) 1.3px, transparent 1.5px); background-size: 26px 26px; }}
.logo {{ position: absolute; left: 72px; top: 64px; width: 210px; }}
.text {{ position: absolute; left: 72px; top: 200px; width: 640px; }}
.kicker {{ font-size: 24px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #b4adff; display: flex; align-items: center; gap: 14px; }}
.kicker::before {{ content: ""; width: 30px; height: 3px; background: #b4adff; }}
h1 {{ font-size: 60px; line-height: 1.08; letter-spacing: -.03em; font-weight: 800; margin: 22px 0 0; }}
.url {{ position: absolute; left: 72px; bottom: 58px; font-size: 24px; font-weight: 700; color: #c9c5e6; }}
svg {{ position: absolute; right: -40px; top: 150px; width: 560px; opacity: .95; }}
.states path {{ fill: #2f2a5c; stroke: #1b1836; stroke-width: 1.5; }} .states path.hub {{ fill: #8f86f0; }}
.link {{ fill: none; stroke: rgba(255,255,255,.6); stroke-width: 3; stroke-dasharray: 3 10; stroke-linecap: round; }}
.glow {{ fill: rgba(143,134,240,.25); }} .halo {{ fill: #8f86f0; }} .dot {{ fill: #fff; }}
.badge {{ position: absolute; right: 72px; top: 56px; width: 92px; height: 92px; border-radius: 22px; background: #fff; display: grid; place-items: center; box-shadow: 0 10px 30px rgba(0,0,0,.35); }}
.badge img {{ width: 72px; height: 72px; object-fit: contain; }}
</style></head><body>
<img class="logo" src="brand/logo-white.png">
{badge}
<div class="text"><div class="kicker">{escape(kicker)}</div><h1>{escape(headline)}</h1></div>
<svg viewBox="0 0 975 610" xmlns="http://www.w3.org/2000/svg"><g class="states">{paths}</g><path class="link" d="{link}"/>{pins}</svg>
<div class="url">boxioship.com</div>
</body></html>'''


def main():
    states = json.loads((SRC / "assets" / "us-states.json").read_text())["states"]
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for sub in ("fonts", "brand", "integrations"):
            shutil.copytree(SRC / "assets" / sub, tmp / sub)
        for slug, (kicker, headline, logo) in PAGES.items():
            page = tmp / f"{slug}.html"
            page.write_text(page_html(kicker, headline, logo, states))
            png = tmp / f"{slug}.png"
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1200,630",
                            "--virtual-time-budget=4000", f"--screenshot={png}", f"file://{page}"],
                           check=True, capture_output=True)
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "86", str(png), "--out", str(OUT / f"{slug}.jpg")],
                           check=True, capture_output=True)
            print(f"og/{slug}.jpg")


if __name__ == "__main__":
    main()
