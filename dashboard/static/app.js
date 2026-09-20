/* Shared utilities */
const $ = id => document.getElementById(id);
const setHtml = (id, html) => { const el = $(id); if (el) el.innerHTML = html; };
const setText = (id, text) => { const el = $(id); if (el) el.textContent = text; };

function riskBadge(risk) {
  return `<span class="badge badge-${risk}">${risk}</span>`;
}

function tcoTable(breakdown) {
  if (!breakdown) return '';
  const rows = [
    ['Token cost', breakdown.token_cost_usd],
    ['Human review (est.)', breakdown.review_cost_usd],
    ['Eval share', breakdown.eval_cost_usd],
    ['Incident cost', breakdown.incident_cost_usd],
    ['Total', breakdown.total_cost_usd],
  ];
  return `<table class="tco-table">
    <thead><tr><th>Category</th><th>Cost (USD)</th></tr></thead>
    <tbody>${rows.map(([l, v]) =>
      `<tr><td>${l}</td><td>$${Number(v).toFixed(5)}</td></tr>`
    ).join('')}</tbody>
  </table>`;
}
