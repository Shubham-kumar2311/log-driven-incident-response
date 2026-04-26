"""Dashboard UI for the pipeline demo microservice."""


def render_dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pipeline Demo</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    :root{
      --bg:#0d1117;--surface:#161b22;--surface2:#1c2333;--surface3:#21293a;
      --border:#30363d;--border-light:#3d444d;
      --text:#e6edf3;--text2:#8b949e;--text3:#6e7681;
      --accent:#58a6ff;--accent-dim:rgba(88,166,255,.15);
      --green:#3fb950;--green-dim:rgba(63,185,80,.15);
      --yellow:#d29922;--yellow-dim:rgba(210,153,34,.15);
      --red:#f85149;--red-dim:rgba(248,81,73,.15);
      --orange:#db6d28;--orange-dim:rgba(219,109,40,.15);
      --purple:#bc8cff;--purple-dim:rgba(188,140,255,.15);
    }
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.5;overflow-x:hidden}
    a{color:var(--accent);text-decoration:none}
    ::-webkit-scrollbar{width:8px}
    ::-webkit-scrollbar-track{background:transparent}
    ::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
    ::-webkit-scrollbar-thumb:hover{background:var(--border-light)}

    /* ── Header ── */
    .header{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
    .header-left{display:flex;align-items:center;gap:12px}
    .header-logo{width:28px;height:28px;background:var(--accent);border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:#fff}
    .header h1{font-size:15px;font-weight:600}
    .header .status{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text2)}
    .header .dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse-dot 2s ease-in-out infinite}
    @keyframes pulse-dot{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(63,185,80,.4)}50%{opacity:.8;box-shadow:0 0 0 6px rgba(63,185,80,0)}}

    /* ── Layout ── */
    .container{display:flex;height:calc(100vh - 49px)}
    .sidebar{width:360px;min-width:300px;border-right:1px solid var(--border);display:flex;flex-direction:column;background:var(--surface)}
    .main{flex:1;overflow-y:auto;padding:24px 28px}

    /* ── Sidebar sections ── */
    .sb-section{border-bottom:1px solid var(--border);padding:14px}
    .sb-section h2{font-size:13px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}

    /* ── Prebuilt event list ── */
    .prebuilt-list{display:flex;flex-direction:column;gap:4px;max-height:calc(100vh - 240px);overflow-y:auto}
    .prebuilt-item{padding:10px 12px;border:1px solid var(--border);border-radius:6px;cursor:pointer;transition:all .2s;border-left:3px solid transparent;background:var(--surface2)}
    .prebuilt-item:hover{background:var(--surface3);border-color:var(--border-light)}
    .prebuilt-item.active{background:var(--surface3);border-left-color:var(--accent)}
    .prebuilt-item .pi-label{font-size:13px;font-weight:600;color:var(--text)}
    .prebuilt-item .pi-desc{font-size:11px;color:var(--text2);margin-top:2px}
    .prebuilt-item .pi-type{font-size:10px;color:var(--accent);font-family:monospace;margin-top:4px}

    /* ── Banner ── */
    .banner{padding:10px 16px;font-size:13px;display:none;border-bottom:1px solid var(--border)}
    .banner.visible{display:block}
    .banner.info{background:var(--accent-dim);color:var(--accent);border-color:rgba(88,166,255,.3)}
    .banner.warn{background:var(--yellow-dim);color:var(--yellow);border-color:rgba(210,153,34,.3)}
    .banner.error{background:var(--red-dim);color:var(--red);border-color:rgba(248,81,73,.3)}
    .banner.success{background:var(--green-dim);color:var(--green);border-color:rgba(63,185,80,.3)}

    /* ── Panels / cards ── */
    .panel{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px 18px;margin-bottom:16px;animation:fadeIn .25s ease}
    .panel h2{font-size:14px;font-weight:600;margin-bottom:12px;color:var(--text)}
    .panel p.hint{font-size:12px;color:var(--text3);margin-bottom:10px}
    @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}

    /* ── Buttons ── */
    .btn{padding:7px 16px;border-radius:6px;border:1px solid var(--border);background:var(--surface2);color:var(--text);font-size:12px;cursor:pointer;transition:all .2s;font-weight:500}
    .btn:hover{background:var(--surface3);border-color:var(--border-light)}
    .btn:active{transform:scale(.97)}
    .btn:disabled{opacity:.5;cursor:not-allowed}
    .btn-primary{background:rgba(88,166,255,.15);border-color:rgba(88,166,255,.4);color:var(--accent)}
    .btn-primary:hover{background:rgba(88,166,255,.25);border-color:var(--accent)}
    .btn-success{background:rgba(63,185,80,.15);border-color:rgba(63,185,80,.4);color:var(--green)}
    .btn-success:hover{background:rgba(63,185,80,.25);border-color:var(--green)}
    .btn-danger{background:var(--red-dim);border-color:rgba(248,81,73,.4);color:var(--red)}

    /* ── Form fields ── */
    .form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .field{display:grid;gap:4px}
    .field.span-2{grid-column:span 2}
    .field label{font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.5px}
    .field input,.field select,.field textarea{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;border-radius:6px;font-size:12px;font-family:inherit;transition:border-color .2s;width:100%}
    .field input:focus,.field select:focus,.field textarea:focus{border-color:var(--accent);outline:none}
    .field textarea{min-height:60px;resize:vertical;font-family:'Consolas','Courier New',monospace}

    /* ── JSON editor ── */
    .json-editor{position:relative}
    .json-editor textarea{background:var(--bg);border:1px solid var(--border);color:#e2e8f0;padding:12px;border-radius:6px;font:12px/1.5 'Consolas','Courier New',monospace;width:100%;min-height:180px;resize:vertical;tab-size:2}
    .json-editor textarea:focus{border-color:var(--accent);outline:none}
    .json-editor textarea.invalid{border-color:var(--red)}
    .json-editor .je-toolbar{display:flex;gap:6px;margin-top:6px;align-items:center}
    .json-editor .je-status{font-size:11px;color:var(--text3);margin-left:auto}
    .json-editor .je-status.ok{color:var(--green)}
    .json-editor .je-status.err{color:var(--red)}

    /* ── Run summary ── */
    .run-summary{padding:12px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);font-size:12px;color:var(--text2);display:none;margin-bottom:12px}
    .run-summary.visible{display:block}

    /* ── Event detail card ── */
    .event-card{border:1px solid var(--border);border-radius:6px;background:var(--surface2);padding:14px;display:none;gap:8px;margin-bottom:12px}
    .event-card.visible{display:grid}
    .event-card h3{font-size:13px;font-weight:600;color:var(--accent);margin-bottom:4px}
    .event-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .event-row{border:1px solid var(--border);border-radius:4px;background:var(--surface3);padding:6px 8px;font-size:12px;color:var(--text2)}
    .event-row strong{color:var(--accent)}

    /* ── Steps ── */
    .steps{display:grid;gap:6px;margin-bottom:12px}
    .step-item{border-radius:4px;border:1px solid var(--border);background:var(--surface2);padding:8px 10px;display:flex;justify-content:space-between;align-items:center;font-size:12px}
    .step-item.ok{border-color:rgba(63,185,80,.3);color:var(--green)}
    .step-item.fail{border-color:rgba(248,81,73,.3);color:var(--red)}

    /* ── Raw JSON box ── */
    .json-box{border-radius:6px;border:1px solid var(--border);background:var(--bg);color:#e2e8f0;padding:12px;font:12px/1.5 'Consolas','Courier New',monospace;white-space:pre-wrap;max-height:360px;overflow:auto;margin-bottom:12px}
    .json-box.hidden{display:none}

    /* ── Controls row ── */
    .controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}

    /* ── Responsive ── */
    @media(max-width:860px){
      .container{flex-direction:column}
      .sidebar{width:100%;min-width:0;max-height:260px;overflow-y:auto;border-right:none;border-bottom:1px solid var(--border)}
      .form-grid{grid-template-columns:1fr}
      .field.span-2{grid-column:span 1}
      .event-grid{grid-template-columns:1fr}
    }
  </style>
</head>
<body>

<!-- ── Header ── -->
<div class="header">
  <div class="header-left">
    <div class="header-logo">P</div>
    <h1>Pipeline Demo Console</h1>
  </div>
  <div class="status">
    <span class="dot"></span>
    <span id="statusText">Loading...</span>
  </div>
</div>

<!-- ── Banner ── -->
<div id="banner" class="banner" role="status" aria-live="polite"></div>

<!-- ── Main layout ── -->
<div class="container">

  <!-- ── Sidebar: prebuilt event switcher ── -->
  <div class="sidebar">
    <div class="sb-section">
      <h2>Prebuilt Events</h2>
      <div id="prebuiltList" class="prebuilt-list"></div>
    </div>
  </div>

  <!-- ── Main content ── -->
  <div class="main">

    <!-- Custom Event Runner -->
    <div class="panel">
      <h2>Custom Event Runner</h2>
      <p class="hint">Edit fields or directly modify the JSON payload below. Changes sync both ways.</p>

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
          <label for="metadata_json">Metadata JSON</label>
          <textarea id="metadata_json" name="metadata_json" spellcheck="false">{"reason":"manual demo trigger"}</textarea>
        </div>
      </form>

      <!-- Live editable JSON preview -->
      <div class="json-editor" style="margin-top:12px">
        <label style="font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:4px">Payload JSON (editable)</label>
        <textarea id="jsonEditorArea" spellcheck="false"></textarea>
        <div class="je-toolbar">
          <button id="copyPayload" class="btn" type="button">Copy JSON</button>
          <button id="runCustom" class="btn btn-primary" type="button">Run Event</button>
          <span id="jsonStatus" class="je-status"></span>
        </div>
      </div>
    </div>

    <!-- Execution Output -->
    <div class="panel">
      <h2>Actuator Payload Received</h2>
      <p class="hint">Only payload received by actuator is shown below.</p>
      <div id="runSummary" class="run-summary"></div>
      <section id="eventCard" class="event-card">
        <h3>Actuator Execution Details</h3>
        <div id="eventGrid" class="event-grid"></div>
      </section>
      <div id="steps" class="steps"></div>
      <pre id="jsonBox" class="json-box hidden"></pre>
      <div class="controls">
        <button id="toggleRawJson" class="btn" type="button">Show Actuator Payload JSON</button>
      </div>
    </div>

  </div><!-- /.main -->
</div><!-- /.container -->

<script>
(function(){
  "use strict";

  const API = {
    prebuilt: "/demo/prebuilt-logs",
    health: "/demo/pipeline-health",
    run: "/demo/pipeline-run"
  };

  const state = {
    prebuiltLogs: [],
    selectedPrebuiltIdx: -1,
    lastResult: null,
    running: false,
    lastSource: "",
    showRawJson: false,
    jsonEditorDirty: false   // true when user edits JSON directly
  };

  /* ── Element refs ── */
  const $ = id => document.getElementById(id);
  const el = {
    banner: $("banner"),
    statusText: $("statusText"),
    prebuiltList: $("prebuiltList"),
    form: $("customEventForm"),
    jsonEditor: $("jsonEditorArea"),
    jsonStatus: $("jsonStatus"),
    copyPayload: $("copyPayload"),
    runCustom: $("runCustom"),
    runSummary: $("runSummary"),
    eventCard: $("eventCard"),
    eventGrid: $("eventGrid"),
    steps: $("steps"),
    jsonBox: $("jsonBox"),
    toggleRawJson: $("toggleRawJson"),
  };

  /* ── Helpers ── */
  function esc(v){
    const s = String(v==null?"":v);
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
  }

  function setBanner(msg, variant){
    if(!msg){el.banner.className="banner";el.banner.textContent="";return}
    el.banner.className="banner visible "+(variant||"info");
    el.banner.textContent=msg;
  }

  async function fetchJson(url, opts){
    const r = await fetch(url, opts||{});
    let body={};try{body=await r.json()}catch(e){}
    if(!r.ok){
      let m="Request failed";
      if(body&&typeof body==="object"){
        if(typeof body.detail==="string")m=body.detail;
        else if(body.detail&&typeof body.detail.message==="string")m=body.detail.message;
      }
      const err=new Error(m+" ("+r.status+")");err.responsePayload=body;err.statusCode=r.status;throw err;
    }
    return body;
  }

  async function copyToClipboard(text){
    if(navigator.clipboard&&window.isSecureContext){
      try{await navigator.clipboard.writeText(text);return true}catch(e){}
    }
    const ta=document.createElement("textarea");
    ta.value=text;ta.setAttribute("readonly","true");
    ta.style.cssText="position:fixed;opacity:0;pointer-events:none;top:0;left:0";
    document.body.appendChild(ta);ta.focus();ta.select();
    const ok=document.execCommand("copy");
    document.body.removeChild(ta);
    if(!ok)throw new Error("Copy not supported");
    return true;
  }

  async function copyOrPrompt(text){
    try{await copyToClipboard(text);return true}catch(e){window.prompt("Copy manually:",text);return false}
  }

  function setRunning(v){
    state.running=v;
    el.runCustom.disabled=v;
    el.copyPayload.disabled=v;
    document.querySelectorAll("[data-run-idx]").forEach(b=>{b.disabled=v});
  }

  /* ── Form <-> JSON sync ── */
  function formToPayload(){
    const fd=new FormData(el.form);
    const sc=Number(fd.get("status_code")||500);
    const lm=Number(fd.get("latency_ms")||1200);
    let meta={};
    try{const p=JSON.parse(fd.get("metadata_json")||"{}");if(p&&typeof p==="object"&&!Array.isArray(p))meta=p;}catch(e){}
    return {
      event_type:String(fd.get("event_type")||"").trim(),
      service_name:String(fd.get("service_name")||"").trim(),
      message:String(fd.get("message")||"").trim(),
      log_level:String(fd.get("log_level")||"ERROR").trim(),
      environment:String(fd.get("environment")||"").trim(),
      status_code:sc,
      latency_ms:lm,
      metadata:meta
    };
  }

  function payloadToForm(p){
    if(!p||typeof p!=="object")return;
    const s=k=>el.form.elements[k];
    if(p.event_type!=null&&s("event_type"))s("event_type").value=p.event_type;
    if(p.service_name!=null&&s("service_name"))s("service_name").value=p.service_name;
    if(p.message!=null&&s("message"))s("message").value=p.message;
    if(p.log_level!=null&&s("log_level"))s("log_level").value=p.log_level;
    if(p.environment!=null&&s("environment"))s("environment").value=p.environment;
    if(p.status_code!=null&&s("status_code"))s("status_code").value=p.status_code;
    if(p.latency_ms!=null&&s("latency_ms"))s("latency_ms").value=p.latency_ms;
    if(p.metadata!=null&&s("metadata_json"))s("metadata_json").value=JSON.stringify(p.metadata,null,2);
  }

  function syncFormToEditor(){
    if(state.jsonEditorDirty)return;
    const p=formToPayload();
    el.jsonEditor.value=JSON.stringify(p,null,2);
    el.jsonEditor.classList.remove("invalid");
    el.jsonStatus.textContent="Valid JSON";
    el.jsonStatus.className="je-status ok";
  }

  function syncEditorToForm(){
    const raw=el.jsonEditor.value;
    try{
      const p=JSON.parse(raw);
      if(!p||typeof p!=="object"||Array.isArray(p))throw new Error("Must be object");
      el.jsonEditor.classList.remove("invalid");
      el.jsonStatus.textContent="Valid JSON";
      el.jsonStatus.className="je-status ok";
      payloadToForm(p);
      return p;
    }catch(e){
      el.jsonEditor.classList.add("invalid");
      el.jsonStatus.textContent="Invalid: "+e.message;
      el.jsonStatus.className="je-status err";
      return null;
    }
  }

  function getCurrentPayload(){
    if(state.jsonEditorDirty){
      return syncEditorToForm();
    }
    return formToPayload();
  }

  /* ── Prebuilt events ── */
  function renderPrebuiltList(){
    if(!state.prebuiltLogs.length){
      el.prebuiltList.innerHTML='<div style="padding:12px;color:var(--text3);font-size:12px">No prebuilt events found.</div>';
      return;
    }
    let html="";
    state.prebuiltLogs.forEach((item,i)=>{
      const active=i===state.selectedPrebuiltIdx?"active":"";
      const evType=item.payload&&item.payload.event_type?item.payload.event_type:"";
      html+='<div class="prebuilt-item '+active+'" data-run-idx="'+i+'">';
      html+='<div class="pi-label">'+esc(item.label||item.id||"Event "+i)+'</div>';
      html+='<div class="pi-desc">'+esc(item.description||"")+'</div>';
      html+='<div class="pi-type">'+esc(evType)+'</div>';
      html+='</div>';
    });
    el.prebuiltList.innerHTML=html;

    document.querySelectorAll("[data-run-idx]").forEach(div=>{
      div.addEventListener("click",()=>{
        const idx=parseInt(div.getAttribute("data-run-idx"),10);
        selectPrebuilt(idx);
      });
    });
  }

  function selectPrebuilt(idx){
    if(idx<0||idx>=state.prebuiltLogs.length)return;
    state.selectedPrebuiltIdx=idx;
    const item=state.prebuiltLogs[idx];
    if(item&&item.payload){
      payloadToForm(item.payload);
      state.jsonEditorDirty=false;
      syncFormToEditor();
    }
    // highlight active
    document.querySelectorAll("[data-run-idx]").forEach((d,i)=>{
      d.classList.toggle("active",i===idx);
    });
  }

  /* ── Render steps ── */
  function renderSteps(steps){
    if(!Array.isArray(steps)||!steps.length){el.steps.innerHTML="";return}
    let h="";
    steps.forEach(s=>{
      const ok=Boolean(s&&s.ok);
      h+='<div class="step-item '+(ok?"ok":"fail")+'"><strong>'+esc(s.step||"step")+'</strong><span>'+(ok?"OK":"ISSUE")+'</span></div>';
    });
    el.steps.innerHTML=h;
  }

  function renderEventCard(result){
    const actuatorExecution = result && result.actuator_execution && typeof result.actuator_execution === "object"
      ? result.actuator_execution
      : ((result && result.latest_actuator_execution && typeof result.latest_actuator_execution === "object")
        ? result.latest_actuator_execution
        : null);
    const actuatorPayload = result && result.actuator_received_payload && typeof result.actuator_received_payload === "object"
      ? result.actuator_received_payload
      : ((actuatorExecution && actuatorExecution.actuator_received_payload && typeof actuatorExecution.actuator_received_payload === "object")
        ? actuatorExecution.actuator_received_payload
        : {});

    const payloadDetails = actuatorPayload && actuatorPayload.details && typeof actuatorPayload.details === "object"
      ? actuatorPayload.details
      : {};

    const steps=result&&Array.isArray(result.steps)?result.steps:[];
    const ps=steps.find(s=>s&&s.step==="processing")||{};

    const rows=[
      {l:"Demo",v:(result&&result.demo_id)||"n/a"},
      {l:"Processing",v:ps.summary||(ps.ok?"processed":"not processed")},
      {l:"Actuator Signal",v:actuatorPayload.signal_type||actuatorPayload.type||"n/a"},
      {l:"Actuator Service",v:actuatorPayload.service||actuatorPayload.service_name||"n/a"},
      {l:"Actuator Problem",v:actuatorPayload.error||actuatorPayload.problem||"n/a"},
      {l:"Payload Detail",v:Object.keys(payloadDetails).length?"available":"n/a"}
    ];
    if(actuatorExecution){
      rows.push(
        {l:"Actuator Action",v:actuatorExecution.action||"n/a"},
        {l:"Actuator Status",v:actuatorExecution.execution_status||"n/a"},
        {l:"Actuator Output",v:actuatorExecution.output||"n/a"},
        {l:"Executed At",v:actuatorExecution.executed_at||"n/a"}
      );
    }else{
      rows.push({l:"Actuator",v:"Waiting for downstream"});
    }
    let h="";rows.forEach(r=>{h+='<div class="event-row"><strong>'+esc(r.l)+':</strong> '+esc(r.v)+'</div>'});
    el.eventGrid.innerHTML=h;
    el.eventCard.className="event-card visible";
  }

  function renderResult(result){
    state.lastResult=result;
    const status=result&&result.status?result.status:"unknown";
    const demoId=result&&result.demo_id?result.demo_id:"n/a";
    const reason=result&&result.reason?result.reason:"";
    const message=result&&result.message?result.message:"";
    const actuatorExecution=result&&result.actuator_execution&&typeof result.actuator_execution==="object"
      ? result.actuator_execution
      : ((result&&result.latest_actuator_execution&&typeof result.latest_actuator_execution==="object")
        ? result.latest_actuator_execution
        : null);
    const action=actuatorExecution&&actuatorExecution.action?actuatorExecution.action:"pending";
    const actuatorPayload=result&&result.actuator_received_payload&&typeof result.actuator_received_payload==="object"
      ? result.actuator_received_payload
      : {};
    el.runSummary.className="run-summary visible";
    el.runSummary.textContent="Demo "+demoId+" — status: "+status+". Actuator action: "+action+(message?". "+message:"")+(reason?". Reason: "+reason:"");
    renderEventCard(result||{});
    renderSteps(result&&result.steps?result.steps:[]);
    el.jsonBox.textContent=JSON.stringify(actuatorPayload,null,2);
    el.jsonBox.classList.toggle("hidden",!state.showRawJson);
    el.toggleRawJson.textContent=state.showRawJson?"Hide Actuator Payload JSON":"Show Actuator Payload JSON";
  }

  /* ── Pipeline run ── */
  async function runPipeline(payload, sourceLabel){
    if(state.running)return;
    setRunning(true);
    setBanner("Running pipeline for "+sourceLabel+"...","warn");
    try{
      const result=await fetchJson(API.run,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      renderResult(result);
      state.lastSource=sourceLabel;
      const status=result&&result.status?result.status:"unknown";
      setBanner("Pipeline run finished — "+status+".",status==="completed"?"success":"info");
    }catch(error){
      const detail=error&&error.responsePayload&&error.responsePayload.detail;
      if(detail&&typeof detail==="object"){
        renderResult({
          demo_id:"n/a",
          status:"failed",
          reason:detail.message||error.message,
          failed_step:detail.failed_step||"unknown",
          actuator_execution:null,
          actuator_received_payload:{},
          steps:Array.isArray(detail.steps)?detail.steps:[],
          response_attempts:Array.isArray(detail.response_attempts)?detail.response_attempts:[]
        });
      }
      setBanner(detail&&detail.message?detail.message:error.message,"error");
    }finally{
      setRunning(false);
    }
  }

  /* ── Event wiring ── */
  // Form inputs -> sync to JSON editor
  el.form.querySelectorAll("input, select, textarea").forEach(inp=>{
    inp.addEventListener("input",()=>{state.jsonEditorDirty=false;syncFormToEditor()});
    inp.addEventListener("change",()=>{state.jsonEditorDirty=false;syncFormToEditor()});
  });

  // JSON editor direct edits
  el.jsonEditor.addEventListener("input",()=>{
    state.jsonEditorDirty=true;
    syncEditorToForm();
  });

  // Run custom
  el.runCustom.addEventListener("click",async()=>{
    const p=getCurrentPayload();
    if(!p){setBanner("Fix JSON errors first.","error");return}
    await runPipeline(p,"custom payload");
  });

  // Prevent form submit default
  el.form.addEventListener("submit",e=>{e.preventDefault();el.runCustom.click()});

  // Copy payload
  el.copyPayload.addEventListener("click",async()=>{
    const p=getCurrentPayload();
    if(!p){setBanner("JSON is invalid.","error");return}
    const text=JSON.stringify(p,null,2);
    const ok=await copyOrPrompt(text);
    setBanner(ok?"JSON copied to clipboard.":"Clipboard blocked.","success");
  });

  // Raw JSON toggle
  el.toggleRawJson.addEventListener("click",()=>{
    state.showRawJson=!state.showRawJson;
    el.jsonBox.classList.toggle("hidden",!state.showRawJson);
    el.toggleRawJson.textContent=state.showRawJson?"Hide Actuator Payload JSON":"Show Actuator Payload JSON";
  });

  /* ── Init ── */
  async function init(){
    setBanner("Loading...","info");
    el.statusText.textContent="Loading...";

    try{
      const data=await fetchJson(API.prebuilt);
      state.prebuiltLogs=Array.isArray(data.items)?data.items:[];
    }catch(e){
      state.prebuiltLogs=[];
    }
    renderPrebuiltList();

    // Select first prebuilt by default
    if(state.prebuiltLogs.length>0)selectPrebuilt(0);

    syncFormToEditor();
    el.statusText.textContent="Ready";
    setBanner("Dashboard ready. Select a prebuilt event or build a custom one.","success");
    setTimeout(()=>setBanner(null),3000);
  }

  init();
})();
</script>
</body>
</html>
"""
