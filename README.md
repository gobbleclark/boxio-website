# boxioship.com

Static website for Boxio. No framework, no dependencies beyond Python 3.

## Build

```
python3 build.py
```

Outputs the finished site to `dist/`. Upload the contents of `dist/` to any static host (Netlify, Cloudflare Pages, Vercel, or your current web host).

## Where things live

| What | File |
|---|---|
| Business name, addresses, phones, email | `CONFIG` in `build.py` |
| Page titles & meta descriptions (SEO) | `PAGES` in `build.py` |
| FAQ questions (also become FAQ schema) | `FAQS` in `build.py` |
| Old URL → new URL redirects | `REDIRECTS` in `build.py` |
| Page content | `src/pages/*.html` |
| Shared sections (map, location cards, CTA) | `src/partials/*.html` |
| Styles / interactions | `src/assets/styles.css`, `src/assets/main.js` |
| Where form submissions go | `FORM_ENDPOINT` at the top of `src/assets/main.js` |

## Before launch

1. Fill in the Florida address, ZIP, phone and coordinates in `CONFIG` (the build warns until you do).
2. Set `FORM_ENDPOINT` so quote and contact forms deliver to your inbox/CRM. Until then they open the visitor's email app.
3. Add `src/pages/privacy.html` and `src/pages/terms.html` (copy from the current site) and add them to `PAGES`.
4. After going live, submit `https://www.boxioship.com/sitemap.xml` in Google Search Console.
