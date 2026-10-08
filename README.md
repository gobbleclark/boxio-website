# boxioship.com

Static website for Boxio. No framework, no dependencies beyond Python 3.

## Build

```
python3 build.py
```

Outputs the finished site to `dist/`. Hosted on **Vercel**: `vercel.json` tells Vercel to run `python3 build.py` and publish `dist/`, so every push to `main` redeploys.

## Where things live

| What | File |
|---|---|
| Business name, addresses, phones, email | `CONFIG` in `build.py` |
| Page titles & meta descriptions (SEO) | `PAGES` in `build.py` |
| FAQ questions (also become FAQ schema) | `FAQS` in `build.py` |
| Old URL → new URL redirects | `redirects` in `vercel.json` (keep `REDIRECTS` in `build.py` in sync for non-Vercel hosts) |
| Integrations list (from ShipHero) | `src/data/integrations.json`, logos in `src/assets/integrations/` |
| Customer logo carousel | `CONFIG["customers"]` in `build.py`, logos in `src/assets/logos/` |
| Page content | `src/pages/*.html` |
| Shared sections (map, location cards, CTA) | `src/partials/*.html` |
| Styles / interactions | `src/assets/styles.css`, `src/assets/main.js` |
| Where form submissions go | `FORM_ENDPOINT` in `src/assets/main.js` → Supabase Edge Function `website-lead` (source in `supabase/functions/website-lead/`) → `public.website_leads` table |

## Before launch

1. Add `src/pages/privacy.html` and `src/pages/terms.html` (copy from the current site) and add them to `PAGES`.
2. After going live, submit `https://www.boxioship.com/sitemap.xml` in Google Search Console.
