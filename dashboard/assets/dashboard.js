async function loadPayload() {
  const response = await fetch("../data/processed/dashboard_payload.json");
  if (!response.ok) throw new Error("Unable to load dashboard_payload.json");
  return response.json();
}

function fmt(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

function band(score) {
  if (score >= 60) return "red";
  if (score >= 30) return "amber";
  return "green";
}

function interpretation(score) {
  if (score <= 30) return "Thesis weakening / AI economics improving";
  if (score <= 60) return "Ambiguous";
  if (score <= 80) return "Thesis being validated";
  return "Severe stress / bubble-risk evidence strong";
}

function renderHeader(payload) {
  document.getElementById("asof").textContent = `As of ${payload.asof_date}`;
  document.getElementById("coverage").textContent = `Coverage ${fmt(payload.data_quality.data_coverage * 100)}%`;
  document.getElementById("confidence").textContent = `Average confidence ${fmt(payload.data_quality.average_confidence * 100)}%`;
  const score = payload.stress_index.ai_economic_stress_index;
  document.getElementById("stressScore").textContent = fmt(score);
  document.getElementById("stressInterpretation").textContent = interpretation(score);
}

function renderPillars(payload) {
  const el = document.getElementById("pillarCards");
  el.innerHTML = payload.pillar_scores.map(p => `
    <div class="pillar-card ${band(p.confidence_adjusted_score)}">
      <div class="label">${p.pillar.replaceAll("_", " ")}</div>
      <div class="score">${fmt(p.confidence_adjusted_score)}</div>
      <div class="interpretation">Coverage ${fmt(p.data_coverage * 100)}% · stale ${p.stale_metric_count}</div>
    </div>`).join("");
}

function renderHeatmap(payload) {
  const latest = new Map(payload.latest_metrics.map(m => [m.metric_id, m]));
  document.getElementById("heatmap").innerHTML = payload.metric_catalog.map(m => {
    const row = latest.get(m.metric_id);
    const klass = row ? band(row.confidence_adjusted_score) : "missing";
    const score = row ? fmt(row.confidence_adjusted_score) : "missing";
    const value = row ? `${fmt(row.value)} ${row.unit || m.unit}` : "No observation";
    return `<div class="tile ${klass}">
      <strong>${m.metric_name}</strong>
      <span>${m.pillar.replaceAll("_", " ")} · score ${score}</span>
      <span>${value} · confidence ${row ? row.confidence_grade : "--"}</span>
    </div>`;
  }).join("");
}

function table(id, columns, rows) {
  const head = `<thead><tr>${columns.map(c => `<th>${c.label}</th>`).join("")}</tr></thead>`;
  const body = `<tbody>${rows.map(r => `<tr>${columns.map(c => `<td>${c.format ? c.format(r[c.key], r) : (r[c.key] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody>`;
  document.getElementById(id).innerHTML = head + body;
}

function renderTables(payload) {
  table("metricTable", [
    {key:"pillar", label:"Pillar"},
    {key:"metric_name", label:"Metric"},
    {key:"entity", label:"Entity"},
    {key:"value", label:"Value", format:(v,r)=>`${fmt(v)} ${r.unit || ""}`},
    {key:"confidence_adjusted_score", label:"Score", format:v=>fmt(v)},
    {key:"confidence_grade", label:"Conf."},
    {key:"source_id", label:"Source"},
    {key:"notes", label:"Notes"}
  ], payload.latest_metrics);
  table("eventTable", [
    {key:"event_date", label:"Date"},
    {key:"entity", label:"Entity"},
    {key:"event_type", label:"Type"},
    {key:"thesis_impact", label:"Impact"},
    {key:"severity", label:"Severity"},
    {key:"confidence_grade", label:"Conf."},
    {key:"summary", label:"Summary"}
  ], payload.event_log);
  table("sourceTable", [
    {key:"source_id", label:"Source"},
    {key:"source_type", label:"Type"},
    {key:"entity", label:"Entity"},
    {key:"pillar", label:"Pillar"},
    {key:"confidence_grade", label:"Conf."},
    {key:"active", label:"Active"}
  ], payload.source_registry);
}

function renderWarnings(payload) {
  const rows = payload.warnings.length ? payload.warnings : [{type:"none", message:"No warnings."}];
  document.getElementById("warnings").innerHTML = rows.map(w => `<div class="warning"><strong>${w.type}</strong><br>${w.pillar || ""} ${w.metric_id || ""}<br>${w.message}</div>`).join("");
}

function renderIndicators(payload) {
  for (const [id, rows] of [["falsification", payload.falsification_indicators], ["validation", payload.validation_indicators]]) {
    document.getElementById(id).innerHTML = rows.map(r => `<div class="indicator ${r.triggered ? "triggered" : ""}">
      <strong>${r.triggered ? "Triggered" : "Not triggered"}: ${r.id.replaceAll("_", " ")}</strong><br>
      ${r.summary}<br>Latest ${fmt(r.latest_value)} vs ${r.condition} ${r.threshold}
    </div>`).join("");
  }
}

function drawChart(payload) {
  const canvas = document.getElementById("seriesChart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const metrics = payload.latest_metrics.slice(0, 12);
  const max = Math.max(100, ...metrics.map(m => Number(m.confidence_adjusted_score || 0)));
  const barW = canvas.width / Math.max(metrics.length, 1) - 8;
  metrics.forEach((m, i) => {
    const h = (Number(m.confidence_adjusted_score || 0) / max) * 210;
    const x = i * (barW + 8) + 8;
    const y = 240 - h;
    ctx.fillStyle = band(m.confidence_adjusted_score) === "red" ? "#b93a32" : band(m.confidence_adjusted_score) === "amber" ? "#c08222" : "#2f8f5b";
    ctx.fillRect(x, y, barW, h);
    ctx.fillStyle = "#172026";
    ctx.font = "11px sans-serif";
    ctx.fillText(m.metric_id.slice(0, 12), x, 260);
  });
}

loadPayload().then(payload => {
  renderHeader(payload);
  renderPillars(payload);
  renderHeatmap(payload);
  renderTables(payload);
  renderWarnings(payload);
  renderIndicators(payload);
  drawChart(payload);
}).catch(err => {
  document.body.innerHTML = `<main><section><h1>Dashboard load failed</h1><p>${err.message}</p></section></main>`;
});

