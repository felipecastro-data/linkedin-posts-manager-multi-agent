/**
 * LinkedIn Posts — read-only viewer web app (deploy: Execute as me, Access: Only myself).
 * Reads the LinkedIn Posts, Post Scores and Agent Runs tabs that /linkedin-ideas
 * writes, and hands them to Index.html as one JSON payload.
 *
 * Optional script property SPREADSHEET_ID overrides the default below.
 */

const DEFAULT_SPREADSHEET_ID = '1zKbL54y6twj1ySJu1zjPuJwoo8frfXE1aBc82jsbMsA';
const SCHEDULE_COLUMNS = ['Date', 'Pillar', 'Lenses', 'Topic', 'Status', 'Rationale', 'Source', 'LinkedIn URL', 'Shape'];
const SCHEDULE_KEYS = ['date', 'pillar', 'lens', 'topic', 'status', 'rationale', 'source', 'url', 'shape'];

function doGet() {
  return HtmlService.createTemplateFromFile('Index').evaluate()
    .setTitle('LinkedIn Posts')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover')
    .setFaviconUrl('https://www.gstatic.com/images/branding/product/1x/apps_script_48dp.png');
}

function include(name) {
  return HtmlService.createHtmlOutputFromFile(name).getContent();
}

function spreadsheet_() {
  const id = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID') || DEFAULT_SPREADSHEET_ID;
  return SpreadsheetApp.openById(id);
}

function findCell_(rows, text) {
  for (let r = 0; r < rows.length; r++) {
    const c = rows[r].indexOf(text);
    if (c >= 0) return [r, c];
  }
  throw new Error('Header "' + text + '" not found on the LinkedIn Posts tab');
}

function readList_(rows, header) {
  const [r0, c] = findCell_(rows, header);
  const out = [];
  for (let r = r0 + 1; r < rows.length && rows[r][c]; r++) out.push(rows[r][c].trim());
  return out;
}

function readSchedule_(rows) {
  const [r0, c] = findCell_(rows, 'Date');
  const header = SCHEDULE_COLUMNS.map((_, i) => rows[r0][c + i]);
  if (header.join('|') !== SCHEDULE_COLUMNS.join('|')) throw new Error('Unexpected schedule header: ' + header.join(', '));
  const out = [];
  for (let r = r0 + 1; r < rows.length; r++) {
    const cells = SCHEDULE_KEYS.map((_, i) => String(rows[r][c + i] || '').trim());
    if (!cells.some(Boolean)) break;
    const rec = {};
    SCHEDULE_KEYS.forEach((k, i) => rec[k] = cells[i]);
    out.push(rec);
  }
  return out;
}

/** A header-row tab as objects keyed by slugified header ("Run ID" -> run_id). */
function readTab_(ss, name) {
  const sh = ss.getSheetByName(name);
  if (!sh) return [];
  const rows = sh.getDataRange().getDisplayValues();
  if (!rows.length) return [];
  const keys = rows[0].map(h => h.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, ''));
  return rows.slice(1).filter(r => r[0]).map(r => {
    const o = {};
    keys.forEach((k, i) => { if (k) o[k] = r[i]; });
    return o;
  });
}

function getData() {
  const ss = spreadsheet_();
  const rows = ss.getSheetByName('LinkedIn Posts').getRange('A1:J300').getDisplayValues();
  const runs = readTab_(ss, 'Agent Runs').map(r => {
    try { r.change_log = r.change_log ? JSON.parse(r.change_log) : []; }
    catch (e) { r.change_log = []; }
    try { r.agent_stats = r.agent_stats ? JSON.parse(r.agent_stats) : null; }
    catch (e) { r.agent_stats = null; }
    return r;
  });
  return JSON.stringify({
    pillars: readList_(rows, 'Pillars'),
    lenses: readList_(rows, 'Lenses'),
    schedule: readSchedule_(rows),
    scores: readTab_(ss, 'Post Scores'),
    runs: runs,
    today: Utilities.formatDate(new Date(), 'America/Bogota', 'yyyy-MM-dd'),
    sheet_url: ss.getUrl()
  });
}
