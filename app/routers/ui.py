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

    .advanced-toggle {
      margin-top: 14px;
      font-size: 0.8rem;
      color: var(--accent);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-weight: 600;
      user-select: none;
    }
    .advanced-options {
      margin-top: 12px;
      padding: 16px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      display: none;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .advanced-options.visible { display: grid; }
    .adv-field { display: flex; flex-direction: column; gap: 4px; }
    .adv-field label { font-size: 0.75rem; font-weight: 600; color: var(--muted); }
    .adv-field select {
      padding: 6px 8px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 0.82rem;
      background: #fff;
      outline: none;
      transition: border-color 0.15s;
    }
    .adv-field select:focus { border-color: var(--accent); }

    /* ── Tooltips ─────────────────────────────────────────────── */
    .info-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #e5e7eb;
      color: #6b7280;
      font-size: 10px;
      font-weight: bold;
      cursor: help;
      margin-left: 4px;
      position: relative;
      font-style: normal;
    }
    .tooltip {
      position: absolute;
      bottom: 150%;
      left: 50%;
      transform: translateX(-50%);
      background: #1f2937;
      color: #ffffff;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: normal;
      white-space: nowrap;
      visibility: hidden;
      opacity: 0;
      transition: opacity 0.2s, transform 0.2s;
      z-index: 10000;
      pointer-events: none;
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .tooltip::after {
      content: '';
      position: absolute;
      top: 100%;
      left: 50%;
      margin-left: -5px;
      border-width: 5px;
      border-style: solid;
      border-color: #1f2937 transparent transparent transparent;
    }
    .info-icon:hover .tooltip {
      visibility: visible;
      opacity: 1;
      transform: translateX(-50%) translateY(-2px);
    }

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

    .badge-requested          { background: #fef3c7; color: #92400e; }
    .badge-joining            { background: #e0f2fe; color: #0369a1; }
    .badge-awaiting_admission { background: #ffedd5; color: #9a3412; }
    .badge-active             { background: #dcfce7; color: #166534; }
    .badge-stopping           { background: #f3f4f6; color: #374151; }
    .badge-completed          { background: #f0fdf4; color: #15803d; }
    .badge-failed             { background: #fee2e2; color: #b91c1c; }

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

    /* ── Detail Overlay (Maestro) ───────────────────────────── */
    #detail-panel {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: #0f0f0f;
      z-index: 1000;
      display: none;
      flex-direction: column;
      overflow: hidden;
      color: #fff;
    }
    #detail-panel.open { display: flex; }

    .detail-header {
      padding: 16px 24px;
      border-bottom: 1px solid #333;
      display: flex;
      align-items: center;
      gap: 16px;
      background: #161616;
    }
    .back-btn {
      background: none; border: none; color: #fff;
      cursor: pointer; font-size: 1.4rem; padding: 4px 12px;
      border-radius: 8px; transition: background 0.2s;
    }
    .back-btn:hover { background: #333; }

    .detail-body {
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 340px;
      overflow: hidden;
    }
    .detail-content {
      padding: 40px;
      overflow-y: auto;
      border-right: 1px solid #333;
    }
    .detail-sidebar {
      padding: 24px;
      overflow-y: auto;
      background: #141414;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* Transcript Style */
    .transcript-line {
      margin-bottom: 24px;
      border-bottom: none;
    }
    .speaker-label {
      font-weight: 700;
      color: var(--accent);
      font-size: 0.9rem;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .speaker-time { font-weight: normal; color: #666; font-size: 0.75rem; }
    .speaker-text { line-height: 1.6; color: #d0d0d0; font-size: 1.05rem; }

    /* Summary Card */
    .summary-section {
      background: #1a1a1a;
      border: 1px solid var(--accent);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 40px;
      box-shadow: 0 4px 30px rgba(0,0,0,0.3);
    }
    .summary-section h3 { color: var(--accent); margin-bottom: 12px; }

    /* Sidebar Cards */
    .side-card {
      background: #1e1e1e;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 16px;
    }
    .side-card h4 {
      font-size: 0.75rem;
      color: #777;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .side-info-item {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .side-info-icon { font-size: 1.2rem; min-width: 24px; text-align: center; }
    .side-info-text .label { font-size: 0.7rem; color: #666; }
    .side-info-text .value { font-size: 0.9rem; font-weight: 500; }

    /* Status Badge */
    .status-badge-big {
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 700;
      background: #333;
    }
    .status-requested          { color: #fbbf24; background: rgba(251, 191, 36, 0.1); }
    .status-joining            { color: #38bdf8; background: rgba(56, 189, 248, 0.1); }
    .status-awaiting_admission { color: #fb923c; background: rgba(251, 146, 60, 0.1); }
    .status-active             { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
    .status-stopping           { color: #9ca3af; background: rgba(156, 163, 175, 0.1); }
    .status-completed          { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
    .status-failed             { color: #f87171; background: rgba(248, 113, 113, 0.1); }

    .btn-danger-big {
      width: 100%;
      padding: 14px;
      background: #2a1515;
      color: #f87171;
      border: 1px solid #4a2525;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 700;
      transition: all 0.2s;
    }
    .btn-danger-big:hover { background: #4a2525; }

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
      color: #1a1918;
    }
    .auth-card h2 { margin-bottom: 20px; font-size: 1.2rem; }
    .auth-card input { width: 100%; padding: 12px; margin-bottom: 12px; border: 1px solid var(--border); border-radius: 8px; text-align: center; font-size: 1.1rem; letter-spacing: 0.2em; }

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

    <!-- Advanced Toggle -->
    <div class="advanced-toggle" onclick="toggleAdvanced()">
      <span id="adv-icon">▶</span> Opciones Avanzadas
    </div>

    <!-- Advanced Options -->
    <div id="advanced-options" class="advanced-options">
      <div class="adv-field">
        <label>
          Idioma 
          <i class="info-icon">i<span class="tooltip">Idioma base para la transcripción</span></i>
        </label>
        <select id="opt-language">
          <option value="">Auto-detectar</option>
          <option value="es">Español</option>
          <option value="en">Inglés</option>
          <option value="pt">Portugués</option>
          <option value="fr">Francés</option>
          <option value="de">Alemán</option>
        </select>
      </div>
      <div class="adv-field">
        <label>
          Tarea 
          <i class="info-icon">i<span class="tooltip">Transcripción original o traducción</span></i>
        </label>
        <select id="opt-task">
          <option value="transcribe">Transcripción</option>
          <option value="translate">Traducción</option>
        </select>
      </div>
      <div class="adv-field">
        <label>
          Calidad (Tier) 
          <i class="info-icon">i<span class="tooltip">Tiempo Real (rápido) o Diferido (preciso)</span></i>
        </label>
        <select id="opt-tier">
          <option value="realtime">Tiempo Real</option>
          <option value="deferred">Diferido (Máxima precisión)</option>
        </select>
      </div>
      
      <div class="adv-field" style="grid-column: span 2; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; border-top: 1px solid var(--border); padding-top: 12px;">
        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text);">
          <input type="checkbox" id="opt-transcribe" checked /> 
          Transcribir
          <i class="info-icon">i<span class="tooltip">Habilitar captura de texto</span></i>
        </label>
        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text);">
          <input type="checkbox" id="opt-record" /> 
          Grabar reunión
          <i class="info-icon">i<span class="tooltip">Guardar respaldo de audio de la sesión</span></i>
        </label>
        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text);">
          <input type="checkbox" id="opt-telegram" checked /> 
          Notificar Telegram
          <i class="info-icon">i<span class="tooltip">Recibir resumen automático en Telegram</span></i>
        </label>
        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text);">
          <input type="checkbox" id="opt-voice-agent" /> 
          Voice Agent (Beta)
          <i class="info-icon">i<span class="tooltip">Permite al bot hablar e interactuar</span></i>
        </label>
      </div>
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

<!-- Auth Overlay -->
<div id="auth-overlay">
  <div class="auth-card">
    <h2>Acceso Restringido</h2>
    <p style="font-size: 0.9rem; color: var(--muted); margin-bottom: 20px;">Ingresá la llave de acceso para continuar.</p>
    <input type="password" id="auth-input" placeholder="••••••••" />
    <button onclick="saveApiKey()" style="width: 100%">Entrar</button>
  </div>
</div>

<!-- Detail Panel (New Professional Overlay) -->
<div id="detail-panel">
  <div class="detail-header">
    <button class="back-btn" onclick="closePanel()">←</button>
    <h2 id="panel-title">mcz-ybpw-myb</h2>
    <span id="panel-status-badge" class="status-badge-big">Status</span>
    <div style="margin-left: auto; display: flex; gap: 12px;">
      <button id="btn-export-transcript" class="btn" style="padding: 8px 16px; font-size: 0.8rem; background: #333;">Exportar</button>
    </div>
  </div>
  
  <div class="detail-body">
    <div class="detail-content" id="panel-content">
      <!-- Summary and Transcript go here -->
    </div>
    
    <div class="detail-sidebar">
      <div class="side-card">
        <h4>📋 Meeting Info</h4>
        <div class="side-info-item">
          <div class="side-info-icon">📹</div>
          <div class="side-info-text">
            <div class="label">Plataforma</div>
            <div id="side-platform" class="value">-</div>
          </div>
        </div>
        <div class="side-info-item">
          <div class="side-info-icon">📅</div>
          <div class="side-info-text">
            <div class="label">Fecha</div>
            <div id="side-date" class="value">-</div>
          </div>
        </div>
        <div class="side-info-item">
          <div class="side-info-icon">🌐</div>
          <div class="side-info-text">
            <div class="label">Idioma</div>
            <div id="side-lang" class="value">-</div>
          </div>
        </div>
      </div>
      
      <div class="side-card">
        <h4>👥 Participantes</h4>
        <div id="side-participants" style="display:flex; flex-direction:column; gap:8px;">
          <div style="color:#666; font-size:0.85rem;">Cargando...</div>
        </div>
      </div>

      <div class="side-card">
        <h4>📊 Estadísticas</h4>
        <div class="side-info-item">
          <div class="side-info-text">
            <div class="label">Intervenciones</div>
            <div id="stat-segments" class="value">0</div>
          </div>
        </div>
        <div class="side-info-item">
          <div class="side-info-text">
            <div class="label">Palabras aproximadas</div>
            <div id="stat-words" class="value">0</div>
          </div>
        </div>
      </div>

      <div class="side-card">
        <h4>📝 Notas</h4>
        <textarea id="side-notes-area" placeholder="Haz clic para añadir notas..." style="width:100%; background:none; border:none; color:#bbb; resize:none; font-size:0.9rem; min-height:100px; outline:none;"></textarea>
      </div>

      <div style="margin-top: auto;">
        <button id="btn-delete-final" class="btn-danger-big">🗑️ Borrar Reunión</button>
      </div>
    </div>
  </div>
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
  
  const maskedUrl = url.includes('key=') ? url.replace(/key=[^&]+/, 'key=***') : url;
  console.log(`[Auth] Fetching ${maskedUrl}...`);
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
let loadTimeout = null;

function debouncedLoadMeetings() {
  if (loadTimeout) clearTimeout(loadTimeout);
  loadTimeout = setTimeout(() => {
    loadMeetings();
  }, 300); // Wait 300ms for more events before fetching
}

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
  
  sseSource.onopen = () => {
    console.log('SSE connection established');
    debouncedLoadMeetings();
    if (typeof currentMeetingId !== 'undefined' && currentMeetingId && typeof currentMeetingPlatform !== 'undefined') {
      // Refresh current open meeting in case we missed events while disconnected
      openMeetingDetails(currentMeetingPlatform, currentMeetingId);
    }
  };
  
  sseSource.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      if (parsed.event === 'ping') return; // Ignore keep-alive
      
      const { event: type, data } = parsed;
      console.log('Real-time event:', type, data);
      
      let status = data.status;
      if (type === 'meeting.started') status = 'active';
      if (type === 'meeting.completed') status = 'completed';
      if (type === 'bot.failed') status = 'failed';

      debouncedLoadMeetings();
      
      const eventNativeId = data.native_meeting_id || data.nativeId;
      const eventId = data.meeting_id || data.id;

      console.log(`[SSE] Checking match: Current=${currentMeetingId} vs Event(Native=${eventNativeId}, ID=${eventId})`);

      if (currentMeetingId && (
          eventNativeId === currentMeetingId || 
          String(eventId) === String(currentMeetingId)
      )) {
        console.log(`[SSE] Match found! Updating banner to: ${status}`);
        if (status) {
          updateBannerStatus(status);
          // If the meeting just completed, refresh the details panel so the transcript appears!
          if (status === 'completed' && typeof currentMeetingPlatform !== 'undefined') {
            setTimeout(() => { openMeetingDetails(currentMeetingPlatform, currentMeetingId); }, 2000);
          }
        }
      } else {
        console.log(`[SSE] No match for current banner.`);
      }
    } catch (e) {
      console.error('SSE error:', e);
    }
  };
  
  sseSource.onerror = (e) => {
    console.warn('SSE connection lost. Reconnecting in 3s...');
    sseSource.close();
    setTimeout(setupSSE, 3000); // Re-try in 3 seconds
  };
}

/* ── Join ─────────────────────────────────────────────────── */
function toggleAdvanced() {
  const panel = document.getElementById('advanced-options');
  const icon = document.getElementById('adv-icon');
  const isVisible = panel.classList.toggle('visible');
  icon.textContent = isVisible ? '▼' : '▶';
}

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
        language: document.getElementById('opt-language').value || null,
        task: document.getElementById('opt-task').value,
        transcription_tier: document.getElementById('opt-tier').value,
        voice_agent_enabled: document.getElementById('opt-voice-agent').checked,
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
    awaiting_admission: 'Esperando a ser admitido en la reunión…',
    active:    'Reunión en progreso — capturando…',
    stopping:  'Terminando sesión y procesando…',
    completed: 'Reunión finalizada ✓',
    failed:    'Error en la reunión ✗',
  };
  document.getElementById('status-text').textContent = messages[status] || status;
  const showSpinner = ['requested', 'joining', 'awaiting_admission', 'active', 'stopping'].includes(status);
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
      <div class="meeting-item" onclick="openMeetingDetails('${m.platform}', '${m.native_meeting_id}')">
        <div class="platform-icon ${m.platform === 'google_meet' ? 'google' : m.platform === 'teams' ? 'teams' : 'zoom'}">
          ${platformLabel(m.platform)}
        </div>
        <div class="info">
          <div class="url" style="display:flex; align-items:center; gap:6px;">
            ${escHtml(m.native_meeting_id)}
            <span style="font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; background: ${m.source==='vexa'?'#f3e8ff':m.source==='local'?'#e0f2fe':'#dcfce7'}; color: ${m.source==='vexa'?'#7c3aed':m.source==='local'?'#0369a1':'#166534'};">
              ${m.source === 'vexa' ? '☁️ Vexa Only' : m.source === 'local' ? '💻 Local' : '🔄 Sync'}
            </span>
          </div>
          <div class="meta">${formatDate(m.created_at)} · ${m.platform}</div>
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
  return { 
    requested: 'Solicitado', 
    joining: 'Uniéndose', 
    awaiting_admission: 'Esperando admisión', 
    active: 'Activa', 
    stopping: 'Deteniendo...',
    completed: 'Finalizada', 
    failed: 'Error' 
  }[s] || s;
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('es-AR', { dateStyle:'short', timeStyle:'short' });
  } catch (_) { return iso; }
}

/* ── Detail panel ─────────────────────────────────────────── */
/* ── Detail Panel Logic ──────────────────────────────────── */
async function openMeetingDetails(platform, nativeId) {
  const panel = document.getElementById('detail-panel');
  const content = document.getElementById('panel-content');
  const title = document.getElementById('panel-title');
  const badge = document.getElementById('panel-status-badge');
  
  window.currentMeetingId = nativeId;
  window.currentMeetingPlatform = platform;
  title.innerText = nativeId;
  panel.classList.add('open');
  content.innerHTML = '<div style="color:#666; text-align:center; padding-top:100px;">Cargando...</div>';

  try {
    const key = getApiKey();
    const [resMeeting, resSummary, resTranscript] = await Promise.all([
      fetch(`/meetings/${platform}/${nativeId}?key=${encodeURIComponent(key)}`),
      fetch(`/meetings/${platform}/${nativeId}/summary?key=${encodeURIComponent(key)}`),
      fetch(`/meetings/${platform}/${nativeId}/transcript?key=${encodeURIComponent(key)}`)
    ]);

    if (!resMeeting.ok) throw new Error('Failed to load meeting');
    const data = await resMeeting.json();
    const summaryData = resSummary.ok ? await resSummary.json() : { summary: null };
    const transcriptData = resTranscript.ok ? await resTranscript.json() : { segments: [] };
    
    // Header & Sidebar basic info
    badge.innerText = statusLabel(data.status);
    badge.className = `status-badge-big status-${data.status.toLowerCase()}`;
    
    document.getElementById('side-platform').innerText = data.platform;
    document.getElementById('side-date').innerText = formatDate(data.created_at);
    document.getElementById('side-lang').innerText = data.language || 'Auto';
    
    // Notes logic
    const notesArea = document.getElementById('side-notes-area');
    notesArea.value = data.notes || '';
    notesArea.onblur = async () => {
      try {
        await authFetch(`/meetings/${platform}/${nativeId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ notes: notesArea.value })
        });
        console.log('Notes saved');
      } catch (e) {
        console.error('Failed to save notes', e);
      }
    };
    
    let html = '';
    
    document.getElementById('btn-export-transcript').style.display = 'block';

    if (['requested', 'joining', 'awaiting_admission', 'active', 'stopping'].includes(data.status)) {
      html += `
        <div style="text-align:center; padding: 80px 20px; background: rgba(0,0,0,0.2); border-radius: 12px; border: 1px solid #333;">
          <div class="spinner" style="margin: 0 auto 24px auto; border-color: var(--accent) transparent var(--accent) transparent; width: 40px; height: 40px; border-width: 3px;"></div>
          <h2 style="margin-bottom: 12px; font-size: 1.4rem; font-weight: 500;">Sesión en Progreso</h2>
          <p style="color:#aaa; margin-bottom: 30px; font-size: 1.05rem; line-height: 1.5; max-width: 400px; margin-left: auto; margin-right: auto;">
            El bot está actualmente en la reunión capturando el audio en tiempo real. 
            El resumen y la transcripción completa estarán disponibles una vez finalizada.
          </p>
          <button class="btn" style="background:#ef4444; color:white; font-weight:bold; padding: 12px 28px; border-radius: 8px; font-size: 1.05rem;" onclick="stopMeeting('${platform}', '${nativeId}'); closePanel();">
             Detener Bot y Finalizar
          </button>
        </div>
      `;
      document.getElementById('btn-export-transcript').style.display = 'none';
      content.innerHTML = html;
      return;
    }

    let shouldPollSummary = false;
    // 1. AI Summary Section
    const s = summaryData.summary || summaryData.summary_text;
    if (s) {
      const isStructured = summaryData.summary !== null;
      const isProcessing = typeof s === 'string' && s.includes('⏳');
      if (isProcessing) shouldPollSummary = true;
      
      html += `
        <div class="summary-section">
          <h3 style="margin:0 0 12px 0; font-size:1.1rem;">🧠 Resumen de la IA</h3>
          <p style="margin-bottom:20px; font-size:1.1rem; line-height:1.6; color:#fff;">${isStructured ? s.executive_summary : md(s)}</p>
          
          ${isProcessing ? `
            <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px dashed #444; text-align:center;">
               <div class="spinner" style="margin:0 auto 10px auto; width:20px; height:20px; border-width:2px;"></div>
               <p style="font-size:0.8rem; color:#888;">Estamos procesando la información. Esta vista se actualizará sola...</p>
            </div>
          ` : ''}
          
          ${isStructured && s.key_points && s.key_points.length ? `
            <div style="margin-top:24px;">
              <h4 style="font-size:0.75rem; color:#666; text-transform:uppercase; margin-bottom:8px;">Puntos Clave</h4>
              <ul style="list-style:disc; margin-left:20px; color:#bbb;">
                ${s.key_points.map(p => `<li style="margin-bottom:6px;">${p}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          
          ${isStructured && s.tasks && s.tasks.length ? `
            <div style="margin-top:24px;">
              <h4 style="font-size:0.75rem; color:#666; text-transform:uppercase; margin-bottom:8px;">Tareas y Compromisos</h4>
              <ul style="list-style:none;">
                ${s.tasks.map(t => `
                  <li style="background:#222; padding:12px; border-radius:10px; margin-bottom:8px; border-left:4px solid var(--accent);">
                    <strong>${t.assignee || 'Pendiente'}:</strong> ${t.description}
                  </li>
                `).join('')}
              </ul>
            </div>
          ` : ''}
        </div>
      `;
    } else {
      html += `
        <div class="summary-section" style="text-align:center; color:#666; padding:40px;">
          <p>El resumen se está generando o no hay datos suficientes.</p>
        </div>
      `;
    }

    // 2. Transcript Section & Participants
    const segments = transcriptData.segments || [];
    if (segments.length > 0) {
      
      document.getElementById('stat-segments').innerText = segments.length;
      let totalWords = 0;
      const participants = new Set();
      
      html += '<h3 style="margin:0 0 24px 0; font-size:0.85rem; color:#555; text-transform:uppercase; letter-spacing:1px;">Transcripción Completa</h3>';
      
      html += segments.map(seg => {
        totalWords += (seg.text || "").split(' ').length;
        if (seg.speaker) participants.add(seg.speaker);
        return `
          <div class="transcript-line">
            <div class="speaker-label">
              ${seg.speaker || 'Participante'} 
              <span class="speaker-time">${formatSimpleTime(seg.start !== undefined ? seg.start : seg.start_time)}</span>
            </div>
            <div class="speaker-text">${escHtml(seg.text)}</div>
          </div>
        `;
      }).join('');
      
      document.getElementById('stat-words').innerText = totalWords;

      // Update Participants UI
      const partList = document.getElementById('side-participants');
      if (participants.size > 0) {
        partList.innerHTML = Array.from(participants).map(p => `
          <div style="display:flex; align-items:center; gap:8px; font-size:0.9rem;">
            <div style="width:8px; height:8px; background:var(--accent); border-radius:50%;"></div>
            ${p}
          </div>
        `).join('');
      } else {
        partList.innerHTML = '<div style="color:#666; font-size:0.85rem;">No detectados</div>';
      }
    } else {
      html += '<div style="color:#666; text-align:center; padding:40px;">No hay transcripción disponible.</div>';
    }
    
    content.innerHTML = html;
    
    // Action Buttons
    document.getElementById('btn-export-transcript').onclick = async () => {
      try {
        const btn = document.getElementById('btn-export-transcript');
        btn.innerText = 'Generando...';
        btn.disabled = true;
        
        const res = await authFetch(`/meetings/${platform}/${nativeId}/share`, { method: 'POST' });
        const shareData = await res.json();
        
        if (res.ok && shareData.url) {
          window.open(shareData.url, '_blank');
        } else {
          alert(shareData.detail || 'No se pudo generar el enlace de exportación.');
        }
      } catch (err) {
        alert('Error al conectar con el servidor.');
      } finally {
        const btn = document.getElementById('btn-export-transcript');
        btn.innerText = 'Exportar';
        btn.disabled = false;
      }
    };

    document.getElementById('btn-delete-final').onclick = async () => {
      if (!confirm('¿Seguro que querés borrar esta sesión?')) return;
      await authFetch(`/meetings/${platform}/${nativeId}`, { method: 'DELETE' });
      closePanel();
      loadMeetings();
    };

    if (shouldPollSummary) {
      setTimeout(() => {
        if (currentMeetingId === nativeId) {
          openMeetingDetails(platform, nativeId);
        }
      }, 5000);
    }

  } catch (err) {
    content.innerHTML = `<div style="color:#f87171; text-align:center; padding:100px;">Error al cargar: ${err.message}</div>`;
  }
}

function formatSimpleTime(s) {
  if (!s) return '00:00';
  const min = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${min}:${sec.toString().padStart(2, '0')}`;
}

function closePanel() {
  document.getElementById('detail-panel').classList.remove('open');
}

function md(t) { return escHtml(t); } // Basic placeholder for markdown

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
