let categoryChart, netChart;

function fmtCurrency(v) {
  return "₹" + Number(v).toLocaleString();
}

async function fetchTransactions() {
  const res = await fetch("/api/transactions");
  return res.json();
}

async function addTransaction(payload) {
  const res = await fetch("/api/transactions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

async function deleteTransaction(id) {
  const res = await fetch(`/api/transactions/${id}`, { method: "DELETE" });
  return res.json();
}

async function fetchInsights() {
  const res = await fetch("/api/insights");
  return res.json();
}

function renderTable(rows) {
  const tbody = document.querySelector("#tx-table tbody");
  tbody.innerHTML = "";
  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.date}</td>
      <td>${r.type}</td>
      <td>${r.category}</td>
      <td>${fmtCurrency(r.amount)}</td>
      <td>${r.note || ""}</td>
      <td><button class="del" data-id="${r.id}">Delete</button></td>
    `;
    tbody.appendChild(tr);
  });
  tbody.querySelectorAll("button.del").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      await deleteTransaction(id);
      await refresh();
    });
  });
}

function upsertChart(canvasId, type, labels, data, label) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const exists = (type === "pie") ? categoryChart : netChart;
  if (exists) exists.destroy();
  const chart = new Chart(ctx, {
    type,
    data: {
      labels,
      datasets: [{
        label,
        data,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
        tooltip: { enabled: true }
      },
      scales: type === "line" ? { y: { beginAtZero: true } } : undefined,
    },
  });
  if (type === "pie") categoryChart = chart;
  else netChart = chart;
}

function renderInsights(data) {
  const ul = document.getElementById("insights");
  ul.innerHTML = "";
  if (data.top_categories_this_month.length === 0) {
    ul.innerHTML += `<li>No data for this month yet. Add transactions to see insights.</li>`;
  } else {
    const topCats = data.top_categories_this_month.map(c => `${c.category}: ${fmtCurrency(c.total)}`).join(", ");
    ul.innerHTML += `<li>Top categories this month — ${topCats}.</li>`;
  }
  if (data.forecast_next_month_net !== null) {
    const sign = data.forecast_next_month_net >= 0 ? "surplus" : "deficit";
    ul.innerHTML += `<li>Projected next month net: ${fmtCurrency(data.forecast_next_month_net)} (${sign}).</li>`;
  }
  if (data.recommendations && data.recommendations.length) {
    data.recommendations.forEach(r => ul.innerHTML += `<li>${r}</li>`);
  }
  if (data.outliers && data.outliers.length) {
    const o = data.outliers[0];
    ul.innerHTML += `<li>Possible outlier in <b>${o.category}</b>: ${fmtCurrency(o.amount)} on ${o.date} (>${fmtCurrency(o.threshold)}).</li>`;
  }
}

async function refresh() {
  const [rows, ins] = await Promise.all([fetchTransactions(), fetchInsights()]);
  renderTable(rows);

  // category chart (this month)
  const now = new Date();
  const ym = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
  const byCat = {};
  rows.filter(r => r.type === "expense" && r.date.startsWith(ym))
      .forEach(r => byCat[r.category] = (byCat[r.category] || 0) + Number(r.amount));
  const labelsCat = Object.keys(byCat);
  const dataCat = Object.values(byCat);
  upsertChart("categoryChart", "pie", labelsCat, dataCat, "This Month");

  // net by month
  const byMonth = {};
  rows.forEach(r => {
    const m = r.date.slice(0, 7);
    byMonth[m] = byMonth[m] || 0;
    byMonth[m] += (r.type === "expense" ? 1 : -1) * Number(r.amount);
  });
  const labelsNet = Object.keys(byMonth).sort();
  const dataNet = labelsNet.map(m => byMonth[m]);
  upsertChart("netChart", "line", labelsNet, dataNet, "Net (Income - Expenses)");

  renderInsights(ins);
}

document.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("date").valueAsNumber = Date.now() - (new Date()).getTimezoneOffset() * 60000;
  document.getElementById("tx-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      date: document.getElementById("date").value,
      amount: document.getElementById("amount").value,
      type: document.getElementById("type").value,
      category: document.getElementById("category").value,
      note: document.getElementById("note").value,
    };
    const res = await addTransaction(payload);
    if (!res.ok) {
      alert("Error: " + (res.error || "unknown"));
      return;
    }
    e.target.reset();
    document.getElementById("date").valueAsNumber = Date.now() - (new Date()).getTimezoneOffset() * 60000;
    await refresh();
  });

  await refresh();
});
