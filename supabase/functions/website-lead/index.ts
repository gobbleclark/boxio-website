// website-lead: receives quote/contact form submissions from boxioship.com, stores them in
// public.website_leads, then copies them into the CRM (crm_contacts / crm_companies / crm_deals /
// crm_activities). Deployed with verify_jwt = false because it's a public form endpoint; it validates
// input, checks the request origin, drops honeypot spam and rate-limits by (hashed) IP instead.
import postgres from "npm:postgres@3.4.5";

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, { prepare: false, max: 1 });

const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?boxioship\.com$/,
  /^https:\/\/boxio-website[a-z0-9-]*-boxioship\.vercel\.app$/, // Vercel production + preview deployments
  /^https:\/\/boxio-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];
const MAX_PER_IP_PER_10_MIN = 5;

// CRM settings
const LEAD_OWNER_ID = "631120de-69a5-463a-9ec0-0248a16f09dc"; // app_users: Justin Procopio (sales)
const PIPELINE_NAME = "Website Leads"; // website deals go into this pipeline's first open stage
const FREE_EMAIL_DOMAINS = new Set([
  "gmail.com", "googlemail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com", "msn.com", "icloud.com",
  "me.com", "mac.com", "aol.com", "proton.me", "protonmail.com", "ymail.com", "comcast.net", "att.net", "gmx.com",
]);

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

function domainFrom(website: string | null, email: string) {
  if (website) {
    try {
      const host = new URL(/^https?:\/\//i.test(website) ? website : "https://" + website).hostname.toLowerCase();
      if (host.includes(".")) return host.replace(/^www\./, "");
    } catch { /* fall through to email */ }
  }
  const d = email.split("@")[1]?.toLowerCase() ?? "";
  return d && !FREE_EMAIL_DOMAINS.has(d) ? d : null;
}

type Lead = {
  id: string; formType: "quote" | "contact"; name: string; email: string; company: string | null;
  phone: string | null; website: string | null; details: Record<string, unknown>;
};

// Copy one website lead into the CRM. Runs in its own transaction so a CRM problem never loses the lead.
async function syncToCrm(lead: Lead) {
  const now = new Date();
  const domain = domainFrom(lead.website, lead.email);
  const [first, ...rest] = lead.name.split(/\s+/);
  const answers = Object.entries(lead.details)
    .filter(([k, v]) => !k.startsWith("_") && v)
    .map(([k, v]) => `${k}: ${v}`)
    .join("\n");
  const isQuote = lead.formType === "quote";
  const topic = String(lead.details["Topic"] ?? "");
  const isProspect = isQuote || topic === "New fulfillment partnership";

  return await sql.begin(async (tx) => {
    // Company: match on domain, then on name; create if new
    let companyId: string | null = null;
    if (domain || lead.company) {
      const [existing] = await tx`
        select id from public.crm_companies
        where (${domain}::text is not null and lower(domain) = ${domain})
           or (${lead.company}::text is not null and lower(name) = lower(${lead.company}))
        order by (lower(domain) = ${domain}) desc nulls last limit 1`;
      if (existing) {
        companyId = existing.id;
      } else {
        const [created] = await tx`
          insert into public.crm_companies (id, name, domain, website, lifecycle_stage, owner_id, owner_name, created_at, updated_at)
          values (gen_random_uuid(), ${lead.company ?? domain}, ${domain}, ${lead.website ?? (domain ? "https://" + domain : null)},
                  ${isProspect ? "lead" : null}, ${LEAD_OWNER_ID}, 'Justin Procopio', ${now}, ${now})
          returning id`;
        companyId = created.id;
      }
    }

    // Contact: match on email; fill blanks on an existing contact rather than overwriting
    let contactId: string;
    const [contact] = await tx`select id from public.crm_contacts where lower(email) = ${lead.email} order by created_at limit 1`;
    if (contact) {
      contactId = contact.id;
      await tx`
        update public.crm_contacts set
          phone = coalesce(phone, ${lead.phone}),
          company_id = coalesce(company_id, ${companyId}),
          updated_at = ${now}
        where id = ${contactId}`;
    } else {
      const [created] = await tx`
        insert into public.crm_contacts
          (id, first_name, last_name, email, phone, company_id, lifecycle_stage, lead_status, lead_source, owner_id, owner_name, created_at, updated_at)
        values (gen_random_uuid(), ${first}, ${rest.join(" ") || null}, ${lead.email}, ${lead.phone}, ${companyId},
                ${isProspect ? "lead" : null}, ${isProspect ? "NEW" : null},
                ${isQuote ? "Website – Free quote" : "Website – Contact form"},
                ${LEAD_OWNER_ID}, 'Justin Procopio', ${now}, ${now})
        returning id`;
      contactId = created.id;
    }

    // Deal: free-quote requests and new-partnership inquiries open a deal in the Website Leads pipeline
    let dealId: string | null = null;
    if (isProspect) {
      const [stage] = await tx`
        select s.id as stage_id, p.id as pipeline_id
        from public.crm_pipelines p join public.crm_stages s on s.pipeline_id = p.id
        where p.name = ${PIPELINE_NAME} and not coalesce(p.archived, false)
          and not coalesce(s.archived, false) and s.outcome = 'open'
        order by (p.hubspot_id is not null) desc, s.sort_order nulls last limit 1`;
      if (stage) {
        const summary = ["Monthly orders", "Preferred warehouse", "Sales channels", "Services", "SKUs", "Product type", "Location", "Message"]
          .filter((k) => lead.details[k]).map((k) => `${k}: ${lead.details[k]}`).join("\n");
        const [deal] = await tx`
          insert into public.crm_deals
            (id, name, pipeline_id, stage_id, deal_type, description, company_id, owner_id, owner_name, created_at, updated_at)
          values (gen_random_uuid(), ${(lead.company ?? lead.name) + (isQuote ? " — Website quote" : " — Website inquiry")}, ${stage.pipeline_id}, ${stage.stage_id},
                  'newbusiness', ${summary || null}, ${companyId}, ${LEAD_OWNER_ID}, 'Justin Procopio', ${now}, ${now})
          returning id`;
        dealId = deal.id;
        await tx`insert into public.crm_deal_contacts (deal_id, contact_id) values (${dealId}, ${contactId}) on conflict do nothing`;
      }
    }

    // Note with everything they told us
    await tx`
      insert into public.crm_activities
        (id, type, subject, body, occurred_at, direction, company_id, contact_id, deal_id, author_name, created_at, updated_at)
      values (gen_random_uuid(), 'note', ${isQuote ? "Website free quote request" : "Website contact form: " + (topic || "message")},
              ${answers + (lead.details._page_url ? `\n\nSubmitted from: ${lead.details._page_url}` : "")},
              ${now}, 'inbound', ${companyId}, ${contactId}, ${dealId}, 'Website form', ${now}, ${now})`;

    await tx`
      update public.website_leads set
        crm_contact_id = ${contactId}, crm_company_id = ${companyId}, crm_deal_id = ${dealId},
        crm_synced_at = ${now}, crm_error = null
      where id = ${lead.id}`;
    return { contactId, companyId, dealId };
  });
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
  const email = clip(data["Email"], 320)?.toLowerCase() ?? null;
  if (!formType || !name || !email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ error: "Please include your name and a valid email." }, 422, origin);
  }

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  const ipHash = ip ? (await sha256("boxio-leads:" + ip)).slice(0, 32) : null;

  let leadId: string;
  const details: Record<string, unknown> = {};
  try {
    if (ipHash) {
      const [{ n }] = await sql`
        select count(*)::int as n from public.website_leads
        where details->>'_ip_hash' = ${ipHash} and created_at > now() - interval '10 minutes'`;
      if (n >= MAX_PER_IP_PER_10_MIN) return json({ error: "Too many submissions. Please try again shortly." }, 429, origin);
    }

    for (const [k, v] of Object.entries(data).slice(0, 40)) details[String(k).slice(0, 60)] = clip(v, 2000);
    details._ip_hash = ipHash;
    details._user_agent = clip(req.headers.get("user-agent"), 300);
    details._page_url = clip(body.page_url, 1000);

    const [row] = await sql`
      insert into public.website_leads
        (form_type, name, email, company, phone, website, preferred_warehouse, monthly_orders, message, details, page_url)
      values (
        ${formType}, ${name}, ${email},
        ${clip(data["Company"], 200)}, ${clip(data["Phone"], 50)}, ${clip(data["Website"], 500)},
        ${clip(data["Preferred warehouse"] ?? data["Location"], 50)}, ${clip(data["Monthly orders"], 50)},
        ${clip(data["Notes"] ?? data["Message"], 5000)}, ${sql.json(details)}, ${clip(body.page_url, 1000)}
      )
      returning id`;
    leadId = row.id;
  } catch (err) {
    console.error("website-lead insert failed", err);
    return json({ error: "Something went wrong. Please email hello@boxioship.com." }, 500, origin);
  }

  // CRM sync is best-effort: the lead is already saved, so a failure here is recorded, not shown to the visitor.
  try {
    await syncToCrm({
      id: leadId, formType, name, email,
      company: clip(data["Company"], 200), phone: clip(data["Phone"], 50), website: clip(data["Website"], 500), details,
    });
  } catch (err) {
    console.error("website-lead CRM sync failed", err);
    await sql`update public.website_leads set crm_error = ${String((err as Error)?.message ?? err).slice(0, 2000)} where id = ${leadId}`
      .catch(() => {});
  }

  return json({ ok: true, id: leadId }, 200, origin);
});
