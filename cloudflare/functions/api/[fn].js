// POST /api/<fn> with a JSON array of arguments — the Cloudflare twin of the google.script.run API in
// webapp/Code.js (getData), reading the same LinkedIn Posts spreadsheet through the Sheets API as the Google
// service account (Viewer on the sheet). getData returns the same JSON string as Code.js, so App.html parses
// it the same way on both hosts. Cloudflare Access sits in front of the site; this function also verifies
// the Access token itself so a misconfigured policy fails closed.

const SHEETS = "https://sheets.googleapis.com/v4/spreadsheets/";
const SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly";
const SCHEDULE_COLUMNS = ["Date", "Pillar", "Lenses", "Topic", "Status", "Rationale", "Source", "LinkedIn URL"];
const SCHEDULE_KEYS = ["date", "pillar", "lens", "topic", "status", "rationale", "source", "url"];
const POSTS_TAB = "LinkedIn Posts";
const TABS = ["Post Scores", "Agent Runs"];

let cachedToken = null; // { value, exp } — reused across requests on a warm isolate
let cachedCerts = null; // { keys, exp }

const API = { getData };

export async function onRequestPost({ request, env, params }) {
  try {
    await verifyAccess(request, env);
  } catch (e) {
    return json({ error: "Unauthorized" }, 401);
  }
  const fn = Object.hasOwn(API, params.fn) ? API[params.fn] : null;
  if (!fn) return json({ error: "Unknown function" }, 404);
  try {
    const args = await request.json().catch(() => []);
    const result = await fn(env, ...(Array.isArray(args) ? args : []));
    return json({ result }, 200);
  } catch (e) {
    console.error(params.fn + ": " + e.message);
    return json({ error: e.message }, e.status || 502);
  }
}

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" }
  });
}

/* ---------- API ---------- */

async function getData(env) {
  if (!env.SPREADSHEET_ID) throw new Error("Set the SPREADSHEET_ID var.");
  const base = SHEETS + encodeURIComponent(env.SPREADSHEET_ID);
  const meta = await sheets(env, base + "?fields=spreadsheetUrl,sheets.properties.title");
  // readTab_ in Code.js returns [] for a missing tab; batchGet fails on one, so ask only for those that exist.
  const titles = new Set(meta.sheets.map(s => s.properties.title));
  const tabs = TABS.filter(t => titles.has(t));
  const ranges = [POSTS_TAB + "!A1:I300", ...tabs].map(r => "ranges=" + encodeURIComponent(quoteRange(r)));
  const got = await sheets(env, base + "/values:batchGet?valueRenderOption=FORMATTED_VALUE&" + ranges.join("&"));
  const values = got.valueRanges.map(v => v.values || []);
  const tab = name => tabs.includes(name) ? readTab(values[1 + tabs.indexOf(name)]) : [];
  const rows = values[0];
  const runs = tab("Agent Runs").map(r => {
    try { r.change_log = r.change_log ? JSON.parse(r.change_log) : []; }
    catch (e) { r.change_log = []; }
    try { r.agent_stats = r.agent_stats ? JSON.parse(r.agent_stats) : null; }
    catch (e) { r.agent_stats = null; }
    return r;
  });
  return JSON.stringify({
    pillars: readList(rows, "Pillars"),
    lenses: readList(rows, "Lenses"),
    schedule: readSchedule(rows),
    scores: tab("Post Scores"),
    runs: runs,
    today: new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" }).format(new Date()),
    sheet_url: meta.spreadsheetUrl
  });
}

// "LinkedIn Posts!A1:I300" -> "'LinkedIn Posts'!A1:I300"
function quoteRange(r) {
  const [name, cells] = r.split("!");
  return "'" + name.replace(/'/g, "''") + "'" + (cells ? "!" + cells : "");
}

// The Sheets API drops trailing empty cells, so read every cell through this.
function cell(rows, r, c) {
  return String((rows[r] && rows[r][c]) ?? "");
}

function findCell(rows, text) {
  for (let r = 0; r < rows.length; r++) {
    const c = rows[r].indexOf(text);
    if (c >= 0) return [r, c];
  }
  throw new Error('Header "' + text + '" not found on the LinkedIn Posts tab');
}

function readList(rows, header) {
  const [r0, c] = findCell(rows, header);
  const out = [];
  for (let r = r0 + 1; r < rows.length && cell(rows, r, c); r++) out.push(cell(rows, r, c).trim());
  return out;
}

function readSchedule(rows) {
  const [r0, c] = findCell(rows, "Date");
  const header = SCHEDULE_COLUMNS.map((_, i) => cell(rows, r0, c + i));
  if (header.join("|") !== SCHEDULE_COLUMNS.join("|")) throw new Error("Unexpected schedule header: " + header.join(", "));
  const out = [];
  for (let r = r0 + 1; r < rows.length; r++) {
    const cells = SCHEDULE_KEYS.map((_, i) => cell(rows, r, c + i).trim());
    if (!cells.some(Boolean)) break;
    const rec = {};
    SCHEDULE_KEYS.forEach((k, i) => rec[k] = cells[i]);
    out.push(rec);
  }
  return out;
}

/** A header-row tab as objects keyed by slugified header ("Run ID" -> run_id). */
function readTab(rows) {
  if (!rows.length) return [];
  const keys = rows[0].map(h => String(h).trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, ""));
  return rows.slice(1).filter(r => r[0]).map(r => {
    const o = {};
    keys.forEach((k, j) => { if (k) o[k] = String(r[j] ?? ""); });
    return o;
  });
}

async function sheets(env, url) {
  const res = await fetch(url, { headers: { Authorization: "Bearer " + await googleToken(env) } });
  if (!res.ok) throw new Error("Sheets read failed (HTTP " + res.status + ").");
  return res.json();
}

/* ---------- Cloudflare Access ---------- */

async function verifyAccess(request, env) {
  if (env.DEV_NO_ACCESS === "1") return; // local `wrangler pages dev` only (.dev.vars)
  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) throw new Error("Access not configured");
  const jwt = request.headers.get("Cf-Access-Jwt-Assertion");
  if (!jwt) throw new Error("Missing Access token");
  const [h, p, s] = jwt.split(".");
  const header = JSON.parse(b64urlDecodeText(h));
  const claims = JSON.parse(b64urlDecodeText(p));
  const issuer = "https://" + env.ACCESS_TEAM_DOMAIN;
  if (claims.iss !== issuer) throw new Error("Bad issuer");
  const allowed = env.ACCESS_AUD.split(",").map(s => s.trim()).filter(Boolean);
  const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!aud.some(a => allowed.includes(a))) throw new Error("Bad audience");
  if (!claims.exp || claims.exp * 1000 < Date.now()) throw new Error("Expired");
  const jwk = (await accessCerts(issuer)).find(k => k.kid === header.kid);
  if (!jwk) throw new Error("Unknown key");
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64urlDecode(s), new TextEncoder().encode(h + "." + p));
  if (!ok) throw new Error("Bad signature");
}

async function accessCerts(issuer) {
  if (cachedCerts && cachedCerts.exp > Date.now()) return cachedCerts.keys;
  const res = await fetch(issuer + "/cdn-cgi/access/certs");
  if (!res.ok) throw new Error("Access certs HTTP " + res.status);
  const keys = (await res.json()).keys;
  cachedCerts = { keys, exp: Date.now() + 60 * 60 * 1000 };
  return keys;
}

/* ---------- Google service account ---------- */

async function googleToken(env) {
  if (cachedToken && cachedToken.exp > Date.now() + 60 * 1000) return cachedToken.value;
  // Accept the value as written in .dev.vars, where it may be wrapped in quotes.
  const sa = JSON.parse(env.GOOGLE_SA_KEY.trim().replace(/^'([\s\S]*)'$/, "$1"));
  const now = Math.floor(Date.now() / 1000);
  const enc = obj => b64url(new TextEncoder().encode(JSON.stringify(obj)));
  const unsigned = enc({ alg: "RS256", typ: "JWT" }) + "." +
    enc({ iss: sa.client_email, scope: SCOPE, aud: sa.token_uri, iat: now, exp: now + 3600 });
  const der = b64Decode(sa.private_key.replace(/-----[^-]+-----/g, "").replace(/\s+/g, ""));
  const key = await crypto.subtle.importKey("pkcs8", der, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(unsigned)));
  const res = await fetch(sa.token_uri, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: unsigned + "." + b64url(sig)
    })
  });
  if (!res.ok) throw new Error("Google sign-in failed (HTTP " + res.status + ").");
  const data = await res.json();
  cachedToken = { value: data.access_token, exp: Date.now() + data.expires_in * 1000 };
  return cachedToken.value;
}

/* ---------- base64 helpers ---------- */

function base64(bytes) {
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}
function b64url(bytes) {
  return base64(bytes).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64Decode(str) {
  return Uint8Array.from(atob(str), c => c.charCodeAt(0));
}
function b64urlDecode(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  return b64Decode(str + "=".repeat((4 - str.length % 4) % 4));
}
function b64urlDecodeText(str) {
  return new TextDecoder().decode(b64urlDecode(str));
}
