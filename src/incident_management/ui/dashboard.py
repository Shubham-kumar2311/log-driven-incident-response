DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Incident Management — Analyst Dashboard</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --bg: #0f1117;
      --surface: #161b22;
      --surface2: #1c2333;
      --border: #30363d;
      --text: #e1e4e8;
      --text2: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --yellow: #d29922;
      --red: #f85149;
      --orange: #db6d28;
      --purple: #bc8cff;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      overflow-x: hidden;
    }

    a {
      color: var(--accent);
      text-decoration: none;
    }

    /* ── Header ── */
    .header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .header h1 {
      font-size: 16px;
      font-weight: 600;
    }

    .header .status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--text2);
    }

    .header .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
    }

    /* ── Layout ── */
    .container {
      display: flex;
      height: calc(100vh - 49px);
    }

    /* ── Sidebar ── */
    .sidebar {
      width: 380px;
      min-width: 320px;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      background: var(--surface);
    }

    .filters {
      padding: 12px;
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .filters select,
    .filters input {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 5px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    .filters select {
      cursor: pointer;
    }

    /* ── Incident list ── */
    .incident-list {
      flex: 1;
      overflow-y: auto;
      padding: 4px 0;
    }

    .incident-item {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      transition: background 0.15s;
    }

    .incident-item:hover,
    .incident-item.active {
      background: var(--surface2);
    }

    .incident-item .top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }

    .incident-item .id {
      font-size: 13px;
      font-weight: 600;
      font-family: monospace;
    }

    .incident-item .sev {
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 3px;
      font-weight: 600;
      text-transform: uppercase;
    }

    /* ── Severity colours ── */
    .sev-critical  { background: rgba(248, 81,  73,  0.20); color: var(--red);    }
    .sev-high      { background: rgba(219,109,  40,  0.20); color: var(--orange); }
    .sev-medium    { background: rgba(210,153,  34,  0.20); color: var(--yellow); }
    .sev-low       { background: rgba( 63,185,  80,  0.15); color: var(--green);  }
    .sev-info      { background: rgba( 88,166, 255,  0.15); color: var(--accent); }

    .incident-item .desc {
      font-size: 12px;
      color: var(--text2);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .incident-item .meta {
      font-size: 11px;
      color: var(--text2);
      margin-top: 4px;
      display: flex;
      gap: 10px;
    }

    /* ── Status badges ── */
    .stat-badge         { font-size: 11px; padding: 1px 6px; border-radius: 3px; font-weight: 500; }
    .stat-open          { background: rgba( 63,185, 80,  0.15); color: var(--green);  }
    .stat-investigating { background: rgba( 88,166,255,  0.15); color: var(--accent); }
    .stat-mitigated     { background: rgba(210,153, 34,  0.15); color: var(--yellow); }
    .stat-resolved      { background: rgba(188,140,255,  0.15); color: var(--purple); }
    .stat-closed        { background: rgba(139,148,158,  0.15); color: var(--text2);  }

    /* ── Main panel ── */
    .main {
      flex: 1;
      overflow-y: auto;
      padding: 0;
    }

    .empty-state {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text2);
      font-size: 14px;
    }

    /* ── Detail view ── */
    .detail {
      padding: 20px 24px;
    }

    .detail-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }

    .detail-header h2 {
      font-size: 18px;
      font-weight: 600;
    }

    .detail-header .actions {
      display: flex;
      gap: 8px;
    }

    /* ── Buttons ── */
    .btn {
      padding: 6px 14px;
      border-radius: 5px;
      border: 1px solid var(--border);
      background: var(--surface2);
      color: var(--text);
      font-size: 12px;
      cursor: pointer;
      transition: background 0.15s;
    }

    .btn:hover {
      background: var(--border);
    }

    .btn-primary {
      background: rgba(88, 166, 255, 0.15);
      border-color: var(--accent);
      color: var(--accent);
    }

    .btn-primary:hover {
      background: rgba(88, 166, 255, 0.25);
    }

    .btn-danger {
      background: rgba(248, 81, 73, 0.10);
      border-color: var(--red);
      color: var(--red);
    }

    /* ── Info grid ── */
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
      margin-bottom: 20px;
    }

    .info-card {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px 14px;
    }

    .info-card .label {
      font-size: 11px;
      color: var(--text2);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 2px;
    }

    .info-card .value {
      font-size: 14px;
      font-weight: 600;
    }

    /* ── Tabs ── */
    .tabs {
      display: flex;
      border-bottom: 1px solid var(--border);
      margin-bottom: 16px;
    }

    .tab {
      padding: 8px 16px;
      font-size: 13px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      color: var(--text2);
      transition: all 0.15s;
    }

    .tab:hover {
      color: var(--text);
    }

    .tab.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
    }

    .tab-content {
      display: none;
    }

    .tab-content.active {
      display: block;
    }

    /* ── Timeline ── */
    .timeline-item {
      display: flex;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
    }

    .timeline-item:last-child {
      border-bottom: none;
    }

    .tl-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent);
      margin-top: 5px;
      flex-shrink: 0;
    }

    .tl-dot.created  { background: var(--green);  }
    .tl-dot.status   { background: var(--yellow); }
    .tl-dot.signal   { background: var(--purple); }
    .tl-dot.note     { background: var(--orange); }
    .tl-dot.response { background: var(--red);    }

    .timeline-item .tl-time  { font-size: 11px; color: var(--text2); }
    .timeline-item .tl-desc  { font-size: 13px; }
    .timeline-item .tl-actor { font-size: 11px; color: var(--text2); }

    /* ── Notes ── */
    .note-form {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
    }

    .note-form input,
    .note-form textarea {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 6px 10px;
      border-radius: 4px;
      font-size: 13px;
      font-family: inherit;
    }

    .note-form textarea {
      flex: 1;
      resize: vertical;
      min-height: 36px;
    }

    .note-item {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      margin-bottom: 8px;
    }

    .note-item .note-meta { font-size: 11px; color: var(--text2); margin-bottom: 4px; }
    .note-item .note-body { font-size: 13px; }

    /* ── Signals ── */
    .signal-list {
      font-size: 12px;
      font-family: monospace;
      color: var(--text2);
      line-height: 1.8;
    }

    .signal-list span {
      color: var(--accent);
    }

    /* ── Metrics bar ── */
    .metrics-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }

    .metric { text-align: center; }

    .metric .mv {
      font-size: 18px;
      font-weight: 700;
      color: var(--accent);
    }

    .metric .ml {
      font-size: 10px;
      color: var(--text2);
      text-transform: uppercase;
    }

    /* ── Inline forms ── */
    .assign-form,
    .status-form {
      display: flex;
      gap: 6px;
      align-items: center;
      margin-top: 8px;
    }

    .assign-form input {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 5px 8px;
      border-radius: 4px;
      font-size: 12px;
      width: 140px;
    }
  </style>
</head>
<body>

<!-- ═══════════════════════════ Header ═══════════════════════════ -->
<div class="header">
  <h1>Incident Management Dashboard</h1>
  <div class="status">
    <div class="dot"></div>
    <span id="hdr-status">Connecting...</span>
  </div>
</div>

<!-- ═══════════════════════════ Metrics bar ═══════════════════════════ -->
<div class="metrics-bar" id="metrics-bar">
  <div class="metric"><div class="mv" id="m-signals">0</div><div class="ml">Signals</div></div>
  <div class="metric"><div class="mv" id="m-created">0</div><div class="ml">Created</div></div>
  <div class="metric"><div class="mv" id="m-updated">0</div><div class="ml">Updated</div></div>
  <div class="metric"><div class="mv" id="m-active">0</div><div class="ml">Active</div></div>
  <div class="metric"><div class="mv" id="m-rate">0</div><div class="ml">Sig/s</div></div>
</div>

<!-- ═══════════════════════════ Main layout ═══════════════════════════ -->
<div class="container">

  <!-- Sidebar -->
  <div class="sidebar">
    <div class="filters">
      <select id="f-status">
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="investigating">Investigating</option>
        <option value="mitigated">Mitigated</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>
      <select id="f-severity">
        <option value="">All Severity</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
      <input id="f-service" placeholder="Service..." style="width:100px">
    </div>
    <div class="incident-list" id="incident-list"></div>
  </div>

  <!-- Main panel -->
  <div class="main" id="main-panel">
    <div class="empty-state" id="empty-state">Select an incident to view details</div>
    <div class="detail" id="detail-panel" style="display:none"></div>
  </div>

</div>

<script>
  /* ─────────────────────────── State ─────────────────────────── */
  const API = '';           // Base URL; empty = same origin
  let incidents  = [];
  let selected   = null;    // Currently selected incident ID

  /* ─────────────────────────── Helpers ─────────────────────────── */

  /**
   * Fetch JSON from the API.
   * @param {string} url - Path relative to API base.
   * @param {RequestInit} [opts] - Optional fetch options.
   * @returns {Promise<any>}
   */
  async function fetchJSON(url, opts) {
    const response = await fetch(API + url, opts);
    if (!response.ok) throw new Error(response.statusText);
    return response.json();
  }

  /**
   * Escape a string for safe HTML insertion.
   * @param {string} s
   * @returns {string}
   */
  function esc(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  /**
   * Return the CSS modifier class for a timeline dot based on event type.
   * @param {string} eventType
   * @returns {string}
   */
  function tlDotClass(eventType) {
    if (eventType.includes('created'))  return 'created';
    if (eventType.includes('status'))   return 'status';
    if (eventType.includes('signal'))   return 'signal';
    if (eventType.includes('note'))     return 'note';
    if (eventType.includes('response')) return 'response';
    return '';
  }

  /* ─────────────────────────── Polling ─────────────────────────── */

  /**
   * Poll the server for the latest incidents and metrics, then refresh the UI.
   */
  async function poll() {
    try {
      // Build query string from active filters
      const params = new URLSearchParams();
      const statusVal   = document.getElementById('f-status').value;
      const severityVal = document.getElementById('f-severity').value;
      const serviceVal  = document.getElementById('f-service').value.trim();

      if (statusVal)   params.set('status',           statusVal);
      if (severityVal) params.set('severity',          severityVal);
      if (serviceVal)  params.set('affected_service',  serviceVal);

      // Fetch incidents
      const data = await fetchJSON('/incidents?' + params);
      incidents = data.incidents || [];

      // Sort newest first
      incidents.sort((a, b) =>
        (b.created_at || '').localeCompare(a.created_at || '')
      );

      renderList();

      // Refresh detail panel if an incident is already selected
      if (selected) await loadDetail(selected);

      // Fetch and render metrics
      const metrics = await fetchJSON('/metrics');
      document.getElementById('m-signals').textContent = metrics.signals_received  || 0;
      document.getElementById('m-created').textContent = metrics.incidents_created || 0;
      document.getElementById('m-updated').textContent = metrics.incidents_updated || 0;
      document.getElementById('m-active').textContent  = incidents.filter(
        i => ['open', 'investigating', 'mitigated'].includes(i.status)
      ).length;
      document.getElementById('m-rate').textContent = metrics.signals_per_second || 0;

      document.getElementById('hdr-status').textContent =
        'Live — ' + incidents.length + ' incidents';

    } catch (err) {
      document.getElementById('hdr-status').textContent = 'Error: ' + err.message;
    }
  }

  /* ─────────────────────────── Sidebar list ─────────────────────────── */

  /** Render the incident list in the sidebar. */
  function renderList() {
    const el = document.getElementById('incident-list');
    el.innerHTML = incidents.map(i => `
      <div class="incident-item ${selected === i.incident_id ? 'active' : ''}"
           onclick="selectIncident('${i.incident_id}')">
        <div class="top">
          <span class="id">${i.incident_id}</span>
          <span class="sev sev-${i.severity}">${i.severity}</span>
        </div>
        <div class="desc">${esc(i.description || '—')}</div>
        <div class="meta">
          <span class="stat-badge stat-${i.status}">${i.status}</span>
          <span>${i.signal_count || 0} signals</span>
          <span>${i.affected_service || '—'}</span>
        </div>
      </div>
    `).join('');
  }

  /**
   * Select an incident by ID, highlight it in the list, and load its detail.
   * @param {string} id
   */
  function selectIncident(id) {
    selected = id;
    renderList();
    loadDetail(id);
  }

  /* ─────────────────────────── Detail panel ─────────────────────────── */

  /**
   * Fetch full details for an incident and render the detail panel.
   * @param {string} id
   */
  async function loadDetail(id) {
    const dp = document.getElementById('detail-panel');
    const es = document.getElementById('empty-state');

    try {
      const data    = await fetchJSON('/incidents/' + id);
      const inc     = data.incident;
      const timeline = data.timeline || [];
      const notes   = data.notes    || [];

      es.style.display  = 'none';
      dp.style.display  = 'block';

      dp.innerHTML = `
        <div class="detail-header">
          <div>
            <h2>${esc(inc.incident_id)}</h2>
            <span style="color:var(--text2);font-size:13px">${esc(inc.description || '')}</span>
          </div>
          <div class="actions">
            <span class="sev sev-${inc.severity}" style="padding:4px 10px;font-size:12px">
              ${inc.severity.toUpperCase()}
            </span>
            <span class="stat-badge stat-${inc.status}" style="padding:4px 10px;font-size:12px">
              ${inc.status.toUpperCase()}
            </span>
          </div>
        </div>

        <!-- Info cards -->
        <div class="info-grid">
          <div class="info-card"><div class="label">Service</div>    <div class="value">${esc(inc.affected_service || '—')}</div></div>
          <div class="info-card"><div class="label">Environment</div><div class="value">${esc(inc.environment    || '—')}</div></div>
          <div class="info-card"><div class="label">Region</div>     <div class="value">${esc(inc.region         || '—')}</div></div>
          <div class="info-card"><div class="label">Risk Score</div> <div class="value">${(inc.risk_score || 0).toFixed(2)}</div></div>
          <div class="info-card"><div class="label">Signals</div>    <div class="value">${inc.signal_count || 0}</div></div>
          <div class="info-card"><div class="label">Analyst</div>    <div class="value">${esc(inc.assigned_analyst || 'Unassigned')}</div></div>
          <div class="info-card"><div class="label">Created</div>    <div class="value" style="font-size:12px">${esc(inc.created_at    || '—')}</div></div>
          <div class="info-card"><div class="label">Last Signal</div><div class="value" style="font-size:12px">${esc(inc.last_signal_at || '—')}</div></div>
        </div>

        <!-- Action row -->
        <div style="display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap">

          <!-- Status update -->
          <div>
            <label style="font-size:12px;color:var(--text2)">Update Status:</label>
            <div class="status-form">
              <select id="status-sel"
                      style="background:var(--surface2);border:1px solid var(--border);
                             color:var(--text);padding:5px 8px;border-radius:4px;font-size:12px">
                <option value="open">open</option>
                <option value="investigating">investigating</option>
                <option value="mitigated">mitigated</option>
                <option value="resolved">resolved</option>
                <option value="closed">closed</option>
              </select>
              <button class="btn btn-primary" onclick="updateStatus('${inc.incident_id}')">Update</button>
            </div>
          </div>

          <!-- Analyst assignment -->
          <div>
            <label style="font-size:12px;color:var(--text2)">Assign Analyst:</label>
            <div class="assign-form">
              <input id="assign-input"
                     placeholder="analyst name"
                     value="${esc(inc.assigned_analyst || '')}">
              <button class="btn btn-primary" onclick="assignAnalyst('${inc.incident_id}')">Assign</button>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          <div class="tab active"  onclick="switchTab(this,'tab-timeline')">Timeline</div>
          <div class="tab"         onclick="switchTab(this,'tab-notes')">Notes</div>
          <div class="tab"         onclick="switchTab(this,'tab-signals')">Signals</div>
        </div>

        <!-- Timeline tab -->
        <div class="tab-content active" id="tab-timeline">
          ${
            timeline.length
              ? timeline.map(t => `
                  <div class="timeline-item">
                    <div class="tl-dot ${tlDotClass(t.event_type)}"></div>
                    <div>
                      <div class="tl-desc">${esc(t.description)}</div>
                      <div class="tl-time">${esc(t.timestamp)} —
                        <span class="tl-actor">${esc(t.actor)}</span>
                      </div>
                    </div>
                  </div>
                `).join('')
              : '<div style="color:var(--text2);font-size:13px">No timeline entries</div>'
          }
        </div>

        <!-- Notes tab -->
        <div class="tab-content" id="tab-notes">
          <div class="note-form">
            <input    id="note-analyst"  placeholder="Your name" style="width:120px">
            <textarea id="note-content"  placeholder="Investigation note..."></textarea>
            <button class="btn btn-primary" onclick="addNote('${inc.incident_id}')">Add</button>
          </div>
          ${
            notes.length
              ? notes.map(n => `
                  <div class="note-item">
                    <div class="note-meta">${esc(n.analyst)} — ${esc(n.created_at)}</div>
                    <div class="note-body">${esc(n.content)}</div>
                  </div>
                `).join('')
              : '<div style="color:var(--text2);font-size:13px">No notes yet</div>'
          }
        </div>

        <!-- Signals tab -->
        <div class="tab-content" id="tab-signals">
          <div class="signal-list">
            ${
              (inc.signal_ids || []).length
                ? (inc.signal_ids).map(s => `<div><span>${esc(s)}</span></div>`).join('')
                : 'No signals'
            }
          </div>
        </div>
      `;

      // Set the status dropdown to the incident's current status
      document.getElementById('status-sel').value = inc.status;

    } catch (err) {
      dp.innerHTML =
        '<div style="color:var(--red);padding:20px">Error loading incident: ' +
        esc(err.message) + '</div>';
      dp.style.display = 'block';
      es.style.display = 'none';
    }
  }

  /* ─────────────────────────── Tab switching ─────────────────────────── */

  /**
   * Switch active tab.
   * @param {HTMLElement} el  - The clicked tab element.
   * @param {string}      id  - ID of the corresponding tab-content div.
   */
  function switchTab(el, id) {
    // Deactivate all sibling tabs
    el.parentElement.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');

    // Deactivate all tab content panels
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // Activate the target panel
    const target = document.getElementById(id);
    if (target) target.classList.add('active');
  }

  /* ─────────────────────────── Actions ─────────────────────────── */

  /**
   * PATCH the status of an incident.
   * @param {string} id
   */
  async function updateStatus(id) {
    const statusSel = document.getElementById('status-sel');
    if (!statusSel) return;
    const status = statusSel.value;

    try {
      await fetchJSON('/incidents/' + id + '/status', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, actor: 'analyst' }),
      });
      await loadDetail(id);
      await poll();
    } catch (err) {
      console.error('updateStatus failed:', err);
    }
  }

  /**
   * Assign an analyst to an incident.
   * @param {string} id
   */
  async function assignAnalyst(id) {
    const input = document.getElementById('assign-input');
    if (!input) return;
    const analyst = input.value.trim();
    if (!analyst) return;

    try {
      await fetchJSON('/incidents/' + id + '/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analyst }),
      });
      await loadDetail(id);
      await poll();
    } catch (err) {
      console.error('assignAnalyst failed:', err);
    }
  }

  /**
   * Add a note to an incident.
   * @param {string} id
   */
  async function addNote(id) {
    const analystInput  = document.getElementById('note-analyst');
    const contentInput  = document.getElementById('note-content');
    if (!analystInput || !contentInput) return;

    const analyst = analystInput.value.trim();
    const content = contentInput.value.trim();
    if (!analyst || !content) return;

    try {
      await fetchJSON('/incidents/' + id + '/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analyst, content }),
      });
      contentInput.value = '';   // Clear only the note body; keep analyst name
      await loadDetail(id);
    } catch (err) {
      console.error('addNote failed:', err);
    }
  }

  /* ─────────────────────────── Filter listeners ─────────────────────────── */

  document.getElementById('f-status').addEventListener('change', poll);
  document.getElementById('f-severity').addEventListener('change', poll);

  let serviceDebounceTimer;
  document.getElementById('f-service').addEventListener('input', () => {
    clearTimeout(serviceDebounceTimer);
    serviceDebounceTimer = setTimeout(poll, 400);
  });

  /* ─────────────────────────── Bootstrap ─────────────────────────── */
  poll();
  setInterval(poll, 3000);
</script>
</body>
</html>
"""
