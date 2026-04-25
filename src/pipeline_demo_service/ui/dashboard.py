"""Dashboard UI for the pipeline demo microservice."""


def render_dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pipeline Demo Control Room</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg-cream: #f5efe7;
      --bg-sky: #dff3f4;
      --panel: #ffffff;
      --ink: #102a43;
      --muted: #486581;
      --brand: #0e7490;
      --brand-strong: #155e75;
      --accent: #ea580c;
      --good: #15803d;
      --bad: #b91c1c;
      --ring: rgba(14, 116, 144, 0.25);
      --shadow: 0 14px 40px rgba(16, 42, 67, 0.1);
      --radius-lg: 18px;
      --radius-md: 12px;
      --radius-sm: 8px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: "Source Sans 3", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 10%, rgba(14, 116, 144, 0.2), transparent 42%),
        radial-gradient(circle at 88% 12%, rgba(234, 88, 12, 0.17), transparent 36%),
        linear-gradient(180deg, var(--bg-cream), var(--bg-sky));
      min-height: 100vh;
      padding: 28px;
    }

    .page {
      max-width: 1220px;
      margin: 0 auto;
      display: grid;
      gap: 18px;
    }

    .hero {
      position: relative;
      overflow: hidden;
      border-radius: 24px;
      background: linear-gradient(120deg, #0e7490 0%, #155e75 54%, #1f2937 100%);
      color: #f8fafc;
      padding: 26px;
      box-shadow: var(--shadow);
      animation: rise-in 500ms ease;
    }

    .hero::after {
      content: "";
      position: absolute;
      top: -48px;
      right: -36px;
      width: 200px;
      height: 200px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.05));
      pointer-events: none;
    }

    .hero h1 {
      margin: 0 0 8px;
      font: 800 2rem/1.12 "Sora", sans-serif;
      letter-spacing: 0.01em;
    }

    .hero p {
      margin: 0;
      max-width: 760px;
      color: rgba(241, 245, 249, 0.92);
      font-size: 1.02rem;
    }

    .badge-row {
      margin-top: 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .badge {
      font-size: 0.8rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 5px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.35);
      background: rgba(2, 6, 23, 0.22);
    }

    .banner {
      border-radius: var(--radius-md);
      padding: 12px 14px;
      border: 1px solid #bae6fd;
      background: #f0f9ff;
      color: #0c4a6e;
      display: none;
      animation: rise-in 300ms ease;
    }

    .banner.visible {
      display: block;
    }

    .banner.warn {
      border-color: #fde68a;
      background: #fffbeb;
      color: #92400e;
    }

    .banner.error {
      border-color: #fecaca;
      background: #fef2f2;
      color: #991b1b;
    }

    .banner.success {
      border-color: #bbf7d0;
      background: #f0fdf4;
      color: #166534;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 18px;
    }

    .panel {
      background: var(--panel);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
      padding: 18px;
      animation: rise-in 500ms ease;
    }

    .panel h2 {
      margin: 0 0 8px;
      font: 700 1.25rem/1.2 "Sora", sans-serif;
      color: #0f172a;
    }

    .panel p {
      margin: 0;
      color: var(--muted);
    }

    .controls {
      margin-top: 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .btn {
      border: 0;
      border-radius: 999px;
      background: var(--brand);
      color: #fff;
      cursor: pointer;
      font: 700 0.82rem/1 "Sora", sans-serif;
      letter-spacing: 0.02em;
      padding: 10px 14px;
      transition: transform 120ms ease, opacity 120ms ease, background 120ms ease;
    }

    .btn:hover {
      transform: translateY(-1px);
      background: var(--brand-strong);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .btn.secondary {
      background: #334155;
    }

    .btn.secondary:hover {
      background: #0f172a;
    }

    .btn.ghost {
      border: 1px solid #cbd5e1;
      color: #334155;
      background: #f8fafc;
    }

    .btn.ghost:hover {
      background: #f1f5f9;
    }

    .health-grid {
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .health-item {
      border-radius: var(--radius-md);
      border: 1px solid #cbd5e1;
      background: #f8fafc;
      padding: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      opacity: 0;
      transform: translateY(8px);
      animation: stagger-in 250ms ease forwards;
    }

    .health-item.up {
      border-color: #86efac;
      background: #f0fdf4;
    }

    .health-item.down {
      border-color: #fecaca;
      background: #fef2f2;
    }

    .health-pill {
      font: 700 0.73rem/1 "Sora", sans-serif;
      padding: 4px 8px;
      border-radius: 999px;
      color: #fff;
    }

    .health-pill.up {
      background: var(--good);
    }

    .health-pill.down {
      background: var(--bad);
    }

    .log-grid {
      margin-top: 14px;
      display: grid;
      gap: 10px;
    }

    .log-card {
      border: 1px solid #dbeafe;
      border-radius: var(--radius-md);
      background: linear-gradient(180deg, #ffffff, #f8fafc);
      padding: 12px;
      display: grid;
      gap: 8px;
      opacity: 0;
      transform: translateY(10px);
      animation: stagger-in 280ms ease forwards;
    }

    .log-card h3 {
      margin: 0;
      font: 700 1rem/1.2 "Sora", sans-serif;
      color: #0f172a;
    }

    .log-card p {
      margin: 0;
      color: #334155;
      font-size: 0.92rem;
    }

    .small-code {
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      border-radius: var(--radius-sm);
      font: 600 0.72rem/1.5 "Consolas", "Courier New", monospace;
      padding: 8px;
      color: #1e293b;
      white-space: pre-wrap;
      max-height: 108px;
      overflow: auto;
    }

    .form-grid {
      margin-top: 12px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .field {
      display: grid;
      gap: 5px;
    }

    .field.span-2 {
      grid-column: span 2;
    }

    .field label {
      font-size: 0.82rem;
      font-weight: 700;
      color: #334155;
      letter-spacing: 0.01em;
    }

    .field input,
    .field select,
    .field textarea {
      border-radius: var(--radius-sm);
      border: 1px solid #cbd5e1;
      padding: 9px 10px;
      font: 500 0.9rem/1.3 "Source Sans 3", sans-serif;
      color: #0f172a;
      outline: none;
      transition: border-color 120ms ease, box-shadow 120ms ease;
      width: 100%;
      background: #fff;
    }

    .field textarea {
      min-height: 88px;
      resize: vertical;
    }

    .field input:focus,
    .field select:focus,
    .field textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px var(--ring);
    }

    .run-summary {
      margin-top: 12px;
      border: 1px solid #fde68a;
      background: #fffbeb;
      border-radius: var(--radius-md);
      padding: 10px;
      color: #92400e;
      font-size: 0.92rem;
      display: none;
    }

    .run-summary.visible {
      display: block;
    }

    .event-card {
      margin-top: 10px;
      border: 1px solid #dbeafe;
      background: #f8fbff;
      border-radius: var(--radius-md);
      padding: 12px;
      display: none;
      gap: 8px;
    }

    .event-card.visible {
      display: grid;
    }

    .event-card h3 {
      margin: 0;
      font: 700 0.98rem/1.2 "Sora", sans-serif;
      color: #0f172a;
    }

    .event-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 0.86rem;
      color: #1e293b;
    }

    .event-row {
      border: 1px solid #dbeafe;
      border-radius: var(--radius-sm);
      background: #ffffff;
      padding: 8px;
    }

    .event-row strong {
      color: #1d4ed8;
    }

    .steps {
      margin-top: 12px;
      display: grid;
      gap: 8px;
    }

    .step-item {
      border-radius: var(--radius-sm);
      border: 1px solid #cbd5e1;
      background: #f8fafc;
      padding: 9px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-size: 0.87rem;
      opacity: 0;
      transform: translateY(10px);
      animation: stagger-in 250ms ease forwards;
    }

    .step-item.ok {
      border-color: #86efac;
      background: #f0fdf4;
      color: #166534;
    }

    .step-item.fail {
      border-color: #fecaca;
      background: #fef2f2;
      color: #991b1b;
    }

    .json-box {
      margin-top: 12px;
      border-radius: var(--radius-md);
      border: 1px solid #0f172a;
      background: #0f172a;
      color: #e2e8f0;
      padding: 12px;
      font: 500 0.74rem/1.45 "Consolas", "Courier New", monospace;
      white-space: pre-wrap;
      max-height: 380px;
      overflow: auto;
    }

    .json-box.hidden {
      display: none;
    }

    .json-box.compact {
      max-height: 240px;
      margin-top: 10px;
    }

    .json-box.invalid {
      border-color: #7f1d1d;
      background: #7f1d1d;
      color: #fee2e2;
    }

    .empty {
      margin-top: 10px;
      border-radius: var(--radius-sm);
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      padding: 12px;
      color: #64748b;
    }

    .overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.55);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      z-index: 60;
    }

    .overlay.visible {
      display: flex;
      animation: fade-in 180ms ease;
    }

    .popup {
      width: min(540px, 100%);
      border-radius: 20px;
      background: #fff;
      box-shadow: var(--shadow);
      border-top: 10px solid var(--brand);
      padding: 20px;
    }

    .popup h3 {
      margin: 0;
      font: 700 1.25rem/1.2 "Sora", sans-serif;
      color: #0f172a;
    }

    .popup p {
      margin: 10px 0 0;
      color: #334155;
      white-space: pre-wrap;
      line-height: 1.5;
    }

    .popup-actions {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }

    @keyframes rise-in {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes stagger-in {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes fade-in {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @media (max-width: 960px) {
      body {
        padding: 16px;
      }

      .grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 680px) {
      .hero h1 {
        font-size: 1.65rem;
      }

      .form-grid {
        grid-template-columns: 1fr;
      }

      .field.span-2 {
        grid-column: span 1;
      }

      .health-grid {
        grid-template-columns: 1fr;
      }

      .event-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <h1>Pipeline Demo Control Room</h1>
      <p>Trigger the processing hop from this standalone microservice and let the downstream chain continue service-to-service: detection to incident to response to actuator.</p>
      <div class="badge-row">
        <span class="badge">Standalone microservice</span>
        <span class="badge">Prebuilt logs ready</span>
        <span class="badge">Live downstream health</span>
      </div>
    </section>

    <div id="banner" class="banner" role="status" aria-live="polite"></div>

    <section class="grid">
      <article class="panel">
        <h2>Prebuilt Incident Logs</h2>
        <p>Each prebuilt log is crafted to exercise a specific response path.</p>
        <div class="controls">
          <button id="refreshPrebuilt" class="btn ghost" type="button">Refresh Logs</button>
        </div>
        <div id="prebuiltGrid" class="log-grid"></div>
      </article>

      <article class="panel">
        <h2>Pipeline Health</h2>
        <p>Checks downstream service readiness before and after every run.</p>
        <div class="controls">
          <button id="checkHealth" class="btn secondary" type="button">Check Health</button>
        </div>
        <div id="healthGrid" class="health-grid"></div>
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>Custom Event Runner</h2>
        <p>Send a custom payload to /demo/pipeline-run when you need full control.</p>
        <form id="customEventForm" class="form-grid">
          <div class="field">
            <label for="event_type">Event Type</label>
            <input id="event_type" name="event_type" value="deployment.failed" required />
          </div>
          <div class="field">
            <label for="service_name">Service Name</label>
            <input id="service_name" name="service_name" value="deployment-service" required />
          </div>
          <div class="field span-2">
            <label for="message">Message</label>
            <input id="message" name="message" value="Custom pipeline demo event" required />
          </div>
          <div class="field">
            <label for="log_level">Log Level</label>
            <select id="log_level" name="log_level">
              <option value="ERROR" selected>ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
            </select>
          </div>
          <div class="field">
            <label for="environment">Environment</label>
            <input id="environment" name="environment" value="production" required />
          </div>
          <div class="field">
            <label for="status_code">Status Code</label>
            <input id="status_code" name="status_code" type="number" min="100" max="599" value="500" required />
          </div>
          <div class="field">
            <label for="latency_ms">Latency (ms)</label>
            <input id="latency_ms" name="latency_ms" type="number" min="1" value="1200" required />
          </div>
          <div class="field span-2">
            <label for="metadata_json">Metadata JSON Object</label>
            <textarea id="metadata_json" name="metadata_json" spellcheck="false">{"reason":"manual demo trigger"}</textarea>
          </div>
          <div class="field span-2">
            <button id="runCustom" class="btn" type="submit">Run Custom Event</button>
          </div>
        </form>
        <div class="controls">
          <button id="copyPayload" class="btn ghost" type="button">Copy Payload JSON</button>
        </div>
        <pre id="payloadPreview" class="json-box compact">Payload preview will appear here.</pre>
      </article>

      <article class="panel">
        <h2>Execution Output</h2>
        <p>Track processing acceptance and inspect full payload details from the trigger call.</p>
        <div id="runSummary" class="run-summary"></div>
        <section id="eventCard" class="event-card">
          <h3>Event and Response Details</h3>
          <div id="eventGrid" class="event-grid"></div>
        </section>
        <div id="steps" class="steps"></div>
        <pre id="jsonBox" class="json-box hidden">Run a prebuilt log or custom event to view pipeline output.</pre>
        <div class="controls">
          <button id="toggleRawJson" class="btn ghost" type="button">Show Raw JSON</button>
          <button id="showPopupAgain" class="btn ghost" type="button" disabled>Show Completion Popup Again</button>
        </div>
      </article>
    </section>
  </main>

  <div id="popupOverlay" class="overlay" aria-hidden="true">
    <section class="popup" role="dialog" aria-modal="true" aria-labelledby="popupTitle">
      <h3 id="popupTitle">Pipeline Run Finished</h3>
      <p id="popupBody"></p>
      <div class="popup-actions">
        <button id="copyResult" class="btn ghost" type="button">Copy Summary</button>
        <button id="closePopup" class="btn" type="button">Close</button>
      </div>
    </section>
  </div>

  <script>
    const API = {
      prebuilt: "/demo/prebuilt-logs",
      health: "/demo/pipeline-health",
      run: "/demo/pipeline-run"
    };

    const state = {
      prebuiltLogs: [],
      healthSnapshot: null,
      lastResult: null,
      running: false,
      lastSource: "",
      showRawJson: false
    };

    const elements = {
      banner: document.getElementById("banner"),
      prebuiltGrid: document.getElementById("prebuiltGrid"),
      refreshPrebuilt: document.getElementById("refreshPrebuilt"),
      checkHealth: document.getElementById("checkHealth"),
      healthGrid: document.getElementById("healthGrid"),
      customEventForm: document.getElementById("customEventForm"),
      runCustom: document.getElementById("runCustom"),
      copyPayload: document.getElementById("copyPayload"),
      payloadPreview: document.getElementById("payloadPreview"),
      runSummary: document.getElementById("runSummary"),
      eventCard: document.getElementById("eventCard"),
      eventGrid: document.getElementById("eventGrid"),
      steps: document.getElementById("steps"),
      jsonBox: document.getElementById("jsonBox"),
      toggleRawJson: document.getElementById("toggleRawJson"),
      showPopupAgain: document.getElementById("showPopupAgain"),
      popupOverlay: document.getElementById("popupOverlay"),
      popupTitle: document.getElementById("popupTitle"),
      popupBody: document.getElementById("popupBody"),
      closePopup: document.getElementById("closePopup"),
      copyResult: document.getElementById("copyResult")
    };

    function escapeHtml(value) {
      const text = String(value === undefined || value === null ? "" : value);
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function setBanner(message, variant) {
      if (!message) {
        elements.banner.className = "banner";
        elements.banner.textContent = "";
        return;
      }
      const className = variant ? "banner visible " + variant : "banner visible";
      elements.banner.className = className;
      elements.banner.textContent = message;
    }

    async function fetchJson(url, options) {
      const response = await fetch(url, options || {});
      let payload = {};
      try {
        payload = await response.json();
      } catch (error) {
        payload = {};
      }

      if (!response.ok) {
        let message = "Request failed";
        if (payload && typeof payload === "object") {
          if (typeof payload.detail === "string") {
            message = payload.detail;
          } else if (payload.detail && typeof payload.detail === "object" && typeof payload.detail.message === "string") {
            message = payload.detail.message;
          }
        }
        const requestError = new Error(message + " (" + response.status + ")");
        requestError.responsePayload = payload;
        requestError.statusCode = response.status;
        throw requestError;
      }

      return payload;
    }

    async function copyText(text) {
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(text);
          return;
        } catch (error) {
          // Fall back to execCommand path below.
        }
      }

      const helper = document.createElement("textarea");
      helper.value = text;
      helper.setAttribute("readonly", "true");
      helper.style.position = "fixed";
      helper.style.opacity = "0";
      helper.style.pointerEvents = "none";
      helper.style.top = "0";
      helper.style.left = "0";

      document.body.appendChild(helper);
      helper.focus();
      helper.select();

      const copied = document.execCommand("copy");
      document.body.removeChild(helper);

      if (!copied) {
        throw new Error("Clipboard copy is not supported in this context.");
      }
    }

    async function copyTextOrPrompt(text) {
      try {
        await copyText(text);
        return true;
      } catch (error) {
        window.prompt("Clipboard access is blocked. Copy manually:", text);
        return false;
      }
    }

    function setRunning(isRunning) {
      state.running = isRunning;
      elements.runCustom.disabled = isRunning;
      elements.copyPayload.disabled = isRunning;
      elements.checkHealth.disabled = isRunning;
      elements.refreshPrebuilt.disabled = isRunning;

      const runButtons = document.querySelectorAll("[data-run-prebuilt]");
      runButtons.forEach((button) => {
        button.disabled = isRunning;
      });
    }

    function renderHealth(snapshot) {
      if (!snapshot || !Array.isArray(snapshot.services) || !snapshot.services.length) {
        elements.healthGrid.innerHTML = '<div class="empty">No health snapshot yet.</div>';
        return;
      }

      let html = "";
      snapshot.services.forEach((service, index) => {
        const isUp = Boolean(service && service.ok);
        const itemClass = isUp ? "up" : "down";
        const badgeClass = isUp ? "up" : "down";
        const serviceName = service && service.service ? service.service : "unknown";
        html += '<div class="health-item ' + itemClass + '" style="animation-delay:' + (index * 70) + 'ms">';
        html += '<div>' + escapeHtml(serviceName) + '</div>';
        html += '<span class="health-pill ' + badgeClass + '">' + (isUp ? "UP" : "DOWN") + '</span>';
        html += '</div>';
      });
      elements.healthGrid.innerHTML = html;
    }

    function renderPrebuilt() {
      if (!state.prebuiltLogs.length) {
        elements.prebuiltGrid.innerHTML = '<div class="empty">No prebuilt logs found.</div>';
        return;
      }

      let html = "";
      state.prebuiltLogs.forEach((item, index) => {
        const itemId = item && item.id ? item.id : "unknown";
        const itemLabel = item && item.label ? item.label : itemId;
        const itemDescription = item && item.description ? item.description : "Prebuilt payload";
        const payloadPreview = JSON.stringify(item.payload || {}, null, 2);

        html += '<article class="log-card" style="animation-delay:' + (index * 60) + 'ms">';
        html += '<h3>' + escapeHtml(itemLabel) + '</h3>';
        html += '<p>' + escapeHtml(itemDescription) + '</p>';
        html += '<div class="small-code">' + escapeHtml(payloadPreview) + '</div>';
        html += '<button class="btn" type="button" data-run-prebuilt="' + escapeHtml(itemId) + '">Run This Log</button>';
        html += '</article>';
      });

      elements.prebuiltGrid.innerHTML = html;

      const buttons = document.querySelectorAll("[data-run-prebuilt]");
      buttons.forEach((button) => {
        button.addEventListener("click", async () => {
          const id = button.getAttribute("data-run-prebuilt");
          const selected = state.prebuiltLogs.find((item) => item && item.id === id);
          if (!selected || !selected.payload) {
            setBanner("Selected prebuilt payload is unavailable.", "error");
            return;
          }
          await runPipeline(selected.payload, selected.label || id);
        });
      });
    }

    function renderSteps(steps) {
      if (!Array.isArray(steps) || !steps.length) {
        elements.steps.innerHTML = '<div class="empty">No pipeline steps recorded.</div>';
        return;
      }

      let html = "";
      steps.forEach((step, index) => {
        const ok = Boolean(step && step.ok);
        const className = ok ? "ok" : "fail";
        const stepName = step && step.step ? step.step : "step";
        const label = ok ? "OK" : "ISSUE";
        html += '<div class="step-item ' + className + '" style="animation-delay:' + (index * 60) + 'ms">';
        html += '<strong>' + escapeHtml(stepName) + '</strong>';
        html += '<span>' + label + '</span>';
        html += '</div>';
      });
      elements.steps.innerHTML = html;
    }

    function renderEventCard(result) {
      const rawEvent = result && result.raw_event && typeof result.raw_event === "object"
        ? result.raw_event
        : {};
      const metadata = rawEvent.metadata && typeof rawEvent.metadata === "object"
        ? rawEvent.metadata
        : {};

      const steps = result && Array.isArray(result.steps) ? result.steps : [];
      const processingStep = steps.find((step) => step && step.step === "processing") || {};

      const actuator =
        (result && result.latest_actuator_execution && typeof result.latest_actuator_execution === "object" && result.latest_actuator_execution)
        || (result && result.actuator_forwarding && result.actuator_forwarding.execution && typeof result.actuator_forwarding.execution === "object" && result.actuator_forwarding.execution)
        || null;

      const rows = [];
      rows.push({ label: "Event Type", value: rawEvent.event_type || "n/a" });
      rows.push({ label: "Service", value: rawEvent.service_name || "n/a" });
      rows.push({ label: "Environment", value: rawEvent.environment || "n/a" });
      rows.push({ label: "Status Code", value: metadata.status_code || metadata.status || "n/a" });
      rows.push({ label: "Latency (ms)", value: metadata.latency_ms || "n/a" });
      rows.push({ label: "Processing", value: processingStep.summary || (processingStep.ok ? "processed" : "not processed") });

      if (actuator) {
        rows.push({ label: "Actuator Action", value: actuator.action || "n/a" });
        rows.push({ label: "Actuator Status", value: actuator.execution_status || "n/a" });
        rows.push({ label: "Actuator Output", value: actuator.output || "n/a" });
        rows.push({ label: "Executed At", value: actuator.executed_at || "n/a" });
      } else {
        rows.push({ label: "Actuator", value: "Waiting for downstream response generation" });
      }

      let html = "";
      rows.forEach((row) => {
        html += '<div class="event-row"><strong>' + escapeHtml(row.label) + ':</strong> ' + escapeHtml(row.value) + '</div>';
      });

      elements.eventGrid.innerHTML = html;
      elements.eventCard.className = "event-card visible";
    }

    function renderResult(result) {
      state.lastResult = result;
      elements.showPopupAgain.disabled = !state.lastResult;

      const status = result && result.status ? result.status : "unknown";
      const demoId = result && result.demo_id ? result.demo_id : "n/a";
      const reason = result && result.reason ? result.reason : "";
      const message = result && result.message ? result.message : "";
      const action = result && result.response_execution && result.response_execution.action
        ? result.response_execution.action
        : "none";

      const summaryText = "Demo " + demoId + " completed with status " + status + ". Action: " + action + (message ? ". " + message : "") + (reason ? ". Reason: " + reason : "");
      elements.runSummary.className = "run-summary visible";
      elements.runSummary.textContent = summaryText;

      renderEventCard(result || {});
      renderSteps(result && result.steps ? result.steps : []);
      elements.jsonBox.textContent = JSON.stringify(result, null, 2);
      elements.jsonBox.classList.toggle("hidden", !state.showRawJson);
      elements.toggleRawJson.textContent = state.showRawJson ? "Hide Raw JSON" : "Show Raw JSON";
    }

    function showPopup(result, source) {
      if (!result) {
        return;
      }

      const status = result.status || "unknown";
      const demoId = result.demo_id || "n/a";
      const action = result.response_execution && result.response_execution.action
        ? result.response_execution.action
        : "none";
      const message = result.message ? "\nMessage: " + result.message : "";
      const reason = result.reason ? "\nReason: " + result.reason : "";
      const sourceLabel = source ? source : "custom payload";

      const title = status === "completed"
        ? "Pipeline Run Completed"
        : (status === "accepted" ? "Processing Trigger Accepted" : "Pipeline Run Finished with Notes");

      const bodyText = "Source: " + sourceLabel + "\nDemo ID: " + demoId + "\nStatus: " + status + "\nAction: " + action + message + reason;

      elements.popupTitle.textContent = title;
      elements.popupBody.textContent = bodyText;
      elements.popupOverlay.classList.add("visible");
      elements.popupOverlay.setAttribute("aria-hidden", "false");
    }

    function closePopup() {
      elements.popupOverlay.classList.remove("visible");
      elements.popupOverlay.setAttribute("aria-hidden", "true");
    }

    function parseMetadata(rawText) {
      if (!rawText || !rawText.trim()) {
        return {};
      }
      const parsed = JSON.parse(rawText);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Metadata must be a JSON object.");
      }
      return parsed;
    }

    function buildCustomPayload() {
      const form = new FormData(elements.customEventForm);
      const statusCode = Number(form.get("status_code") || 500);
      const latencyMs = Number(form.get("latency_ms") || 1200);

      if (!Number.isFinite(statusCode) || statusCode < 100 || statusCode > 599) {
        throw new Error("Status code must be between 100 and 599.");
      }
      if (!Number.isFinite(latencyMs) || latencyMs < 1) {
        throw new Error("Latency must be at least 1 ms.");
      }

      return {
        event_type: String(form.get("event_type") || "deployment.failed").trim(),
        service_name: String(form.get("service_name") || "deployment-service").trim(),
        message: String(form.get("message") || "Custom pipeline demo event").trim(),
        log_level: String(form.get("log_level") || "ERROR").trim(),
        environment: String(form.get("environment") || "production").trim(),
        status_code: statusCode,
        latency_ms: latencyMs,
        metadata: parseMetadata(String(form.get("metadata_json") || "{}")),
      };
    }

    function updatePayloadPreview() {
      try {
        const payload = buildCustomPayload();
        elements.payloadPreview.classList.remove("invalid");
        elements.payloadPreview.textContent = JSON.stringify(payload, null, 2);
        return payload;
      } catch (error) {
        elements.payloadPreview.classList.add("invalid");
        elements.payloadPreview.textContent = "Payload is invalid: " + error.message;
        return null;
      }
    }

    async function loadPrebuiltLogs() {
      try {
        const payload = await fetchJson(API.prebuilt);
        state.prebuiltLogs = Array.isArray(payload.items) ? payload.items : [];
        renderPrebuilt();
        return true;
      } catch (error) {
        state.prebuiltLogs = [];
        renderPrebuilt();
        setBanner(error.message, "error");
        return false;
      }
    }

    async function loadHealth() {
      try {
        const health = await fetchJson(API.health);
        state.healthSnapshot = health;
        renderHealth(health);
        return true;
      } catch (error) {
        state.healthSnapshot = null;
        renderHealth(null);
        setBanner(error.message, "error");
        return false;
      }
    }

    async function runPipeline(payload, sourceLabel) {
      if (state.running) {
        return;
      }

      setRunning(true);
      setBanner("Running pipeline for " + sourceLabel + "...", "warn");

      try {
        const result = await fetchJson(API.run, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        renderResult(result);
        if (result && result.pipeline_health) {
          state.healthSnapshot = result.pipeline_health;
          renderHealth(result.pipeline_health);
        }

        state.lastSource = sourceLabel;
        showPopup(result, sourceLabel);

        const status = result && result.status ? result.status : "unknown";
        const variant = status === "completed" ? "success" : "warn";
        setBanner("Pipeline run finished with status: " + status + ".", variant);
      } catch (error) {
        const detail = error && error.responsePayload && error.responsePayload.detail;
        if (detail && typeof detail === "object") {
          const partialResult = {
            demo_id: state.lastResult && state.lastResult.demo_id ? state.lastResult.demo_id : "n/a",
            status: "failed",
            reason: detail.message || error.message,
            failed_step: detail.failed_step || "unknown",
            raw_event: payload,
            steps: Array.isArray(detail.steps) ? detail.steps : [],
            response_attempts: Array.isArray(detail.response_attempts) ? detail.response_attempts : []
          };
          renderResult(partialResult);
        }
        setBanner(detail && detail.message ? detail.message : error.message, "error");
      } finally {
        setRunning(false);
      }
    }

    elements.refreshPrebuilt.addEventListener("click", async () => {
      const ok = await loadPrebuiltLogs();
      if (ok) {
        setBanner("Prebuilt logs refreshed.", "success");
      }
    });

    elements.checkHealth.addEventListener("click", async () => {
      const ok = await loadHealth();
      if (ok && state.healthSnapshot) {
        const allHealthy = Boolean(state.healthSnapshot.ok);
        setBanner(
          allHealthy ? "All downstream services are healthy." : "One or more downstream services are unhealthy.",
          allHealthy ? "success" : "warn"
        );
      }
    });

    elements.customEventForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const payload = updatePayloadPreview();
        if (!payload) {
          throw new Error("Fix payload JSON errors before running.");
        }

        await runPipeline(payload, "custom payload");
      } catch (error) {
        setBanner(error.message, "error");
      }
    });

    const customFormInputs = elements.customEventForm.querySelectorAll("input, select, textarea");
    customFormInputs.forEach((input) => {
      input.addEventListener("input", updatePayloadPreview);
      input.addEventListener("change", updatePayloadPreview);
    });

    elements.copyPayload.addEventListener("click", async () => {
      const payload = updatePayloadPreview();
      if (!payload) {
        setBanner("Payload JSON is invalid. Fix form fields first.", "error");
        return;
      }

      const copied = await copyTextOrPrompt(JSON.stringify(payload, null, 2));
      if (copied) {
        setBanner("Payload JSON copied.", "success");
      } else {
        setBanner("Clipboard blocked. Opened manual copy dialog.", "warn");
      }
    });

    elements.toggleRawJson.addEventListener("click", () => {
      state.showRawJson = !state.showRawJson;
      elements.jsonBox.classList.toggle("hidden", !state.showRawJson);
      elements.toggleRawJson.textContent = state.showRawJson ? "Hide Raw JSON" : "Show Raw JSON";
    });

    elements.showPopupAgain.addEventListener("click", () => {
      if (state.lastResult) {
        showPopup(state.lastResult, state.lastSource || "custom payload");
      }
    });

    elements.closePopup.addEventListener("click", closePopup);

    elements.popupOverlay.addEventListener("click", (event) => {
      if (event.target === elements.popupOverlay) {
        closePopup();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && elements.popupOverlay.classList.contains("visible")) {
        closePopup();
      }
    });

    elements.copyResult.addEventListener("click", async () => {
      if (!state.lastResult) {
        return;
      }

      const status = state.lastResult.status || "unknown";
      const demoId = state.lastResult.demo_id || "n/a";
      const action = state.lastResult.response_execution && state.lastResult.response_execution.action
        ? state.lastResult.response_execution.action
        : "none";
      const summary = "Demo ID: " + demoId + "\nStatus: " + status + "\nAction: " + action;

      const copied = await copyTextOrPrompt(summary);
      if (copied) {
        setBanner("Summary copied to clipboard.", "success");
      } else {
        setBanner("Clipboard blocked. Opened manual copy dialog.", "warn");
      }
    });

    async function initialize() {
      setBanner("Loading pipeline dashboard...", "warn");
      await Promise.all([loadPrebuiltLogs(), loadHealth()]);
      updatePayloadPreview();
      elements.toggleRawJson.textContent = "Show Raw JSON";
      setBanner("Dashboard ready. Choose a prebuilt log or run a custom event.", "success");
    }

    initialize();
  </script>
</body>
</html>
"""
