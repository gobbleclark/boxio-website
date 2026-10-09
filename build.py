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
import struct
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
    # Official social profiles: shown in the footer and listed as "sameAs" in schema so Google links them to the site
    "social": {
        "LinkedIn": "https://www.linkedin.com/company/boxioship",
    },
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
            "name": "Boxio Fulfillment — Florida",
            "label": "Florida",
            "street": "2730 Pickettville Road, Unit 105",
            "city": "Jacksonville",
            "state": "FL",
            "state_name": "Florida",
            "zip": "32220",
            # No local Florida line yet — uses the main number. Swap in a 904 number if you get one.
            "phone": "(801) 960-4373",
            "path": "/florida-fulfillment-center/",
            # Approximate; used only for the map pin and transit-time estimates.
            "coords": [30.33, -81.80],
        },
    },
    # Google Search Console "HTML tag" verification: paste only the content="..." value. Leave empty if verified by DNS.
    "google_site_verification": "",
    # Sales rep booking calendar on the Free Quote page. Paste the Calendly event link,
    # e.g. "https://calendly.com/justin-boxio/30min". Leave empty to show a call button instead.
    "sales_rep": {"name": "Justin", "calendly": "https://calendly.com/justin-boxioship/boxio-intro-call"},
    # Customer logos shown in the "Trusted by" strip (files in src/assets/logos/). Order = display order.
    "customers": [
        ("Redmond", "redmond.svg"), ("Re-Lyte", "relyte.svg"), ("Walli", "walli.png"), ("Mabē", "mabe.png"), ("AAPC", "aapc.png"),
        ("Clean Monday Meals", "cleanmonday.png"), ("Ballerina Farm", "ballerinafarm.png"), ("Signal Relief", "signalrelief.png"),
        ("Brixley Bags", "brixley.png"), ("Teddy + Rose", "teddyrose.png"), ("Real Salt", "realsalt.svg", "badge"), ("Super Patch", "superpatch.svg"),
        ("Kindly Camera Bags", "kindly.png"), ("Lates by Kate", "latesbykate.png"), ("Pressed Floral", "pressedfloral.svg"), ("Yonder", "yonder.png"),
    ],
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
     "Florida Fulfillment Center & 3PL in Jacksonville, FL | Boxio",
     "Ecommerce fulfillment in Florida from Boxio's Jacksonville warehouse. Reach Southeast and East Coast customers faster with pick, pack & ship, storage, kitting and B2B. Free quote.",
     "Florida Fulfillment Center"),
    ("/services/", "services.html",
     "3PL Fulfillment Services | Pick, Pack, Ship & Storage | Boxio",
     "Full-service ecommerce 3PL: order fulfillment, warehousing, inventory management, kitting & bundling, B2B retail distribution, dropshipping and 2-day shipping from Utah and Florida.",
     "Services"),
    ("/integrations/", "integrations.html",
     "65+ Fulfillment Integrations: Shopify, Amazon, Walmart, TikTok Shop | Boxio",
     "Connect Shopify, WooCommerce, BigCommerce, Amazon, Walmart, TikTok Shop, NetSuite, Loop and 60+ more to Boxio fulfillment. Ship with UPS, FedEx, USPS, DHL and more.",
     "Integrations"),
    ("/about/", "about.html",
     "About Boxio | Tech-Enabled 3PL in Utah & Florida",
     "Boxio is a tech-enabled third-party logistics company helping growing ecommerce brands ship faster from Utah and Florida with 99.99% order accuracy.",
     "About"),
    ("/request-a-quote/", "quote.html",
     "Get a Free 3PL Fulfillment Quote | Boxio",
     "Tell us about your orders and get a free, custom ecommerce fulfillment quote from Boxio's Utah and Florida warehouses. Reply within one business day.",
     "Free Quote"),
    ("/contact/", "contact.html",
     "Contact Boxio 3PL | Utah & Florida Fulfillment Centers",
     "Contact Boxio fulfillment. Call, email or send a message to our Springville, Utah or Florida warehouse team.",
     "Contact"),
    ("/privacy/", "privacy.html",
     "Privacy Policy | Boxio",
     "How Boxio collects, uses and protects information submitted through boxioship.com.",
     "Privacy Policy"),
    ("/terms/", "terms.html",
     "Terms & Conditions | Boxio",
     "Terms and conditions governing use of the boxioship.com website.",
     "Terms & Conditions"),
    ("/shopify-fulfillment/", "shopify.html",
     "Shopify Fulfillment | Utah & Florida 3PL | Boxio",
     "Shopify fulfillment from Utah and Florida. Orders sync automatically, ship fast with 99.99% accuracy, and tracking flows back to Shopify. Get a free quote.",
     "Shopify Fulfillment"),
    ("/amazon-fulfillment/", "amazon.html",
     "Amazon FBA Prep & FBM Fulfillment | Boxio 3PL",
     "Amazon FBA prep and merchant-fulfilled (FBM) shipping from Utah and Florida. Labeling, bundling, FBA replenishment and fast order fulfillment. Free quote.",
     "Amazon Fulfillment"),
    ("/walmart-fulfillment/", "walmart.html",
     "Walmart Marketplace Fulfillment | Boxio 3PL",
     "Walmart Marketplace fulfillment from Utah and Florida. Orders sync automatically and ship on time to protect your seller metrics. D2C and B2B. Free quote.",
     "Walmart Fulfillment"),
    ("/tiktok-shop-fulfillment/", "tiktok.html",
     "TikTok Shop Fulfillment | Utah & Florida 3PL | Boxio",
     "TikTok Shop fulfillment built for viral spikes. Orders sync automatically and ship fast from Utah and Florida, including creator samples. Get a free quote.",
     "TikTok Shop Fulfillment"),
    ("/what-is-a-3pl/", "what-is-a-3pl.html",
     "What Is a 3PL? Ecommerce Fulfillment Explained | Boxio",
     "What a 3PL (third-party logistics provider) does, how 3PL fulfillment works, when your brand needs one and how to choose the right partner.",
     "What Is a 3PL?"),
    ("/3pl-pricing/", "3pl-pricing.html",
     "3PL Pricing Explained: What Fulfillment Really Costs | Boxio",
     "How 3PL pricing works: receiving, storage, pick and pack, packaging and shipping fees, what drives your cost, and how to compare 3PL quotes.",
     "3PL Pricing"),
    ("/3pl-vs-in-house-fulfillment/", "3pl-vs-in-house.html",
     "3PL vs. In-House Fulfillment: When to Outsource | Boxio",
     "Compare a 3PL with shipping orders yourself: cost, speed, shipping rates and scale. Signs it's time to outsource and how to switch smoothly.",
     "3PL vs. In-House Fulfillment"),
    ("/b2b-fulfillment/", "b2b.html",
     "B2B & Wholesale Fulfillment | Utah & Florida 3PL | Boxio",
     "B2B, wholesale and retail fulfillment from Utah and Florida. Ship retailer orders and D2C orders from one inventory with 99.99% accuracy. Free quote.",
     "B2B Fulfillment"),
]

# Long-form guides get Article schema
ARTICLE_PAGES = {
    "/what-is-a-3pl/": "What Is a 3PL? Ecommerce Fulfillment Explained",
    "/3pl-pricing/": "3PL Pricing Explained: What Fulfillment Really Costs",
    "/3pl-vs-in-house-fulfillment/": "3PL vs. In-House Fulfillment: When to Outsource",
}
ARTICLE_DATE = "2026-10-09"

# Sales-channel pages: path -> (channel name used in the quote form, schema service name)
CHANNEL_PAGES = {
    "/shopify-fulfillment/": ("Shopify", "Shopify order fulfillment"),
    "/amazon-fulfillment/": ("Amazon", "Amazon FBA prep and FBM fulfillment"),
    "/walmart-fulfillment/": ("Walmart", "Walmart Marketplace fulfillment"),
    "/tiktok-shop-fulfillment/": ("TikTok Shop", "TikTok Shop fulfillment"),
}

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
        ("What is a 3PL?",
         "A 3PL (third-party logistics provider) stores your inventory and handles order fulfillment for you: receiving stock, picking and packing orders, and shipping them to your customers. Brands use a 3PL to ship faster and cut costs without running their own warehouse."),
        ("What does Boxio do?",
         "Boxio is a tech-enabled third-party logistics (3PL) company. We store your inventory and pick, pack and ship your ecommerce orders on your behalf, with real-time inventory tracking and integrations for the platforms you already sell on."),
        ("Where are Boxio's fulfillment centers?",
         "We have fulfillment centers in Springville, Utah ({{ut_full}}) and in Florida ({{fl_full}}). Shipping from the location closest to your customers shortens transit times and can lower shipping costs."),
        ("Should I ship from Utah, Florida, or both?",
         "Utah is well placed for customers in the West, Mountain West and Southwest. Florida is well placed for the Southeast and East Coast. Use the shipping map on this page to compare, or request a quote and we'll recommend a setup based on where your customers are."),
        ("Which ecommerce platforms do you integrate with?",
         "Shopify, WooCommerce, BigCommerce, Amazon, Walmart, TikTok Shop, eBay, Etsy and Google Shopping, plus ERPs like Oracle NetSuite, returns platforms like Loop, and 60+ shipping carriers and apps. We also offer API integrations for custom builds."),
        ("How quickly does your team respond?",
         "Fast. Clients reach our team by chat, and our average chat response time is under 1 hour. You talk to real people who know your account, not a ticket queue."),
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
    "shopify": [
        ("How does Shopify fulfillment with Boxio work?",
         "Connect your Shopify store and orders flow to our warehouse automatically. We pick, pack and ship each order, then push tracking back to Shopify so your customer gets their shipping notification right away."),
        ("Does Boxio sync inventory with Shopify?",
         "Yes. Inventory counts update in real time as stock is received and orders ship, so your Shopify store always shows what's actually available and you avoid overselling."),
        ("Can you ship Shopify wholesale and B2B orders too?",
         "Yes. We ship D2C and B2B orders from the same inventory, so wholesale and retail orders go out alongside your everyday Shopify orders."),
        ("Which warehouse should my Shopify orders ship from?",
         "Our Utah warehouse is fastest for the West and Mountain states, and Jacksonville, Florida is fastest for the Southeast and East Coast. Many brands use both so every order ships from the closer warehouse."),
    ],
    "amazon": [
        ("Do you offer Amazon FBA prep?",
         "Yes. We receive your inventory, apply FNSKU labels, poly-bag or bundle units as required, label cartons and ship them into Amazon fulfillment centers."),
        ("Can you fulfill merchant-fulfilled (FBM) Amazon orders?",
         "Yes. FBM orders sync from Seller Central automatically and ship on time with valid tracking, which protects your seller metrics."),
        ("Can I use one inventory for Amazon and my own website?",
         "Yes. Keep your inventory with us, replenish FBA as needed and ship your Shopify, TikTok Shop and FBM orders from the same stock."),
        ("Why keep inventory at a 3PL instead of all in FBA?",
         "Amazon limits how much inventory you can store and charges more for long-term storage. Keeping your main inventory with us and sending FBA what it needs avoids stockouts and storage limits."),
    ],
    "walmart": [
        ("Do you integrate with Walmart Marketplace?",
         "Yes. Walmart Marketplace orders flow to our warehouse automatically, and tracking is sent back to Walmart as soon as each order ships."),
        ("How do you help protect my Walmart seller performance?",
         "Walmart holds sellers to strict on-time shipping and tracking standards. With 99.97% on-time shipments and automatic tracking uploads, your orders go out on time with valid tracking."),
        ("Can you handle B2B and retail orders as well?",
         "Yes. We ship D2C and B2B orders from the same inventory. Tell us your retail and wholesale requirements and we'll set up the right packing and shipping workflow."),
        ("Can I sell on Walmart, Amazon and Shopify from one inventory?",
         "Yes. All of your channels pull from one inventory pool in our warehouses, so stock levels stay accurate everywhere you sell."),
    ],
    "tiktok": [
        ("Does Boxio integrate with TikTok Shop?",
         "Yes. TikTok Shop orders sync to our warehouse automatically, and tracking flows back to TikTok Shop as soon as each order ships."),
        ("Can you handle a viral spike in TikTok Shop orders?",
         "Yes. Our team and infrastructure scale with demand. Let us know before a big LIVE, launch or creator push and we'll plan staffing and inventory so orders keep shipping on time."),
        ("Can you ship creator and affiliate samples?",
         "Yes. Creator and affiliate sample orders ship just like customer orders, so you can get product into creators' hands quickly."),
        ("How do TikTok Shop orders get to customers faster?",
         "Ship from the warehouse closest to each customer: Springville, Utah for the West and Jacksonville, Florida for the Southeast and East Coast."),
    ],
    "whatis": [
        ("What does 3PL stand for?",
         "3PL stands for third-party logistics. A 3PL is a company that stores your inventory and handles order fulfillment for you, from receiving stock to picking, packing and shipping orders."),
        ("What's the difference between a 3PL and a fulfillment center?",
         "A fulfillment center is the warehouse where orders are packed and shipped. A 3PL is the company that runs fulfillment for you, often across one or more fulfillment centers, along with the technology, integrations and carrier relationships behind it."),
        ("Is a 3PL the same as Amazon FBA?",
         "No. FBA only fulfills Amazon orders from Amazon's warehouses. A 3PL fulfills orders from every channel you sell on, including your own website, marketplaces and B2B, and can also prep and send inventory into FBA."),
        ("How do I know if my business needs a 3PL?",
         "Common signs: packing orders takes over your week, you've run out of space, shipping mistakes are creeping in, you're adding sales channels or wholesale accounts, or customers on the other side of the country wait too long for deliveries."),
    ],
    "pricing": [
        ("How much does a 3PL cost?",
         "It depends on your order volume, items per order, product size, storage needs and where your customers are. Most 3PL pricing combines receiving, storage, pick and pack, packaging and shipping fees. The most reliable way to know is a custom quote based on your real order data."),
        ("Is shipping included in 3PL pricing?",
         "Usually postage is billed separately from fulfillment fees, based on the carrier, service level, package weight and dimensions, and destination zone. Ask every 3PL how they bill postage so you can compare quotes fairly."),
        ("Why do 3PL quotes vary so much?",
         "3PLs bundle fees differently: some charge per order, some per item, some include packaging and some don't. Compare the total cost per order for your typical order, not individual line items."),
        ("How can a 3PL lower my shipping costs?",
         "Carrier discounts and smarter packaging help, but warehouse location matters most. Shipping from a warehouse closer to your customers means fewer shipping zones per package, which lowers postage and speeds up delivery."),
    ],
    "vsinhouse": [
        ("When should I switch from in-house fulfillment to a 3PL?",
         "When fulfillment starts limiting growth: packing orders eats up your time, you're out of space, errors or delays are increasing, or you're adding channels like Amazon, TikTok Shop or wholesale that are hard to manage from one garage or small warehouse."),
        ("Is a 3PL cheaper than doing fulfillment myself?",
         "Often, once you count everything: rent, staff, packaging, software and the shipping discounts a 3PL gets from volume. In-house can be cheaper at very low volumes, but it usually costs more of your time."),
        ("Will I lose control if I outsource fulfillment?",
         "Not with the right 3PL. You should see live inventory and order status, set your own packaging rules and reach a real person quickly. Boxio clients get real-time inventory and an average chat response time under 1 hour."),
        ("How hard is it to switch to a 3PL?",
         "The main steps are connecting your store, setting up your products and sending in inventory. A good 3PL handles onboarding with you so orders keep shipping during the move."),
    ],
    "b2b": [
        ("What is B2B fulfillment?",
         "B2B fulfillment is shipping orders to other businesses, such as retailers, wholesalers and distributors, instead of to individual consumers. These orders are often larger and come with retailer-specific packing, labeling and paperwork requirements."),
        ("Can you ship B2B and D2C orders from the same inventory?",
         "Yes. Your wholesale and retail orders ship from the same inventory as your D2C orders, so stock levels stay accurate across every channel."),
        ("Do you support retail dropshipping?",
         "Yes. We fulfill dropship orders on behalf of your retail partners, shipping directly to their customers."),
        ("Can you handle EDI orders?",
         "Boxio connects with SPS Commerce for EDI, which many retailers require. Tell us which retailers you sell to and we'll confirm the setup."),
    ],
    "florida": [
        ("Where is Boxio's Florida fulfillment center?",
         "Our Florida warehouse is at {{fl_full}}, in Northeast Florida."),
        ("Why use a Jacksonville, Florida 3PL?",
         "Jacksonville sits at the junction of I-95 and I-10, putting your inventory close to the fast-growing Southeast and within ground reach of the entire East Coast. JAXPORT and Florida's major airports also make it a natural gateway for international orders."),
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

# Brand logo (src/assets/brand/). Source: Boxio logo, brand color #29254F.
LOGO = '<img src="/assets/brand/logo.png" alt="Boxio" width="126" height="32">'
LOGO_WHITE = '<img src="/assets/brand/logo-white.png" alt="Boxio" width="134" height="34">'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def albers_usa(lon, lat):
    """Project lon/lat to the 975x610 Albers USA frame used by src/assets/us-states.json (lower 48 only)."""
    from math import radians, sin, cos, sqrt
    phi0, phi1 = radians(29.5), radians(45.5)
    n = (sin(phi0) + sin(phi1)) / 2
    c = 1 + sin(phi0) * (2 * n - sin(phi0))
    r0 = sqrt(c) / n

    def raw(lam, phi):
        r = sqrt(c - 2 * n * sin(phi)) / n
        return r * sin(lam * n), r0 - r * cos(lam * n)

    k, tx, ty = 1300, 487.5, 305
    cx, cy = raw(radians(-0.6), radians(38.7))
    px, py = raw(radians(lon + 96), radians(lat))
    return [round(tx + k * (px - cx), 1), round(ty - k * (py - cy), 1)]


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
        {"key": k, "label": L["label"], "city": L["city"], "state": L["state"], "coords": L["coords"], "xy": albers_usa(L["coords"][1], L["coords"][0])} for k, L in CONFIG["locations"].items()
    ]))
    return t


TOKENS = loc_tokens()


def fill(text):
    text = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: ICONS[m.group(1)], text)
    for k, v in TOKENS.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def logo_size(path, area=4600, max_h=46, max_w=215):
    """Size logos to a similar visual area so wide wordmarks and tall marks look balanced."""
    data = path.read_bytes()
    if path.suffix == ".png":
        w, h = struct.unpack(">II", data[16:24])
    else:
        vb = re.search(rb'viewBox="[\d.\s-]*?([\d.]+)[\s,]+([\d.]+)"', data)
        w, h = float(vb.group(1)), float(vb.group(2))
    r = w / h
    hh = min(max_h, (area / r) ** 0.5, max_w / r)
    return round(hh * r), round(hh)


def customer_logos_html():
    def li(n, f, mode=""):
        # "badge" logos have knocked-out lettering, so they're shown in grayscale instead of as a silhouette
        w, h = logo_size(SRC / "assets" / "logos" / f)
        cls = f' class="{mode}"' if mode else ""
        return f'<li><img src="/assets/logos/{f}" alt="{escape(n)}" width="{w}" height="{h}"{cls} loading="lazy" decoding="async"></li>'
    items = "".join(li(*c) for c in CONFIG["customers"])
    dup = items.replace('alt="', 'aria-hidden="true" alt="')
    return f"""<section class="logos" aria-label="Brands that ship with Boxio">
  <div class="container"><p class="logos-title">Trusted by 100+ growing brands</p></div>
  <div class="logo-marquee"><ul class="logo-track">{items}{dup}</ul></div>
</section>"""

INT_LABELS = {"store": "Ecommerce platform", "market": "Marketplace", "shipping": "Shipping carrier",
              "erp": "ERP", "returns": "Returns", "apps": "Apps & partners"}


def integrations():
    return json.loads((SRC / "data" / "integrations.json").read_text())


# Integrations that have their own page on the site (internal links help those pages rank)
INT_PAGES = {
    "Shopify": ("/shopify-fulfillment/", "Shopify fulfillment"),
    "Amazon": ("/amazon-fulfillment/", "Amazon FBA prep & FBM"),
    "Walmart": ("/walmart-fulfillment/", "Walmart fulfillment"),
    "TikTok Shop": ("/tiktok-shop-fulfillment/", "TikTok Shop fulfillment"),
    "SPS Commerce": ("/b2b-fulfillment/", "B2B & EDI fulfillment"),
}


def integrations_grid_html():
    def card(i):
        inner = (f'<span class="int-logo"><img src="/assets/integrations/{i["logo"]}" alt="{escape(i["name"])} logo" loading="lazy" decoding="async"></span>'
                 f'<strong>{escape(i["name"])}</strong><small>{INT_LABELS[i["category"]]}</small>')
        attrs = f'data-cat="{i["category"]}" data-name="{escape(i["name"])}"'
        if i["name"] in INT_PAGES:
            href, label = INT_PAGES[i["name"]]
            return f'<a class="int int-link" href="{href}" {attrs}>{inner}<span class="more">{escape(label)} <span>→</span></span></a>'
        return f'<div class="int" {attrs}>{inner}</div>'
    cards = "".join(card(i) for i in integrations())
    cards += ('<div class="int" data-cat="apps" data-name="Custom API integration"><span class="int-logo int-logo-api">{}</span>'
              '<strong>Custom API</strong><small>For custom builds</small></div>')
    return cards

def booking_html():
    rep = CONFIG["sales_rep"]
    url = rep["calendly"].strip()
    if not url:
        return (f'<a class="btn btn-light" href="tel:{{{{ut_tel}}}}" style="width:100%">{{{{icon:phone}}}} Call {escape(rep["name"])}: {{{{ut_phone}}}}</a>')
    sep = "&" if "?" in url else "?"
    full = url + sep + "hide_gdpr_banner=1&hide_event_type_details=1&primary_color=29254f&text_color=0f0d1f"
    return (f'<div class="calendly-box" data-calendly="{escape(full)}">'
            f'<p class="calendly-loading">Loading {escape(rep["name"])}\'s calendar…</p>'
            f'<noscript><a href="{escape(url)}">Book a call with {escape(rep["name"])}</a></noscript></div>')

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
        "image": CONFIG["site_url"] + "/assets/brand/logo-large.png",
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
        "logo": CONFIG["site_url"] + "/assets/brand/logo-large.png",
        "email": CONFIG["email"],
        "telephone": TOKENS["ut_tel"],
        "description": "Tech-enabled third-party logistics (3PL) and ecommerce fulfillment with warehouses in Utah and Florida.",
        "sameAs": list(CONFIG["social"].values()),
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
    if path in ARTICLE_PAGES:
        graph.append({"@type": "Article", "headline": ARTICLE_PAGES[path],
                      "datePublished": ARTICLE_DATE, "dateModified": ARTICLE_DATE,
                      "author": {"@id": CONFIG["site_url"] + "/#organization"},
                      "publisher": {"@id": CONFIG["site_url"] + "/#organization"},
                      "image": CONFIG["site_url"] + "/assets/brand/logo-large.png",
                      "mainEntityOfPage": CONFIG["site_url"] + path})
    if path == "/b2b-fulfillment/":
        graph.append({"@type": "Service", "name": "B2B and wholesale fulfillment", "serviceType": "B2B fulfillment",
                      "provider": {"@id": CONFIG["site_url"] + "/#organization"},
                      "areaServed": {"@type": "Country", "name": "United States"}, "url": CONFIG["site_url"] + path})
    if path in CHANNEL_PAGES:
        name = CHANNEL_PAGES[path][1]
        graph.append({"@type": "Service", "name": name, "serviceType": name,
                      "provider": {"@id": CONFIG["site_url"] + "/#organization"},
                      "areaServed": {"@type": "Country", "name": "United States"},
                      "url": CONFIG["site_url"] + path})
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
    <a class="logo" href="/" aria-label="Boxio home">{LOGO}</a>
    <nav class="nav" aria-label="Main">
      <div class="dd">
        <button type="button" aria-expanded="false" aria-haspopup="true">Services <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>
        <div class="dd-menu">
          <a href="/services/"><span class="pin">3PL</span><span><strong>All fulfillment services</strong><span>Pick &amp; pack, storage, kitting, B2B</span></span></a>
          <a href="/shopify-fulfillment/"><span class="pin">SH</span><span><strong>Shopify fulfillment</strong><span>Orders &amp; tracking sync automatically</span></span></a>
          <a href="/amazon-fulfillment/"><span class="pin">AMZ</span><span><strong>Amazon FBA prep &amp; FBM</strong><span>Prep, replenishment &amp; order fulfillment</span></span></a>
          <a href="/walmart-fulfillment/"><span class="pin">WMT</span><span><strong>Walmart fulfillment</strong><span>On-time shipping for Marketplace sellers</span></span></a>
          <a href="/tiktok-shop-fulfillment/"><span class="pin">TT</span><span><strong>TikTok Shop fulfillment</strong><span>Built for viral spikes &amp; creator samples</span></span></a>
          <a href="/b2b-fulfillment/"><span class="pin">B2B</span><span><strong>B2B &amp; wholesale fulfillment</strong><span>Retail, wholesale &amp; dropship orders</span></span></a>
        </div>
      </div>
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


SOCIAL_ICONS = {
    "LinkedIn": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>',
}


def social_links():
    links = "".join(
        f'<a href="{escape(url)}" target="_blank" rel="noopener" aria-label="Boxio on {name}">{SOCIAL_ICONS.get(name, escape(name))}</a>'
        for name, url in CONFIG["social"].items()
    )
    return f'<div class="social">{links}</div>' if links else ""


def footer():
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="foot-grid">
      <div>
        <a class="logo" href="/" aria-label="Boxio home">{LOGO_WHITE}</a>
        <p>Boxio is a tech-enabled ecommerce 3PL (third-party logistics) company with fulfillment centers in Springville, Utah and Jacksonville, Florida. We ship orders fast, so you can grow faster.</p>
        <p><a href="mailto:{{{{email}}}}">{{{{email}}}}</a></p>
        {social_links()}
      </div>
      <div>
        <h4>Utah 3PL Fulfillment Center</h4>
        <address>{{{{ut_street}}}}<br>{{{{ut_city}}}}, {{{{ut_state}}}} {{{{ut_zip}}}}<br><a href="tel:{{{{ut_tel}}}}">{{{{ut_phone}}}}</a></address>
        <p><a href="{{{{ut_path}}}}">Utah 3PL &amp; fulfillment →</a></p>
      </div>
      <div>
        <h4>Florida 3PL Fulfillment Center</h4>
        <address>{{{{fl_street}}}}<br>{{{{fl_city}}}}, {{{{fl_state}}}} {{{{fl_zip}}}}<br><a href="tel:{{{{fl_tel}}}}">{{{{fl_phone}}}}</a></address>
        <p><a href="{{{{fl_path}}}}">Florida 3PL &amp; fulfillment →</a></p>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="/services/">3PL fulfillment services</a></li>
          <li><a href="/shopify-fulfillment/">Shopify fulfillment</a></li>
          <li><a href="/amazon-fulfillment/">Amazon FBA prep &amp; FBM</a></li>
          <li><a href="/walmart-fulfillment/">Walmart fulfillment</a></li>
          <li><a href="/tiktok-shop-fulfillment/">TikTok Shop fulfillment</a></li>
          <li><a href="/b2b-fulfillment/">B2B &amp; wholesale fulfillment</a></li>
          <li><a href="/what-is-a-3pl/">What is a 3PL?</a></li>
          <li><a href="/3pl-pricing/">3PL pricing explained</a></li>
          <li><a href="/3pl-vs-in-house-fulfillment/">3PL vs. in-house</a></li>
          <li><a href="/integrations/">Integrations</a></li>
          <li><a href="/about/">About Boxio</a></li>
          <li><a href="/request-a-quote/">Get a free 3PL quote</a></li>
          <li><a href="/contact/">Contact us</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-bottom">
      <span>© {{{{year}}}} {CONFIG['legal_name']}. Ecommerce 3PL &amp; order fulfillment in Utah and Florida.</span>
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
    body = body.replace("{{crumbs}}", crumbs).replace("{{customer_logos}}", customer_logos_html()).replace("{{integrations_grid}}", integrations_grid_html()).replace("{{integrations_count}}", str(len(integrations()))).replace("{{booking}}", booking_html()).replace("{{sales_rep}}", escape(CONFIG["sales_rep"]["name"]))
    canonical = CONFIG["site_url"] + path
    geo = ""
    if path == "/utah-fulfillment-center/":
        geo = '<meta name="geo.region" content="US-UT">\n<meta name="geo.placename" content="Springville, Utah">\n'
    if path == "/florida-fulfillment-center/":
        geo = '<meta name="geo.region" content="US-FL">\n<meta name="geo.placename" content="{{fl_city}}, Florida">\n'
    gsv = CONFIG["google_site_verification"].strip()
    gsv = f'\n<meta name="google-site-verification" content="{escape(gsv)}">' if gsv and path == "/" else ""
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
<meta name="theme-color" content="#29254f">{gsv}
<link rel="icon" href="/assets/brand/icon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/brand/icon.png">
<meta property="og:image" content="{CONFIG['site_url']}/assets/brand/logo-large.png">
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
    shutil.copytree(SRC / "assets", DIST / "assets", dirs_exist_ok=True)

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
    if not CONFIG["sales_rep"]["calendly"]:
        print("  ! No Calendly link yet — set CONFIG['sales_rep']['calendly'] in build.py (showing a call button for now)")
    if missing:
        print("  ! Footer links to /privacy/ and /terms/ — add src/pages/privacy.html and terms.html (copy from the current site) and list them in PAGES")


if __name__ == "__main__":
    main()
