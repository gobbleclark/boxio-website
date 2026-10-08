#!/usr/bin/env python3
"""
Builds the Boxio website into ./dist as plain static HTML.

    python3 build.py

Edit business details in CONFIG below — every page, the footer, structured data (schema.org)
and the sitemap pull from here, so name/address/phone stay identical everywhere (important for local SEO).
Page content lives in src/pages/*.html.
"""
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

# ---------------------------------------------------------------------------
# Business details
# ---------------------------------------------------------------------------
CONFIG = {
    "site_url": "https://www.boxioship.com",
    "brand": "Boxio",
    "legal_name": "Boxio LLC",
    "email": "hello@boxioship.com",
    "locations": {
        "ut": {
            "name": "Boxio Fulfillment — Utah",
            "label": "Utah",
            "street": "2111 W Center Street, Unit 4",
            "city": "Springville",
            "state": "UT",
            "state_name": "Utah",
            "zip": "84663",
            "phone": "(801) 960-4373",
            "path": "/utah-fulfillment-center/",
            # Approximate; used only for the transit-time map estimates.
            "coords": [40.165, -111.64],
        },
        "fl": {
            # TODO: replace every [bracketed] value with the real Florida details.
            "name": "Boxio Fulfillment — Florida",
            "label": "Florida",
            "street": "[Florida street address]",
            "city": "[City]",
            "state": "FL",
            "state_name": "Florida",
            "zip": "[ZIP]",
            "phone": "[Florida phone]",
            "path": "/florida-fulfillment-center/",
            "coords": [28.5, -81.4],  # TODO: set to the warehouse's lat/lng
        },
    },
    "integrations": {
        "store": ["Shopify", "WooCommerce", "BigCommerce", "Magento", "Squarespace", "Volusion", "QuickBooks Commerce"],
        "market": ["Amazon", "Walmart", "eBay", "Etsy", "Wayfair", "Overstock", "Google Shopping"],
        "shipping": ["ShipStation", "UPS", "FedEx", "USPS", "DHL", "FirstMile", "Asendia"],
    },
}

# ---------------------------------------------------------------------------
# Pages: (output path, source file, title, meta description, breadcrumb label)
# ---------------------------------------------------------------------------
PAGES = [
    ("/", "home.html",
     "Ecommerce Fulfillment & 3PL in Utah and Florida | Boxio",
     "Boxio is a tech-enabled 3PL with fulfillment centers in Springville, Utah and Florida. Fast pick, pack & ship, real-time inventory and 99.99% order accuracy. Get a free quote.",
     None),
    ("/utah-fulfillment-center/", "utah.html",
     "Utah Fulfillment Center & 3PL in Springville, UT | Boxio",
     "Ecommerce fulfillment in Utah from Boxio's Springville warehouse off I-15. Pick, pack & ship, storage, kitting and B2B for brands across Utah and the West. Free quote.",
     "Utah Fulfillment Center"),
    ("/florida-fulfillment-center/", "florida.html",
     "Florida Fulfillment Center & 3PL | Boxio Ecommerce Fulfillment",
     "Ecommerce fulfillment in Florida from Boxio. Reach Southeast and East Coast customers faster with pick, pack & ship, storage, kitting and retail distribution. Free quote.",
     "Florida Fulfillment Center"),
    ("/services/", "services.html",
     "Ecommerce Fulfillment Services | Pick, Pack, Ship & Storage | Boxio",
     "Order fulfillment, warehousing, inventory management, kitting & bundling, B2B retail distribution, dropshipping and 2-day shipping from Utah and Florida.",
     "Services"),
    ("/integrations/", "integrations.html",
     "Shopify, Amazon & Walmart Fulfillment Integrations | Boxio",
     "Connect Shopify, WooCommerce, Amazon, Walmart, BigCommerce, Etsy, eBay and more to Boxio fulfillment. Ship with UPS, FedEx, USPS and DHL. Custom API available.",
     "Integrations"),
    ("/about/", "about.html",
     "About Boxio | Tech-Enabled 3PL in Utah & Florida",
     "Boxio is a tech-enabled third-party logistics company helping growing ecommerce brands ship faster from Utah and Florida with 99.99% order accuracy.",
     "About"),
    ("/request-a-quote/", "quote.html",
     "Get a Free Fulfillment Quote | Boxio 3PL",
     "Tell us about your orders and get a free, custom ecommerce fulfillment quote from Boxio's Utah and Florida warehouses. Reply within one business day.",
     "Free Quote"),
    ("/contact/", "contact.html",
     "Contact Boxio | Utah & Florida Fulfillment Centers",
     "Contact Boxio fulfillment. Call, email or send a message to our Springville, Utah or Florida warehouse team.",
     "Contact"),
]

# Old URLs on the current site -> new URLs (301). Written to _redirects and .htaccess.
REDIRECTS = {
    "/shipping-supply-chain-product/": "/services/",
    "/partner-request/": "/contact/",
}

# ---------------------------------------------------------------------------
# FAQ content — rendered as accordions AND FAQPage schema from the same source
# ---------------------------------------------------------------------------
FAQS = {
    "home": [
        ("What does Boxio do?",
         "Boxio is a tech-enabled third-party logistics (3PL) company. We store your inventory and pick, pack and ship your ecommerce orders on your behalf, with real-time inventory tracking and integrations for the platforms you already sell on."),
        ("Where are Boxio's fulfillment centers?",
         "We have fulfillment centers in Springville, Utah ({{ut_full}}) and in Florida ({{fl_full}}). Shipping from the location closest to your customers shortens transit times and can lower shipping costs."),
        ("Should I ship from Utah, Florida, or both?",
         "Utah is well placed for customers in the West, Mountain West and Southwest. Florida is well placed for the Southeast and East Coast. Use the shipping map on this page to compare, or request a quote and we'll recommend a setup based on where your customers are."),
        ("Which ecommerce platforms do you integrate with?",
         "Shopify, WooCommerce, BigCommerce, Magento, Squarespace, Amazon, Walmart, eBay, Etsy, Wayfair, Google Shopping, ShipStation and more. We also offer API integrations for custom builds."),
        ("How much does ecommerce fulfillment cost?",
         "Pricing depends on your monthly order volume, number of SKUs, storage needs and packaging. Request a free quote and we'll build pricing around your business."),
    ],
    "utah": [
        ("Where is Boxio's Utah fulfillment center?",
         "Our Utah warehouse is at {{ut_full}}, in Utah County just off I-15, about an hour south of Salt Lake City."),
        ("Why use a Utah 3PL?",
         "Utah sits in the middle of the western United States, so ground shipments reach the West Coast, Mountain West and Southwest quickly. That makes it a strong home base for brands with customers across the West."),
        ("Do you work with Utah-based ecommerce brands?",
         "Yes. We work with brands across Utah County, Salt Lake County and the rest of the state, along with brands nationwide. Local brands can talk with our team in person."),
        ("What services are available at the Utah warehouse?",
         "Order fulfillment (pick, pack and ship), inventory storage, real-time inventory management, kitting and bundling, B2B and retail distribution, retail dropshipping, and 2-day express and international shipping."),
    ],
    "florida": [
        ("Where is Boxio's Florida fulfillment center?",
         "Our Florida warehouse is at {{fl_full}}."),
        ("Why use a Florida 3PL?",
         "Florida puts your inventory close to the fast-growing Southeast and within ground reach of the East Coast. Florida's major ports and airports also make it a natural gateway for international orders."),
        ("Can I use both the Utah and Florida warehouses?",
         "Yes. Pairing Utah with Florida puts inventory on both sides of the country, which can shorten transit times for customers coast to coast. We'll help you decide what makes sense for your volume."),
        ("What services are available at the Florida warehouse?",
         "Order fulfillment (pick, pack and ship), inventory storage, real-time inventory management, kitting and bundling, B2B and retail distribution, retail dropshipping, and 2-day express and international shipping."),
    ],
}

# ---------------------------------------------------------------------------
# Icons (inline SVG)
# ---------------------------------------------------------------------------
_s = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
ICONS = {
    "box": f'<svg {_s}><path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/></svg>',
    "scan": f'<svg {_s}><path d="M3 7V5a2 2 0 012-2h2M17 3h2a2 2 0 012 2v2M21 17v2a2 2 0 01-2 2h-2M7 21H5a2 2 0 01-2-2v-2"/><path d="M7 8v8M11 8v8M15 8v8M18 8v8"/></svg>',
    "chart": f'<svg {_s}><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 6-6"/></svg>',
    "layers": f'<svg {_s}><path d="M12 2l10 5-10 5L2 7l10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
    "store": f'<svg {_s}><path d="M3 9l1.5-5h15L21 9"/><path d="M4 9v11h16V9"/><path d="M3 9a3 3 0 006 0 3 3 0 006 0 3 3 0 006 0"/><path d="M10 20v-5h4v5"/></svg>',
    "truck": f'<svg {_s}><path d="M1 4h14v12H1z"/><path d="M15 9h4l3 3v4h-7"/><circle cx="6" cy="18.5" r="2"/><circle cx="18" cy="18.5" r="2"/></svg>',
    "globe": f'<svg {_s}><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 010 20M12 2a15 15 0 000 20"/></svg>',
    "plug": f'<svg {_s}><path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 01-12 0V8z"/><path d="M12 18v4"/></svg>',
    "pin": f'<svg {_s}><path d="M12 22s-8-7.5-8-13a8 8 0 0116 0c0 5.5-8 13-8 13z"/><circle cx="12" cy="9" r="3"/></svg>',
    "phone": f'<svg {_s}><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h3a2 2 0 012 1.7c.1 1 .4 1.9.7 2.8a2 2 0 01-.5 2.1L8 9.9a16 16 0 006 6l1.3-1.3a2 2 0 012.1-.4c.9.3 1.8.6 2.8.7a2 2 0 011.7 2z"/></svg>',
    "mail": f'<svg {_s}><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/></svg>',
    "shield": f'<svg {_s}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>',
    "code": f'<svg {_s}><path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/></svg>',
    "bolt": f'<svg {_s}><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    "arrow": f'<svg {_s}><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "search": f'<svg {_s}><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
    "chat": f'<svg {_s}><path d="M21 12a8 8 0 01-11.6 7.1L3 21l1.9-6.4A8 8 0 1121 12z"/></svg>',
}

LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="10" fill="#fe4608"/>'
        '<path d="M20 9l10 5.5v11L20 31l-10-5.5v-11L20 9z" fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/>'
        '<path d="M10 14.5L20 20l10-5.5M20 20v11" fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/></svg>')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def loc_tokens():
    t = {}
    for key, L in CONFIG["locations"].items():
        tel = "+1" + re.sub(r"\D", "", L["phone"]) if re.search(r"\d", L["phone"]) else ""
        full = f'{L["street"]}, {L["city"]}, {L["state"]} {L["zip"]}'
        t.update({
            f"{key}_name": L["name"], f"{key}_label": L["label"], f"{key}_street": L["street"], f"{key}_city": L["city"],
            f"{key}_state": L["state"], f"{key}_zip": L["zip"], f"{key}_phone": L["phone"], f"{key}_tel": tel,
            f"{key}_full": full, f"{key}_path": L["path"],
            f"{key}_maps": "https://www.google.com/maps/search/?api=1&query=" + full.replace(" ", "+").replace(",", "%2C"),
            f"{key}_embed": "https://www.google.com/maps?q=" + full.replace(" ", "+").replace(",", "%2C") + "&output=embed",
        })
    t["email"] = CONFIG["email"]
    t["brand"] = CONFIG["brand"]
    t["year"] = str(date.today().year)
    t["hubs_json"] = escape(json.dumps([
        {"key": k, "label": L["label"], "state": L["state"], "coords": L["coords"]} for k, L in CONFIG["locations"].items()
    ]))
    return t


TOKENS = loc_tokens()


def fill(text):
    text = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: ICONS[m.group(1)], text)
    for k, v in TOKENS.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def faq_html(key):
    items = "".join(
        f'<details><summary>{escape(q)}</summary><div class="answer"><p>{escape(fill(a))}</p></div></details>'
        for q, a in FAQS[key]
    )
    return f'<div class="faq">{items}</div>'


def faq_schema(key):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": fill(a)}}
            for q, a in FAQS[key]
        ],
    }


def local_business(key):
    L = CONFIG["locations"][key]
    url = CONFIG["site_url"] + L["path"]
    lb = {
        "@type": "LocalBusiness",
        "@id": url + "#business",
        "name": L["name"],
        "url": url,
        "email": CONFIG["email"],
        "telephone": TOKENS[f"{key}_tel"] or None,
        "image": CONFIG["site_url"] + "/assets/logo.svg",
        "priceRange": "$$",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": L["street"],
            "addressLocality": L["city"],
            "addressRegion": L["state"],
            "postalCode": L["zip"],
            "addressCountry": "US",
        },
        "areaServed": [{"@type": "State", "name": L["state_name"]}, {"@type": "Country", "name": "United States"}],
        "parentOrganization": {"@id": CONFIG["site_url"] + "/#organization"},
        "description": f"Ecommerce order fulfillment and third-party logistics (3PL) warehouse in {L['city']}, {L['state_name']}.",
        "hasMap": TOKENS[f"{key}_maps"],
    }
    return {k: v for k, v in lb.items() if v}


def organization():
    return {
        "@type": "Organization",
        "@id": CONFIG["site_url"] + "/#organization",
        "name": CONFIG["brand"],
        "legalName": CONFIG["legal_name"],
        "url": CONFIG["site_url"] + "/",
        "logo": CONFIG["site_url"] + "/assets/logo.svg",
        "email": CONFIG["email"],
        "telephone": TOKENS["ut_tel"],
        "description": "Tech-enabled third-party logistics (3PL) and ecommerce fulfillment with warehouses in Utah and Florida.",
        "department": [{"@id": CONFIG["site_url"] + L["path"] + "#business"} for L in CONFIG["locations"].values()],
        "contactPoint": {"@type": "ContactPoint", "contactType": "sales", "telephone": TOKENS["ut_tel"], "email": CONFIG["email"], "areaServed": "US"},
    }


def breadcrumb(path, label):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": CONFIG["site_url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": label, "item": CONFIG["site_url"] + path},
        ],
    }


def schema_for(path, label, body_src):
    graph = [organization()]
    if path == "/":
        graph.append({"@type": "WebSite", "@id": CONFIG["site_url"] + "/#website", "url": CONFIG["site_url"] + "/", "name": CONFIG["brand"], "publisher": {"@id": CONFIG["site_url"] + "/#organization"}})
    if path in ("/", "/contact/"):
        graph += [local_business("ut"), local_business("fl")]
    if path == "/utah-fulfillment-center/":
        graph.append(local_business("ut"))
    if path == "/florida-fulfillment-center/":
        graph.append(local_business("fl"))
    if path == "/services/":
        names = ["Ecommerce order fulfillment", "Warehousing & inventory storage", "Inventory management", "Kitting & bundling",
                 "B2B & retail distribution", "Retail dropshipping", "2-day & international shipping"]
        graph += [{"@type": "Service", "name": n, "serviceType": n, "provider": {"@id": CONFIG["site_url"] + "/#organization"},
                   "areaServed": {"@type": "Country", "name": "United States"}} for n in names]
    for key in FAQS:
        if "{{faq:" + key + "}}" in body_src:
            graph.append(faq_schema(key))
    if label:
        graph.append(breadcrumb(path, label))
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=1, ensure_ascii=False).replace("</", "<\\/")


def header(path):
    def cur(p):
        return ' aria-current="page"' if path == p else ""
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="logo" href="/" aria-label="Boxio home">{LOGO}<span>boxio</span></a>
    <nav class="nav" aria-label="Main">
      <a href="/services/"{cur('/services/')}>Services</a>
      <div class="dd">
        <button type="button" aria-expanded="false" aria-haspopup="true">Locations <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>
        <div class="dd-menu">
          <a href="{{{{ut_path}}}}"><span class="pin">UT</span><span><strong>Utah Fulfillment Center</strong><span>Springville, UT · ships the West fast</span></span></a>
          <a href="{{{{fl_path}}}}"><span class="pin">FL</span><span><strong>Florida Fulfillment Center</strong><span>{{{{fl_city}}}}, FL · ships the Southeast &amp; East Coast</span></span></a>
        </div>
      </div>
      <a href="/integrations/"{cur('/integrations/')}>Integrations</a>
      <a href="/about/"{cur('/about/')}>About</a>
      <a href="/contact/"{cur('/contact/')}>Contact</a>
      <a class="btn btn-primary mobile-only" href="/request-a-quote/">Get a free quote</a>
    </nav>
    <div class="header-cta">
      <a class="header-phone" href="tel:{{{{ut_tel}}}}">{{{{ut_phone}}}}</a>
      <a class="btn btn-primary btn-sm" href="/request-a-quote/">Get a free quote</a>
    </div>
    <button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>"""


def footer():
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="foot-grid">
      <div>
        <a class="logo" href="/">{LOGO}<span>boxio</span></a>
        <p>Tech-enabled ecommerce fulfillment from Utah and Florida. We ship orders fast, so you can grow faster.</p>
        <p><a href="mailto:{{{{email}}}}">{{{{email}}}}</a></p>
      </div>
      <div>
        <h4>Utah Fulfillment Center</h4>
        <address>{{{{ut_street}}}}<br>{{{{ut_city}}}}, {{{{ut_state}}}} {{{{ut_zip}}}}<br><a href="tel:{{{{ut_tel}}}}">{{{{ut_phone}}}}</a></address>
        <p><a href="{{{{ut_path}}}}">Utah 3PL &amp; fulfillment →</a></p>
      </div>
      <div>
        <h4>Florida Fulfillment Center</h4>
        <address>{{{{fl_street}}}}<br>{{{{fl_city}}}}, {{{{fl_state}}}} {{{{fl_zip}}}}<br><a href="tel:{{{{fl_tel}}}}">{{{{fl_phone}}}}</a></address>
        <p><a href="{{{{fl_path}}}}">Florida 3PL &amp; fulfillment →</a></p>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="/services/">Fulfillment services</a></li>
          <li><a href="/integrations/">Integrations</a></li>
          <li><a href="/about/">About Boxio</a></li>
          <li><a href="/request-a-quote/">Get a free quote</a></li>
          <li><a href="/contact/">Contact us</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-bottom">
      <span>© {{{{year}}}} {CONFIG['legal_name']}. All rights reserved.</span>
      <span><a href="/privacy/">Privacy Policy</a> · <a href="/terms/">Terms &amp; Conditions</a></span>
    </div>
  </div>
</footer>
<a class="btn btn-primary fab" href="/request-a-quote/">{{{{icon:bolt}}}} Get a free quote</a>
<div class="mobile-bar">
  <a class="btn btn-ghost" href="tel:{{{{ut_tel}}}}">{{{{icon:phone}}}} Call</a>
  <a class="btn btn-primary" href="/request-a-quote/">Free quote</a>
</div>"""


def render(path, src_name, title, desc, crumb):
    body = (SRC / "pages" / src_name).read_text()
    schema = schema_for(path, crumb, body)
    for key in FAQS:
        body = body.replace("{{faq:" + key + "}}", faq_html(key))
    partials = {name.stem: name.read_text() for name in (SRC / "partials").glob("*.html")}
    for name, html in partials.items():
        body = body.replace("{{partial:" + name + "}}", html)
    crumbs = ""
    if crumb:
        crumbs = f'<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">{escape(crumb)}</li></ol></nav>'
    body = body.replace("{{crumbs}}", crumbs)
    canonical = CONFIG["site_url"] + path
    geo = ""
    if path == "/utah-fulfillment-center/":
        geo = '<meta name="geo.region" content="US-UT">\n<meta name="geo.placename" content="Springville, Utah">\n'
    if path == "/florida-fulfillment-center/":
        geo = '<meta name="geo.region" content="US-FL">\n<meta name="geo.placename" content="{{fl_city}}, Florida">\n'
    html = f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(fill(title))}</title>
<meta name="description" content="{escape(fill(desc))}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large">
{geo}<meta property="og:type" content="website">
<meta property="og:site_name" content="Boxio">
<meta property="og:title" content="{escape(fill(title))}">
<meta property="og:description" content="{escape(fill(desc))}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#141413">
<link rel="icon" href="/assets/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/assets/styles.css">
<script type="application/ld+json">
{schema}
</script>
</head>
<body>
{header(path)}
<main id="main">
{body}
</main>
{footer()}
<script src="/assets/main.js" defer></script>
</body>
</html>
"""
    return fill(html)


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    for f in (SRC / "assets").iterdir():
        shutil.copy(f, DIST / "assets" / f.name)
    (DIST / "assets" / "logo.svg").write_text(LOGO.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" '))

    for path, src_name, title, desc, crumb in PAGES:
        out = DIST / path.strip("/") / "index.html" if path != "/" else DIST / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(path, src_name, title, desc, crumb))

    # 404
    nf = render("/404", "404.html", "Page not found | Boxio", "This page could not be found.", None)
    (DIST / "404.html").write_text(nf.replace('content="index, follow, max-image-preview:large"', 'content="noindex"'))

    today = date.today().isoformat()
    urls = "".join(f"  <url><loc>{CONFIG['site_url']}{p}</loc><lastmod>{today}</lastmod></url>\n" for p, *_ in PAGES)
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {CONFIG['site_url']}/sitemap.xml\n")
    (DIST / "_redirects").write_text("".join(f"{a} {b} 301\n{a.rstrip('/')} {b} 301\n" for a, b in REDIRECTS.items()))
    (DIST / ".htaccess").write_text("ErrorDocument 404 /404.html\n" + "".join(f"Redirect 301 {a.rstrip('/')} {b}\n" for a, b in REDIRECTS.items()))

    # Warn about anything still to fill in
    todos = set()
    missing = [p for p in ("privacy", "terms") if not (DIST / p / "index.html").exists()]
    for f in DIST.rglob("*.html"):
        todos.update(re.findall(r"\[(?:Florida street address|City|ZIP|Florida phone)\]", f.read_text()))
    print(f"Built {len(PAGES) + 1} pages into {DIST.relative_to(ROOT)}/")
    if todos:
        print("  ! Placeholders still present:", ", ".join(sorted(todos)), "— update CONFIG['locations']['fl'] in build.py")
    if missing:
        print("  ! Footer links to /privacy/ and /terms/ — add src/pages/privacy.html and terms.html (copy from the current site) and list them in PAGES")


if __name__ == "__main__":
    main()
