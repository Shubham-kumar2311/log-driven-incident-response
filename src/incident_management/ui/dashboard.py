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
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #1c2333;
      --surface3: #21293a;
      --border: #30363d;
      --border-light: #3d444d;
      --text: #e6edf3;
      --text2: #8b949e;
      --text3: #6e7681;
      --accent: #58a6ff;
      --accent-dim: rgba(88, 166, 255, 0.15);
      --green: #3fb950;
      --green-dim: rgba(63, 185, 80, 0.15);
      --yellow: #d29922;
      --yellow-dim: rgba(210, 153, 34, 0.15);
      --red: #f85149;
      --red-dim: rgba(248, 81, 73, 0.15);
      --orange: #db6d28;
      --orange-dim: rgba(219, 109, 40, 0.15);
      --purple: #bc8cff;
      --purple-dim: rgba(188, 140, 255, 0.15);
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

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-light); }

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

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .header-logo {
      width: 28px;
      height: 28px;
      background: linear-gradient(135deg, var(--accent), var(--purple));
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
      color: white;
    }

    .header h1 {
      font-size: 15px;
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
      animation: pulse-dot 2s ease-in-out infinite;
    }

    @keyframes pulse-dot {
      0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.4); }
      50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(63, 185, 80, 0); }
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
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 12px;
      transition: border-color 0.2s;
    }

    .filters select:focus,
    .filters input:focus {
      border-color: var(--accent);
      outline: none;
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
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      transition: all 0.2s ease;
      border-left: 3px solid transparent;
    }

    .incident-item:hover {
      background: var(--surface2);
    }

    .incident-item.active {
      background: var(--surface2);
      border-left-color: var(--accent);
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
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }

    /* ── Severity colours ── */
    .sev-critical  { background: var(--red-dim);    color: var(--red);    }
    .sev-high      { background: var(--orange-dim);  color: var(--orange); }
    .sev-medium    { background: var(--yellow-dim);  color: var(--yellow); }
    .sev-low       { background: var(--green-dim);   color: var(--green);  }
    .sev-info      { background: var(--accent-dim);  color: var(--accent); }

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
      margin-top: 6px;
      display: flex;
      gap: 10px;
      align-items: center;
    }

    /* ── Status badges ── */
    .stat-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 500;
      transition: all 0.3s ease;
    }

    .stat-open          { background: var(--green-dim);  color: var(--green);  }
    .stat-investigating { background: var(--accent-dim); color: var(--accent); }
    .stat-mitigated     { background: var(--yellow-dim); color: var(--yellow); }
    .stat-resolved      { background: var(--purple-dim); color: var(--purple); }
    .stat-closed        { background: rgba(139,148,158,0.15); color: var(--text2); }

    /* ── Main panel ── */
    .main {
      flex: 1;
      overflow-y: auto;
      padding: 0;
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text2);
      font-size: 14px;
      gap: 12px;
    }

    .empty-state-icon {
      font-size: 48px;
      opacity: 0.3;
    }

    /* ── Detail view ── */
    .detail {
      padding: 24px 28px;
      animation: fadeIn 0.25s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .detail-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
    }

    .detail-header h2 {
      font-size: 18px;
      font-weight: 600;
      font-family: monospace;
      color: var(--accent);
    }

    .detail-header .subtitle {
      color: var(--text2);
      font-size: 13px;
      margin-top: 4px;
    }

    .detail-header .badges {
      display: flex;
      gap: 8px;
    }

    .detail-badge {
      padding: 5px 12px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      transition: all 0.3s ease;
    }

    /* ── Buttons ── */
    .btn {
      padding: 7px 16px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--surface2);
      color: var(--text);
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-weight: 500;
    }

    .btn:hover {
      background: var(--surface3);
      border-color: var(--border-light);
    }

    .btn:active {
      transform: scale(0.97);
    }

    .btn-primary {
      background: rgba(88, 166, 255, 0.15);
      border-color: rgba(88, 166, 255, 0.4);
      color: var(--accent);
    }

    .btn-primary:hover {
      background: rgba(88, 166, 255, 0.25);
      border-color: var(--accent);
    }

    .btn-success {
      background: rgba(63, 185, 80, 0.15);
      border-color: rgba(63, 185, 80, 0.4);
      color: var(--green);
    }

    .btn-success:hover {
      background: rgba(63, 185, 80, 0.25);
      border-color: var(--green);
    }

    .btn-danger {
      background: var(--red-dim);
      border-color: rgba(248, 81, 73, 0.4);
      color: var(--red);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* ── Info grid ── */
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
      margin-bottom: 24px;
    }

    .info-card {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      transition: all 0.3s ease;
    }

    .info-card .label {
      font-size: 11px;
      color: var(--text3);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }

    .info-card .value {
      font-size: 14px;
      font-weight: 600;
    }

    /* ── Action row ── */
    .action-row {
      display: flex;
      gap: 20px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }

    .action-group {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 18px;
      flex: 1;
      min-width: 240px;
    }

    .action-group label {
      display: block;
      font-size: 11px;
      color: var(--text3);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      font-weight: 600;
    }

    .action-group .form-row {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .action-group select,
    .action-group input {
      background: var(--surface3);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 7px 10px;
      border-radius: 6px;
      font-size: 12px;
      transition: border-color 0.2s;
    }

    .action-group select:focus,
    .action-group input:focus {
      border-color: var(--accent);
      outline: none;
    }

    /* ── Tabs ── */
    .tabs {
      display: flex;
      border-bottom: 2px solid var(--border);
      margin-bottom: 16px;
      gap: 4px;
    }

    .tab {
      padding: 10px 18px;
      font-size: 13px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      color: var(--text2);
      transition: all 0.2s ease;
      margin-bottom: -2px;
      border-radius: 6px 6px 0 0;
      font-weight: 500;
    }

    .tab:hover {
      color: var(--text);
      background: var(--surface2);
    }

    .tab.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
      background: transparent;
    }

    .tab-content {
      display: none;
    }

    .tab-content.active {
      display: block;
      animation: fadeIn 0.2s ease;
    }

    /* ── Timeline ── */
    .timeline-item {
      display: flex;
      gap: 14px;
      padding: 10px 0;
      border-bottom: 1px solid var(--border);
      transition: background 0.2s;
    }

    .timeline-item:last-child {
      border-bottom: none;
    }

    .timeline-item:hover {
      background: var(--surface2);
      border-radius: 6px;
      padding-left: 8px;
      margin-left: -8px;
    }

    .tl-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent);
      margin-top: 6px;
      flex-shrink: 0;
      transition: transform 0.2s;
    }

    .timeline-item:hover .tl-dot {
      transform: scale(1.3);
    }

    .tl-dot.created   { background: var(--green);  }
    .tl-dot.status    { background: var(--yellow); }
    .tl-dot.signal    { background: var(--purple); }
    .tl-dot.note      { background: var(--orange); }
    .tl-dot.response  { background: var(--red);    }
    .tl-dot.assigned  { background: var(--accent); }
    .tl-dot.severity  { background: var(--red);    }

    .timeline-item .tl-time  { font-size: 11px; color: var(--text3); }
    .timeline-item .tl-desc  { font-size: 13px; }
    .timeline-item .tl-actor { font-size: 11px; color: var(--text2); font-style: italic; }

    /* ── Notes ── */
    .note-form {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      align-items: flex-end;
    }

    .note-form input,
    .note-form textarea {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-family: inherit;
      transition: border-color 0.2s;
    }

    .note-form input:focus,
    .note-form textarea:focus {
      border-color: var(--accent);
      outline: none;
    }

    .note-form textarea {
      flex: 1;
      resize: vertical;
      min-height: 40px;
    }

    .note-item {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 8px;
      transition: border-color 0.2s;
    }

    .note-item:hover {
      border-color: var(--border-light);
    }

    .note-item .note-meta { font-size: 11px; color: var(--text3); margin-bottom: 6px; }
    .note-item .note-body { font-size: 13px; line-height: 1.6; }

    /* ── Signals ── */
    .signal-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .signal-item {
      font-size: 12px;
      font-family: monospace;
      padding: 8px 12px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--accent);
      transition: border-color 0.2s;
    }

    .signal-item:hover {
      border-color: var(--accent);
    }

    /* ── Metrics bar ── */
    .metrics-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 8px;
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }

    .metric {
      text-align: center;
      padding: 4px 0;
    }

    .metric .mv {
      font-size: 20px;
      font-weight: 700;
      color: var(--accent);
      transition: all 0.3s ease;
    }

    .metric .ml {
      font-size: 10px;
      color: var(--text3);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* ── Toast notifications ── */
    .toast-container {
      position: fixed;
      top: 60px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .toast {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 20px 12px 16px;
      font-size: 13px;
      color: var(--text);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
      opacity: 0;
      transform: translateX(120%);
      transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
      max-width: 380px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .toast.show {
      opacity: 1;
      transform: translateX(0);
    }

    .toast-icon {
      font-size: 16px;
      flex-shrink: 0;
    }

    .toast-success {
      border-left: 4px solid var(--green);
      background: linear-gradient(135deg, rgba(63, 185, 80, 0.1), var(--surface2));
    }

    .toast-error {
      border-left: 4px solid var(--red);
      background: linear-gradient(135deg, rgba(248, 81, 73, 0.1), var(--surface2));
    }

    .toast-info {
      border-left: 4px solid var(--accent);
      background: linear-gradient(135deg, rgba(88, 166, 255, 0.1), var(--surface2));
    }

    /* ── Flash animation for updates ── */
    @keyframes flashSuccess {
      0% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.5); }
      50% { box-shadow: 0 0 12px 4px rgba(63, 185, 80, 0.3); }
      100% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0); }
    }

    @keyframes flashAccent {
      0% { box-shadow: 0 0 0 0 rgba(88, 166, 255, 0.5); }
      50% { box-shadow: 0 0 12px 4px rgba(88, 166, 255, 0.3); }
      100% { box-shadow: 0 0 0 0 rgba(88, 166, 255, 0); }
    }

    .flash-success {
      animation: flashSuccess 0.8s ease;
    }

    .flash-accent {
      animation: flashAccent 0.8s ease;
    }

    /* ── Spinner for loading ── */
    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* ── Sidebar updated indicator ── */
    @keyframes sidebarFlash {
      0% { background: rgba(63, 185, 80, 0.15); }
      100% { background: transparent; }
    }

    .sidebar-updated {
      animation: sidebarFlash 1.5s ease;
    }

    /* ── Empty list ── */
    .no-items {
      color: var(--text3);
      font-size: 13px;
      padding: 16px;
      text-align: center;
    }
  </style>
</head>
<body>

<!-- Toast container -->
<div class="toast-container" id="toast-container"></div>

<!-- ═══════════════════════════ Header ═══════════════════════════ -->
<div class="header">
  <div class="header-left">
    <div class="header-logo">IM</div>
    <h1>Incident Management</h1>
  </div>
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
    <div class="empty-state" id="empty-state">
      <div class="empty-state-icon">&#9432;</div>
      <div>Select an incident to view details</div>
    </div>
    <div class="detail" id="detail-panel" style="display:none"></div>
  </div>

</div>

<script>
  /* ─────────────────────────── State ─────────────────────────── */
  const API = '';
  let incidents  = [];
  let selected   = null;
  let actionInProgress = false;   // lock to prevent poll from rebuilding detail during actions

  /* ─────────────────────────── Toast system ─────────────────────────── */

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const icons = { success: '\u2713', error: '\u2717', info: '\u2139' };
    toast.className = 'toast toast-' + type;
    toast.innerHTML = '<span class="toast-icon">' + (icons[type] || icons.info) +
                      '</span><span>' + esc(message) + '</span>';
    container.appendChild(toast);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => toast.classList.add('show'));
    });
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 350);
    }, 3500);
  }

  /* ─────────────────────────── Helpers ─────────────────────────── */

  async function fetchJSON(url, opts) {
    const response = await fetch(API + url, opts);
    if (!response.ok) {
      let errMsg = response.statusText;
      try {
        const body = await response.json();
        if (body.detail) errMsg = body.detail;
      } catch (_) {}
      throw new Error(errMsg);
    }
    return response.json();
  }

  function esc(s) {
    if (s === null || s === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(s);
    return div.innerHTML;
  }

  function tlDotClass(eventType) {
    if (eventType.includes('created'))  return 'created';
    if (eventType.includes('status'))   return 'status';
    if (eventType.includes('signal'))   return 'signal';
    if (eventType.includes('note'))     return 'note';
    if (eventType.includes('response')) return 'response';
    if (eventType.includes('assign'))   return 'assigned';
    if (eventType.includes('severity')) return 'severity';
    return '';
  }

  function flashElement(el, cls) {
    if (!el) return;
    el.classList.remove(cls);
    void el.offsetWidth;   // force reflow
    el.classList.add(cls);
    setTimeout(() => el.classList.remove(cls), 1000);
  }

  /* ─────────────────────────── Polling ─────────────────────────── */

  async function poll() {
    try {
      const params = new URLSearchParams();
      const statusVal   = document.getElementById('f-status').value;
      const severityVal = document.getElementById('f-severity').value;
      const serviceVal  = document.getElementById('f-service').value.trim();

      if (statusVal)   params.set('status',           statusVal);
      if (severityVal) params.set('severity',          severityVal);
      if (serviceVal)  params.set('affected_service',  serviceVal);

      const data = await fetchJSON('/incidents?' + params);
      incidents = data.incidents || [];

      incidents.sort((a, b) =>
        (b.created_at || '').localeCompare(a.created_at || '')
      );

      renderList();

      // Only auto-refresh detail panel if NO action is in progress
      // This prevents destroying user's form input (dropdown, text fields)
      if (selected && !actionInProgress) {
        await refreshDetail(selected);
      }

      // Metrics
      const metrics = await fetchJSON('/metrics');
      updateMetric('m-signals', metrics.signals_received  || 0);
      updateMetric('m-created', metrics.incidents_created || 0);
      updateMetric('m-updated', metrics.incidents_updated || 0);
      updateMetric('m-active', incidents.filter(
        i => ['open', 'investigating', 'mitigated'].includes(i.status)
      ).length);
      updateMetric('m-rate', metrics.signals_per_second || 0);

      document.getElementById('hdr-status').textContent =
        'Live \u2014 ' + incidents.length + ' incident' + (incidents.length !== 1 ? 's' : '');

    } catch (err) {
      document.getElementById('hdr-status').textContent = 'Error: ' + err.message;
    }
  }

  function updateMetric(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    const old = el.textContent;
    el.textContent = value;
    if (old !== String(value)) {
      flashElement(el, 'flash-accent');
    }
  }

  /* ─────────────────────────── Sidebar list ─────────────────────────── */

  function renderList() {
    const el = document.getElementById('incident-list');
    if (!incidents.length) {
      el.innerHTML = '<div class="no-items">No incidents found</div>';
      return;
    }
    el.innerHTML = incidents.map(i => `
      <div class="incident-item ${selected === i.incident_id ? 'active' : ''}"
           onclick="selectIncident('${i.incident_id}')">
        <div class="top">
          <span class="id">${esc(i.incident_id)}</span>
          <span class="sev sev-${i.severity}">${esc(i.severity)}</span>
        </div>
        <div class="desc">${esc(i.description || '\u2014')}</div>
        <div class="meta">
          <span class="stat-badge stat-${i.status}">${esc(i.status)}</span>
          <span>${i.signal_count || 0} signals</span>
          <span>${esc(i.affected_service || '\u2014')}</span>
        </div>
      </div>
    `).join('');
  }

  function selectIncident(id) {
    selected = id;
    renderList();
    loadDetail(id);
  }

  /* ─────────────────────────── Detail panel ─────────────────────────── */

  // Full render of detail panel (used on initial select and after actions)
  async function loadDetail(id) {
    const dp = document.getElementById('detail-panel');
    const es = document.getElementById('empty-state');

    try {
      const data     = await fetchJSON('/incidents/' + id);
      const inc      = data.incident;
      const timeline = data.timeline || [];
      const notes    = data.notes    || [];

      es.style.display  = 'none';
      dp.style.display  = 'block';

      dp.innerHTML = buildDetailHTML(inc, timeline, notes);

      // Set the status dropdown to current status
      const sel = document.getElementById('status-sel');
      if (sel) sel.value = inc.status;

    } catch (err) {
      dp.innerHTML =
        '<div style="color:var(--red);padding:20px">Error loading incident: ' +
        esc(err.message) + '</div>';
      dp.style.display = 'block';
      es.style.display = 'none';
    }
  }

  // Smart refresh: updates read-only parts WITHOUT destroying form state
  async function refreshDetail(id) {
    const dp = document.getElementById('detail-panel');
    if (!dp || dp.style.display === 'none') return;

    try {
      const data     = await fetchJSON('/incidents/' + id);
      const inc      = data.incident;
      const timeline = data.timeline || [];
      const notes    = data.notes    || [];

      // Update info cards without touching action forms
      updateInfoCards(inc);

      // Update header badges
      const statusBadge = document.getElementById('detail-status-badge');
      if (statusBadge) {
        statusBadge.className = 'detail-badge stat-' + inc.status;
        statusBadge.textContent = (inc.status || '').toUpperCase();
      }

      const sevBadge = document.getElementById('detail-sev-badge');
      if (sevBadge) {
        sevBadge.className = 'detail-badge sev-' + inc.severity;
        sevBadge.textContent = (inc.severity || '').toUpperCase();
      }

      // Update timeline if tab is active
      const tlTab = document.getElementById('tab-timeline');
      if (tlTab && tlTab.classList.contains('active')) {
        tlTab.innerHTML = buildTimelineHTML(timeline);
      }

      // Update signals
      const sigTab = document.getElementById('tab-signals');
      if (sigTab && sigTab.classList.contains('active')) {
        sigTab.innerHTML = buildSignalsHTML(inc.signal_ids || []);
      }

    } catch (_) {
      // silent - detail refresh is best-effort
    }
  }

  function updateInfoCards(inc) {
    const updates = {
      'ic-service':     inc.affected_service || '\u2014',
      'ic-environment': inc.environment      || '\u2014',
      'ic-region':      inc.region           || '\u2014',
      'ic-risk':        (inc.risk_score || 0).toFixed(2),
      'ic-signals':     inc.signal_count     || 0,
      'ic-analyst':     inc.assigned_analyst || 'Unassigned',
      'ic-created':     inc.created_at       || '\u2014',
      'ic-lastsignal':  inc.last_signal_at   || '\u2014',
    };
    for (const [id, val] of Object.entries(updates)) {
      const el = document.getElementById(id);
      if (el && el.textContent !== String(val)) {
        el.textContent = val;
        flashElement(el.closest('.info-card'), 'flash-accent');
      }
    }
  }

  /* ─────────────────────────── HTML builders ─────────────────────────── */

  function buildDetailHTML(inc, timeline, notes) {
    return `
      <div class="detail-header">
        <div>
          <h2>${esc(inc.incident_id)}</h2>
          <div class="subtitle">${esc(inc.description || '')}</div>
        </div>
        <div class="badges">
          <span id="detail-sev-badge" class="detail-badge sev-${inc.severity}">
            ${(inc.severity || '').toUpperCase()}
          </span>
          <span id="detail-status-badge" class="detail-badge stat-${inc.status}">
            ${(inc.status || '').toUpperCase()}
          </span>
        </div>
      </div>

      <!-- Info cards -->
      <div class="info-grid">
        <div class="info-card"><div class="label">Service</div>     <div class="value" id="ic-service">${esc(inc.affected_service || '\u2014')}</div></div>
        <div class="info-card"><div class="label">Environment</div> <div class="value" id="ic-environment">${esc(inc.environment    || '\u2014')}</div></div>
        <div class="info-card"><div class="label">Region</div>      <div class="value" id="ic-region">${esc(inc.region         || '\u2014')}</div></div>
        <div class="info-card"><div class="label">Risk Score</div>  <div class="value" id="ic-risk">${(inc.risk_score || 0).toFixed(2)}</div></div>
        <div class="info-card"><div class="label">Signals</div>     <div class="value" id="ic-signals">${inc.signal_count || 0}</div></div>
        <div class="info-card"><div class="label">Analyst</div>     <div class="value" id="ic-analyst">${esc(inc.assigned_analyst || 'Unassigned')}</div></div>
        <div class="info-card"><div class="label">Created</div>     <div class="value" id="ic-created" style="font-size:12px">${esc(inc.created_at    || '\u2014')}</div></div>
        <div class="info-card"><div class="label">Last Signal</div> <div class="value" id="ic-lastsignal" style="font-size:12px">${esc(inc.last_signal_at || '\u2014')}</div></div>
      </div>

      <!-- Action row -->
      <div class="action-row">
        <div class="action-group">
          <label>Update Status</label>
          <div class="form-row">
            <select id="status-sel">
              <option value="open">Open</option>
              <option value="investigating">Investigating</option>
              <option value="mitigated">Mitigated</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
            <button class="btn btn-primary" id="btn-status" onclick="updateStatus('${inc.incident_id}')">
              Update
            </button>
          </div>
        </div>

        <div class="action-group">
          <label>Assign Analyst</label>
          <div class="form-row">
            <input id="assign-input"
                   placeholder="Enter analyst name..."
                   value="${esc(inc.assigned_analyst || '')}"
                   style="flex:1">
            <button class="btn btn-success" id="btn-assign" onclick="assignAnalyst('${inc.incident_id}')">
              Assign
            </button>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <div class="tab active"  onclick="switchTab(this,'tab-timeline')">Timeline (${timeline.length})</div>
        <div class="tab"         onclick="switchTab(this,'tab-notes')">Notes (${notes.length})</div>
        <div class="tab"         onclick="switchTab(this,'tab-signals')">Signals (${(inc.signal_ids || []).length})</div>
      </div>

      <!-- Timeline tab -->
      <div class="tab-content active" id="tab-timeline">
        ${buildTimelineHTML(timeline)}
      </div>

      <!-- Notes tab -->
      <div class="tab-content" id="tab-notes">
        <div class="note-form">
          <input    id="note-analyst"  placeholder="Your name" style="width:130px">
          <textarea id="note-content"  placeholder="Investigation note..."></textarea>
          <button class="btn btn-primary" onclick="addNote('${inc.incident_id}')">Add</button>
        </div>
        ${buildNotesHTML(notes)}
      </div>

      <!-- Signals tab -->
      <div class="tab-content" id="tab-signals">
        ${buildSignalsHTML(inc.signal_ids || [])}
      </div>
    `;
  }

  function buildTimelineHTML(timeline) {
    if (!timeline.length) return '<div class="no-items">No timeline entries</div>';
    return timeline.slice().reverse().map(t => `
      <div class="timeline-item">
        <div class="tl-dot ${tlDotClass(t.event_type)}"></div>
        <div style="flex:1">
          <div class="tl-desc">${esc(t.description)}</div>
          <div class="tl-time">
            ${esc(t.timestamp)}
            <span class="tl-actor"> \u2014 ${esc(t.actor)}</span>
          </div>
        </div>
      </div>
    `).join('');
  }

  function buildNotesHTML(notes) {
    if (!notes.length) return '<div class="no-items">No notes yet</div>';
    return notes.slice().reverse().map(n => `
      <div class="note-item">
        <div class="note-meta">${esc(n.analyst)} \u2014 ${esc(n.created_at)}</div>
        <div class="note-body">${esc(n.content)}</div>
      </div>
    `).join('');
  }

  function buildSignalsHTML(signalIds) {
    if (!signalIds.length) return '<div class="no-items">No signals</div>';
    return '<div class="signal-list">' +
      signalIds.map(s => '<div class="signal-item">' + esc(s) + '</div>').join('') +
      '</div>';
  }

  /* ─────────────────────────── Tab switching ─────────────────────────── */

  function switchTab(el, id) {
    el.parentElement.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const target = document.getElementById(id);
    if (target) target.classList.add('active');
  }

  /* ─────────────────────────── Actions ─────────────────────────── */

  async function updateStatus(id) {
    const sel = document.getElementById('status-sel');
    const btn = document.getElementById('btn-status');
    if (!sel) return;

    const status = sel.value;

    actionInProgress = true;
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Updating...'; }

    try {
      await fetchJSON('/incidents/' + id + '/status', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status, actor: 'analyst' }),
      });
      showToast('Status updated to ' + status, 'success');
      await loadDetail(id);
      await poll();

      // Flash the status badge
      flashElement(document.getElementById('detail-status-badge'), 'flash-success');

    } catch (err) {
      console.error('updateStatus failed:', err);
      showToast('Failed to update status: ' + err.message, 'error');
    } finally {
      actionInProgress = false;
      if (btn) { btn.disabled = false; btn.textContent = 'Update'; }
    }
  }

  async function assignAnalyst(id) {
    const input = document.getElementById('assign-input');
    const btn   = document.getElementById('btn-assign');
    if (!input) return;

    const analyst = input.value.trim();
    if (!analyst) {
      showToast('Please enter an analyst name', 'error');
      input.focus();
      return;
    }

    actionInProgress = true;
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Assigning...'; }

    try {
      await fetchJSON('/incidents/' + id + '/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analyst: analyst }),
      });
      showToast('Assigned to ' + analyst, 'success');
      await loadDetail(id);
      await poll();

      // Flash the analyst card
      const analystCard = document.getElementById('ic-analyst');
      if (analystCard) flashElement(analystCard.closest('.info-card'), 'flash-success');

    } catch (err) {
      console.error('assignAnalyst failed:', err);
      showToast('Failed to assign: ' + err.message, 'error');
    } finally {
      actionInProgress = false;
      if (btn) { btn.disabled = false; btn.textContent = 'Assign'; }
    }
  }

  async function addNote(id) {
    const analystInput  = document.getElementById('note-analyst');
    const contentInput  = document.getElementById('note-content');
    if (!analystInput || !contentInput) return;

    const analyst = analystInput.value.trim();
    const content = contentInput.value.trim();

    if (!analyst || !content) {
      showToast('Please enter both your name and note content', 'error');
      if (!analyst) analystInput.focus();
      else contentInput.focus();
      return;
    }

    actionInProgress = true;

    try {
      await fetchJSON('/incidents/' + id + '/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analyst: analyst, content: content }),
      });
      showToast('Note added successfully', 'success');
      contentInput.value = '';
      await loadDetail(id);
    } catch (err) {
      console.error('addNote failed:', err);
      showToast('Failed to add note: ' + err.message, 'error');
    } finally {
      actionInProgress = false;
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
  setInterval(poll, 4000);
</script>
</body>
</html>
"""
