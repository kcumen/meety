"""
Web UI router — serves the single-page dashboard.
GET /  →  index.html
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index():
    """Serve the meety single-page dashboard."""
    return _HTML


_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Meety — Bot de reuniones</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <style>
    /* ── Reset & base ─────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #f8f7f4;
      --surface:  #ffffff;
      --border:   #e2e0db;
      --text:     #1a1918;
      --muted:    #8a8880;
      --accent:   #2563eb;
      --accent-h: #1d4ed8;
      --green:    #16a34a;
      --red:      #dc2626;
      --radius:   8px;
    }

    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100dvh;
      display: flex;
      flex-direction: column;
    }

    /* ── Header ───────────────────────────────────────────────── */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 14px 24px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    header h1 {
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .badge {
      font-size: 0.7rem;
      background: var(--accent);
      color: #fff;
      padding: 2px 8px;
      border-radius: 20px;
      font-weight: 600;
    }

    /* ── Main ──────────────────────────────────────────────────── */
    main {
      flex: 1;
      max-width: 640px;
      margin: 0 auto;
      padding: 32px 20px;
      width: 100%;
    }

    /* ── Join form ────────────────────────────────────────────── */
    .join-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 32px;
    }

    .join-card h2 {
      font-size: 0.85rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin-bottom: 16px;
    }

    .input-row {
      display: flex;
      gap: 10px;
    }

    input[type="url"] {
      flex: 1;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      font-size: 0.95rem;
      font-family: inherit;
      background: var(--bg);
      outline: none;
      transition: border-color 0.15s;
    }

    input[type="url"]:focus {
      border-color: var(--accent);
    }

    button {
      padding: 10px 20px;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: var(--radius);
      font-size: 0.9rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: background 0.15s;
      white-space: nowrap;
    }

    button:hover:not(:disabled) { background: var(--accent-h); }
    button:disabled { opacity: 0.55; cursor: not-allowed; }

    .form-error {
      margin-top: 10px;
      font-size: 0.85rem;
      color: var(--red);
      min-height: 18px;
    }

    .bot-name-row {
      margin-top: 10px;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.82rem;
      color: var(--muted);
    }
    .bot-name-row input {
      flex: 1;
      padding: 6px 12px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--bg);
      font-size: 0.82rem;
      font-family: inherit;
      outline: none;
      transition: border-color 0.15s;
    }
    .bot-name-row input:focus { border-color: var(--accent); }

    /* ── Options row ──────────────────────────────────────────── */
    .options {
      margin-top: 12px;
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }

    .options label {
      font-size: 0.82rem;
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
    }

    .options input[type="checkbox"] { cursor: pointer; }

    /* ── Status banner ────────────────────────────────────────── */
    .status-banner {
      margin-top: 16px;
      padding: 12px 16px;
      border-radius: var(--radius);
      font-size: 0.88rem;
      display: none;
      align-items: center;
      gap: 10px;
    }

    .status-banner.visible { display: flex; }

    .status-banner.requested,
    .status-banner.joining,
    .status-banner.active {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e40af;
    }

    .status-banner.completed {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      color: #15803d;
    }

    .status-banner.failed {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #b91c1c;
    }

    .spinner {
      width: 14px;
      height: 14px;
      border: 2px solid currentColor;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      flex-shrink: 0;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    /* ── Section titles ───────────────────────────────────────── */
    h3 {
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin-bottom: 12px;
    }

    /* ── Meetings list ────────────────────────────────────────── */
    .meetings-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .meeting-item {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      transition: border-color 0.15s;
    }

    .meeting-item:hover { border-color: var(--accent); }

    .meeting-item .platform-icon {
      width: 32px;
      height: 32px;
      border-radius: 6px;
      background: var(--bg);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--muted);
      flex-shrink: 0;
      text-transform: uppercase;
    }

    .meeting-item .platform-icon.google { background: #e8f0fe; color: #1a73e8; }
    .meeting-item .platform-icon.teams  { background: #f3e8ff; color: #7c3aed; }
    .meeting-item .platform-icon.zoom   { background: #e0f2fe; color: #0369a1; }

    .meeting-item .info { flex: 1; min-width: 0; }

    .meeting-item .url {
      font-size: 0.85rem;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .meeting-item .meta {
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 2px;
    }

    .meeting-item .status-badge {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 20px;
      flex-shrink: 0;
    }

    .badge-failed     { background: #fee2e2; color: #b91c1c; }

    .btn-stop {
      background: #fee2e2;
      color: #b91c1c;
      padding: 6px 10px;
      font-size: 0.72rem;
      font-weight: 700;
      border-radius: var(--radius);
      border: 1px solid #fecaca;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s;
      z-index: 10;
    }

    .btn-stop:hover {
      background: #fecaca;
      border-color: #f87171;
    }

    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    /* ── Transcript lines ─────────────────────────────────────── */
    .transcript-line {
      padding: 10px 0;
      border-bottom: 1px solid #f0f0f0;
      font-size: 0.9rem;
      line-height: 1.5;
    }

    .transcript-line:last-child { border-bottom: none; }

    .transcript-line .speaker {
      font-weight: 700;
      color: var(--accent);
      margin-right: 6px;
      font-size: 0.75rem;
      text-transform: uppercase;
      display: block;
      margin-bottom: 2px;
    }

    .transcript-line .text {
      color: var(--text);
    }

    /* ── Summary card ─────────────────────────────────────────── */
    .summary-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      margin-top: 24px;
      display: none;
    }

    .summary-card.visible { display: block; }

    .summary-card h4 {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin-top: 16px;
      margin-bottom: 6px;
    }

    .summary-card h4:first-child { margin-top: 0; }

    .summary-card p {
      font-size: 0.92rem;
      line-height: 1.6;
      color: var(--text);
    }

    .summary-card ul {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .summary-card li {
      font-size: 0.88rem;
      padding: 8px 12px;
      background: var(--bg);
      border-radius: 6px;
      line-height: 1.4;
    }

    .summary-card li strong { font-weight: 600; }

    /* ── Detail panel (slide-in) ─────────────────────────────── */
    #detail-panel {
      position: fixed;
      top: 0; right: 0;
      width: min(480px, 100vw);
      height: 100dvh;
      background: var(--surface);
      border-left: 1px solid var(--border);
      box-shadow: -4px 0 24px rgba(0,0,0,0.08);
      overflow-y: auto;
      transform: translateX(100%);
      transition: transform 0.25s ease;
      z-index: 100;
      display: flex;
      flex-direction: column;
    }

    #detail-panel.open { transform: translateX(0); }

    .panel-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      background: var(--surface);
    }

    .panel-header h2 { font-size: 1rem; }

    .close-btn {
      background: none;
      border: none;
      font-size: 1.4rem;
      cursor: pointer;
      color: var(--muted);
      padding: 4px 8px;
      border-radius: 4px;
      line-height: 1;
    }

    .close-btn:hover { background: var(--bg); color: var(--text); }

    .panel-body { padding: 20px; flex: 1; }

    .panel-url {
      font-size: 0.8rem;
      color: var(--muted);
      word-break: break-all;
      margin-bottom: 16px;
    }

    .panel-section { margin-top: 20px; }
    .panel-section:first-child { margin-top: 0; }

    .panel-section h4 {
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin-bottom: 8px;
    }

    .panel-section p {
      font-size: 0.9rem;
      line-height: 1.6;
    }

    .panel-section ul {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .panel-section li {
      font-size: 0.88rem;
      background: var(--bg);
      padding: 8px 12px;
      border-radius: 6px;
    }

    /* ── Overlay ──────────────────────────────────────────────── */
    #overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.3);
      z-index: 99;
      display: none;
    }

    #overlay.visible { display: block; }

    /* ── Auth Overlay ────────────────────────────────────────── */
    #auth-overlay {
      position: fixed;
      inset: 0;
      background: rgba(255,255,255,0.95);
      z-index: 9999;
      display: none;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(4px);
    }
    #auth-overlay.visible { display: flex; }
    .auth-card {
      background: #fff;
      padding: 32px;
      border-radius: 12px;
      box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
      width: 100%;
      max-width: 360px;
      text-align: center;
    }
    .auth-card h2 { margin-bottom: 20px; font-size: 1.2rem; }
    .auth-card input { width: 100%; padding: 12px; margin-bottom: 12px; border: 1px solid var(--border); border-radius: 8px; text-align: center; font-size: 1.1rem; letter-spacing: 0.2em; }
  </style>
</head>
<body>

<!-- ── Header ─────────────────────────────────────────── -->
<header>
  <h1>Meety</h1>
  <span class="badge">Beta</span>
</header>

<!-- ── Main ───────────────────────────────────────────── -->
<main>

  <!-- Join form -->
  <div class="join-card">
    <h2>Unir reunión</h2>
    <div class="input-row">
      <input
        type="url"
        id="url-input"
        placeholder="https://meet.google.com/... | https://teams.microsoft.com/... | https://zoom.us/..."
        autocomplete="off"
        spellcheck="false"
      />
      <button id="join-btn" onclick="joinMeeting()">Unirse</button>
    </div>

    <div class="bot-name-row">
      <label for="bot-name-input">Nombre del bot:</label>
      <input type="text" id="bot-name-input" value="KcuBot | kcumen.co" placeholder="Ej: KcuBot | kcumen.co" />
    </div>

    <div id="form-error" class="form-error"></div>

    <!-- Options -->
    <div class="options">
      <label><input type="checkbox" id="opt-transcribe" checked /> Transcribir</label>
      <label><input type="checkbox" id="opt-record" /> Grabar</label>
      <label><input type="checkbox" id="opt-telegram" checked /> Notificar Telegram</label>
    </div>

    <!-- Status banner -->
    <div id="status-banner" class="status-banner">
      <div class="spinner" id="status-spinner"></div>
      <span id="status-text"></span>
    </div>
  </div>

  <!-- Meetings list -->
  <section>
    <h3>Reuniones</h3>
    <div id="meetings-list" class="meetings-list"></div>
  </section>

  <!-- Summary (inline, shown after a meeting in the list is clicked) -->
  <div id="summary-card" class="summary-card"></div>

</main>

<!-- ── Detail panel ────────────────────────────────────── -->
<div id="overlay" onclick="closePanel()"></div>

<!-- Auth Overlay -->
<div id="auth-overlay">
  <div class="auth-card">
    <h2>Acceso Restringido</h2>
    <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 20px;">Ingresá la llave de acceso para continuar.</p>
    <input type="password" id="auth-input" placeholder="••••••••" />
    <button onclick="saveApiKey()" style="width: 100%">Entrar</button>
  </div>
</div>
<div id="detail-panel">
  <div class="panel-header">
    <h2>Detalle</h2>
    <button class="close-btn" onclick="closePanel()">×</button>
  </div>
  <div class="panel-body" id="panel-body"></div>
</div>

<script>
// ── Authentication (Scrambled Storage) ─────────────────────────
const _S = 'meety-v1-salt'; // Internal salt for scrambling

function _scramble(t) {
  const x = t.split('').map((c, i) => String.fromCharCode(c.charCodeAt(0) ^ _S.charCodeAt(i % _S.length))).join('');
  return 'mty:' + btoa(x);
}

function _unscramble(t) {
  if (!t.startsWith('mty:')) return t; // Already plain
  try {
    const b = t.substring(4);
    return atob(b).split('').map((c, i) => String.fromCharCode(c.charCodeAt(0) ^ _S.charCodeAt(i % _S.length))).join('');
  } catch(_) { return ''; }
}

function getApiKey() {
  let tk = localStorage.getItem('_m_tk') || localStorage.getItem('meety_api_key') || '';
  if (!tk) return '';
  
  if (!tk.startsWith('mty:')) {
    // Migration: it's plain text, so scramble it
    const plain = tk;
    const scrambled = _scramble(plain);
    localStorage.setItem('_m_tk', scrambled);
    localStorage.removeItem('meety_api_key');
    return plain;
  }
  
  return _unscramble(tk);
}

function saveApiKey() {
  const val = document.getElementById('auth-input').value;
  if (!val) return;
  localStorage.setItem('_m_tk', _scramble(val));
  localStorage.removeItem('meety_api_key'); // Clean up old key
  document.getElementById('auth-overlay').classList.remove('visible');
  loadMeetings();
  setupSSE();
}

async function authFetch(url, options = {}) {
  const headers = options.headers || {};
  headers['X-Meety-API-Key'] = getApiKey();
  
  console.log(`[Auth] Fetching ${url}...`);
  const res = await window.fetch(url, { ...options, headers });
  
  if (res.status === 401) {
    console.error('[Auth] Error 401: Llave inválida o faltante.');
    document.getElementById('auth-overlay').classList.add('visible');
    document.getElementById('auth-input').focus();
    // Backup alert in case CSS fails to show overlay
    if (!document.querySelector('#auth-overlay.visible')) {
       alert('Acceso restringido. Por favor ingresá la llave.');
    }
  }
  
  return res;
}

// ── Utilities ──────────────────────────────────────────────────

function md(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\\n/g, '<br>');
}

/* ── State ────────────────────────────────────────────────── */
let currentMeetingId = null;

/* ── Init ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  loadMeetings();
  setupSSE();
  
  // Enter key on input triggers join
  document.getElementById('url-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') joinMeeting();
  });
});

/* ── SSE ──────────────────────────────────────────────────── */
let sseSource = null;

function setupSSE() {
  const key = getApiKey();
  if (!key) return; // Don't even try without a key
  
  if (sseSource) sseSource.close();
  
  sseSource = new EventSource('/meetings/events?key=' + key);
  
  sseSource.onmessage = (event) => {
    try {
      const { event: type, data } = JSON.parse(event.data);
      console.log('Real-time event:', type, data);
      
      let status = data.status;
      if (type === 'meeting.started') status = 'active';
      if (type === 'meeting.completed') status = 'completed';
      if (type === 'bot.failed') status = 'failed';

      loadMeetings();
      
      if (currentMeetingId && (
          data.native_meeting_id === currentMeetingId || 
          data.meeting_id === currentMeetingId || 
          data.id === parseInt(currentMeetingId)
      )) {
        if (status) updateBannerStatus(status);
        if (status === 'completed') loadMeetings();
      }
    } catch (e) {
      console.error('SSE error:', e);
    }
  };
  
  sseSource.onerror = (e) => {
    console.warn('SSE connection lost. It will auto-retry or restart on login.');
    // If it's a 401, close it to stop the spam
    if (sseSource.readyState === EventSource.CLOSED) {
       // already closed
    }
  };
}

/* ── Join ─────────────────────────────────────────────────── */
async function joinMeeting() {
  const input = document.getElementById('url-input');
  const btn = document.getElementById('join-btn');
  const errorEl = document.getElementById('form-error');
  errorEl.textContent = '';

  const url = input.value.trim();
  if (!url) { errorEl.textContent = 'Pegá una URL válida.'; return; }

  btn.disabled = true;
  hideStatusBanner();

  try {
    const res = await authFetch('/meetings/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        bot_name: document.getElementById('bot-name-input').value.trim() || 'KcuBot | kcumen.co',
        transcribe_enabled: document.getElementById('opt-transcribe').checked,
        recording_enabled:   document.getElementById('opt-record').checked,
        notify_telegram:     document.getElementById('opt-telegram').checked,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.detail || 'Error al crear reunión.';
      btn.disabled = false;
      return;
    }

    input.value = '';
    btn.disabled = false;
    currentMeetingId = data.native_meeting_id; // Store to filter SSE

    showStatusBanner(data.status, `Reunión creada (ID ${data.id}) — esperando bot…`);
    loadMeetings();

  } catch (e) {
    errorEl.textContent = 'No se pudo conectar con el servidor.';
    btn.disabled = false;
  }
}

/* ── Status banner ────────────────────────────────────────── */
function showStatusBanner(status, message) {
  const banner = document.getElementById('status-banner');
  const spinner = document.getElementById('status-spinner');
  const text = document.getElementById('status-text');
  banner.className = `status-banner visible ${status}`;
  const showSpinner = ['requested', 'joining', 'active'].includes(status);
  spinner.style.display = showSpinner ? 'block' : 'none';
  text.textContent = message;
}

function updateBannerStatus(status) {
  const banner = document.getElementById('status-banner');
  banner.className = `status-banner visible ${status}`;
  const messages = {
    requested: 'Esperando respuesta de vexa.ai…',
    joining:   'Bot uniéndose a la reunión…',
    active:    'Reunión en progreso — grabando…',
    completed: 'Reunión finalizada ✓',
    failed:    'Error en la reunión ✗',
  };
  document.getElementById('status-text').textContent = messages[status] || status;
  const showSpinner = ['requested', 'joining', 'active'].includes(status);
  document.getElementById('status-spinner').style.display = showSpinner ? 'block' : 'none';
}

async function stopMeeting(platform, nativeId) {
  if (!confirm('¿Seguro que querés terminar la sesión del bot?')) return;
  
  try {
    const res = await authFetch(`/meetings/${platform}/${nativeId}/stop`, { method: 'POST' });
    if (res.ok) {
      console.log('Stop request sent');
      loadMeetings();
    } else {
      alert('Error al intentar detener el bot.');
    }
  } catch (e) {
    console.error('Error stopping meeting:', e);
  }
}

function hideStatusBanner() {
  const banner = document.getElementById('status-banner');
  if (banner) banner.className = 'status-banner';
}

/* ── Meetings list ────────────────────────────────────────── */
async function loadMeetings() {
  try {
    const res = await authFetch('/meetings');
    const data = await res.json();
    const list = document.getElementById('meetings-list');

    if (!data.meetings || data.meetings.length === 0) {
      list.innerHTML = '<div class="empty-state">Aún no hay reuniones. Arrancá pegando una URL arriba.</div>';
      return;
    }

    list.innerHTML = data.meetings.map(m => `
      <div class="meeting-item" onclick="openMeeting('${m.id}')">
        <div class="platform-icon ${m.platform === 'google_meet' ? 'google' : m.platform === 'teams' ? 'teams' : 'zoom'}">
          ${platformLabel(m.platform)}
        </div>
        <div class="info">
          <div class="url">${escHtml(m.meeting_url)}</div>
          <div class="meta">${formatDate(m.created_at)} · ID ${m.id}</div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          ${['requested','joining','active'].includes(m.status) ? `
            <button class="btn-stop" onclick="event.stopPropagation(); stopMeeting('${m.platform}', '${m.native_meeting_id}')" title="Terminar sesión">
              ⏹ Parar
            </button>
          ` : ''}
          <span class="status-badge badge-${m.status}">${statusLabel(m.status)}</span>
        </div>
      </div>
    `).join('');
  } catch (_) {
    document.getElementById('meetings-list').innerHTML =
      '<div class="empty-state">Error al cargar reuniones.</div>';
  }
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function platformLabel(p) {
  return { google_meet: 'G', teams: 'T', zoom: 'Z' }[p] || '?';
}

function statusLabel(s) {
  return { requested:'Esperando', joining:'Uniéndose', active:'Activa', completed:'Finalizada', failed:'Error' }[s] || s;
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('es-AR', { dateStyle:'short', timeStyle:'short' });
  } catch (_) { return iso; }
}

/* ── Detail panel ─────────────────────────────────────────── */
async function openMeeting(id) {
  const res = await authFetch(`/meetings/${encodeURIComponent(id)}`);
  if (!res.ok) return;
  const m = await res.json();

  // Fetch summary if available
  const sumRes = await authFetch(`/meetings/${encodeURIComponent(id)}/summary`);
  let summary = null;
  if (sumRes.ok) {
    const sumData = await sumRes.json();
    if (sumData.summary) summary = sumData.summary;
  }

  const body = document.getElementById('panel-body');
  body.innerHTML = `
    <div class="panel-url">${escHtml(m.meeting_url)}</div>

    <div class="panel-section">
      <h4>Estado</h4>
      <p><span class="status-badge badge-${m.status}">${statusLabel(m.status)}</span></p>
    </div>

    ${summary ? `
      <div class="panel-section">
        <h4>Resumen Ejecutivo</h4>
        <div class="md-content">${md(summary.executive_summary)}</div>
      </div>
      
      ${summary.key_points && summary.key_points.length ? `
        <div class="panel-section">
          <h4>Puntos Clave</h4>
          <ul>${summary.key_points.map(p => `<li>${md(p)}</li>`).join('')}</ul>
        </div>
      ` : ''}
      
      ${summary.tasks && summary.tasks.length ? `
        <div class="panel-section">
          <h4>Tareas</h4>
          <ul>${summary.tasks.map(t => `<li><strong>${escHtml(t.owner || '—')}</strong>: ${md(t.title)}</li>`).join('')}</ul>
        </div>
      ` : ''}
      
      ${summary.commitments && summary.commitments.length ? `
        <div class="panel-section">
          <h4>Compromisos</h4>
          <ul>${summary.commitments.map(c => `<li><strong>${escHtml(c.owner || '—')}</strong>: ${md(c.commitment)}</li>`).join('')}</ul>
        </div>
      ` : ''}
    ` : `
      <div class="panel-section"><p style="color:var(--muted);font-size:0.88rem">${['requested','joining','active'].includes(m.status) ? 'La reunión aún está en curso. El resumen aparece cuando termina.' : 'No hay resumen disponible.'}</p></div>
    `}
  `;

  document.getElementById('overlay').classList.add('visible');
  document.getElementById('detail-panel').classList.add('open');
}

function closePanel() {
  document.getElementById('overlay').classList.remove('visible');
  document.getElementById('detail-panel').classList.remove('open');
}

/* ── Inline summary (shown after own meeting completes) ─────── */
function showSummaryInline(m) {
  const card = document.getElementById('summary-card');
  card.innerHTML = `
    <h4>Resumen — reunión #${m.id}</h4>
    <p style="color:var(--muted);font-size:0.88rem;margin-top:8px">
      El resumen aparecerá aquí cuando el bot termine de procesarlo.
    </p>
  `;
  card.classList.add('visible');
}
</script>
</body>
</html>
"""
