// website-lead: receives quote/contact form submissions from boxioship.com and stores them in public.website_leads.
// Deployed with verify_jwt = false because it's a public form endpoint; it validates input, checks the
// request origin, drops honeypot spam and rate-limits by (hashed) IP instead.
import postgres from "npm:postgres@3.4.5";

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, { prepare: false, max: 1 });

const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?boxioship\.com$/,
  /^https:\/\/boxio-website[a-z0-9-]*-boxioship\.vercel\.app$/, // Vercel production + preview deployments
  /^https:\/\/boxio-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];
const MAX_PER_IP_PER_10_MIN = 5;

const cors = (origin: string | null) => ({
  "Access-Control-Allow-Origin": origin ?? "",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "content-type",
  "Access-Control-Max-Age": "86400",
  Vary: "Origin",
});
const json = (body: unknown, status: number, origin: string | null) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(origin) } });

const clip = (v: unknown, max: number) => {
  if (v === undefined || v === null) return null;
  const s = String(v).trim();
  return s ? s.slice(0, max) : null;
};

async function sha256(text: string) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin");
  const allowed = !!origin && ALLOWED_ORIGINS.some((re) => re.test(origin));
  if (req.method === "OPTIONS") return new Response(null, { status: allowed ? 204 : 403, headers: allowed ? cors(origin) : {} });
  if (!allowed) return new Response("Forbidden", { status: 403 });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405, origin);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400, origin);
  }

  // Honeypot field filled in = bot. Pretend success so it doesn't retry.
  if (body.hp) return json({ ok: true }, 200, origin);

  const formType = body.form_type === "contact" ? "contact" : body.form_type === "quote" ? "quote" : null;
  const data = (body.data && typeof body.data === "object" ? body.data : {}) as Record<string, unknown>;
  const name = clip(data["Name"], 200);
  const email = clip(data["Email"], 320);
  if (!formType || !name || !email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ error: "Please include your name and a valid email." }, 422, origin);
  }

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  const ipHash = ip ? (await sha256("boxio-leads:" + ip)).slice(0, 32) : null;

  try {
    if (ipHash) {
      const [{ n }] = await sql`
        select count(*)::int as n from public.website_leads
        where details->>'_ip_hash' = ${ipHash} and created_at > now() - interval '10 minutes'`;
      if (n >= MAX_PER_IP_PER_10_MIN) return json({ error: "Too many submissions. Please try again shortly." }, 429, origin);
    }

    const details: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(data).slice(0, 40)) details[String(k).slice(0, 60)] = clip(v, 2000);
    details._ip_hash = ipHash;
    details._user_agent = clip(req.headers.get("user-agent"), 300);

    const [row] = await sql`
      insert into public.website_leads
        (form_type, name, email, company, phone, website, preferred_warehouse, monthly_orders, message, details, page_url)
      values (
        ${formType}, ${name}, ${email.toLowerCase()},
        ${clip(data["Company"], 200)}, ${clip(data["Phone"], 50)}, ${clip(data["Website"], 500)},
        ${clip(data["Preferred warehouse"] ?? data["Location"], 50)}, ${clip(data["Monthly orders"], 50)},
        ${clip(data["Notes"] ?? data["Message"], 5000)}, ${sql.json(details)}, ${clip(body.page_url, 1000)}
      )
      returning id`;
    return json({ ok: true, id: row.id }, 200, origin);
  } catch (err) {
    console.error("website-lead insert failed", err);
    return json({ error: "Something went wrong. Please email hello@boxioship.com." }, 500, origin);
  }
});
