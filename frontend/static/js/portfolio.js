/**
 * Portfolio module - Virtual portfolio management
 */

async function loadPortfolio() {
  const container = document.getElementById('portfolioContent');
  try {
    const res = await fetch('/api/portfolio');
    const data = await res.json();
    renderPortfolio(data);
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">💼</div><h3>Portfolio is empty</h3><p>Add stocks above to start tracking.</p></div>`;
  }
}

function renderPortfolio(data) {
  const container = document.getElementById('portfolioContent');
  const { holdings, total_invested, total_current_value, total_pnl, total_pnl_pct } = data;

  const pnlClass = total_pnl >= 0 ? 'green' : 'red';
  const pnlArrow = total_pnl >= 0 ? '▲' : '▼';

  let html = `
    <div class="portfolio-summary">
      <div class="metric-card">
        <div class="card-label">Total Invested</div>
        <div class="card-value blue">₹${formatNum(total_invested)}</div>
        <div class="card-sub">${holdings.length} Holdings</div>
      </div>
      <div class="metric-card">
        <div class="card-label">Current Value</div>
        <div class="card-value ${pnlClass}">₹${formatNum(total_current_value)}</div>
        <div class="card-sub">Live prices</div>
      </div>
      <div class="metric-card">
        <div class="card-label">Total P&L</div>
        <div class="card-value ${pnlClass}">${pnlArrow} ₹${formatNum(Math.abs(total_pnl))}</div>
        <div class="card-sub">${total_pnl_pct >= 0 ? '+' : ''}${total_pnl_pct.toFixed(2)}%</div>
      </div>
      <div class="metric-card">
        <div class="card-label">Holdings</div>
        <div class="card-value">${data.num_holdings}</div>
        <div class="card-sub">Stocks</div>
      </div>
    </div>`;

  if (holdings.length === 0) {
    html += `<div class="empty-state"><div class="empty-icon">💼</div><h3>No holdings yet</h3><p>Add stocks using the form above.</p></div>`;
  } else {
    html += `
    <div class="holdings-table">
      <div class="table-header">
        <div>Ticker</div>
        <div>Qty</div>
        <div>Buy Price</div>
        <div>Current</div>
        <div>Invested</div>
        <div>P&L</div>
        <div>Action</div>
      </div>`;

    for (const h of holdings) {
      const pnlCls = h.pnl >= 0 ? 'pos' : 'neg';
      const pnlSign = h.pnl >= 0 ? '+' : '';
      html += `
      <div class="table-row">
        <div class="t-ticker">${h.ticker.replace('.NS','').replace('.BO','')}</div>
        <div>${h.quantity}</div>
        <div>₹${h.purchase_price.toFixed(2)}</div>
        <div>₹${h.current_price.toFixed(2)}</div>
        <div>₹${formatNum(h.invested)}</div>
        <div class="t-pnl ${pnlCls}">${pnlSign}₹${formatNum(Math.abs(h.pnl))} (${pnlSign}${h.pnl_pct.toFixed(1)}%)</div>
        <div><button class="btn-remove" onclick="removeFromPortfolio('${h.ticker}')">Remove</button></div>
      </div>`;
    }
    html += '</div>';
  }

  container.innerHTML = html;
}

async function addToPortfolio() {
  const ticker = document.getElementById('portTicker').value.trim().toUpperCase();
  const qty = parseFloat(document.getElementById('portQty').value);
  const price = parseFloat(document.getElementById('portPrice').value);
  const date = document.getElementById('portDate').value;

  if (!ticker || isNaN(qty) || isNaN(price) || qty <= 0 || price <= 0) {
    showToast('Please fill all portfolio fields correctly', 'error');
    return;
  }

  try {
    const res = await fetch('/api/portfolio/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, quantity: qty, purchase_price: price, date }),
    });
    const data = await res.json();
    showToast(`✅ ${ticker} added to portfolio!`, 'success');
    loadPortfolio();
    // Clear inputs
    document.getElementById('portTicker').value = '';
    document.getElementById('portQty').value = '';
    document.getElementById('portPrice').value = '';
  } catch (e) {
    showToast('Failed to add stock', 'error');
  }
}

async function removeFromPortfolio(ticker) {
  try {
    await fetch(`/api/portfolio/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
    showToast(`Removed ${ticker.replace('.NS','')}`, 'info');
    loadPortfolio();
  } catch (e) {
    showToast('Failed to remove stock', 'error');
  }
}

function formatNum(n) {
  if (n >= 1e7) return (n / 1e7).toFixed(2) + 'Cr';
  if (n >= 1e5) return (n / 1e5).toFixed(2) + 'L';
  return n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function showToast(msg, type = 'info') {
  const existing = document.getElementById('toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'toast';
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:9999;
    padding:12px 20px; border-radius:8px; font-size:13px; font-weight:500;
    max-width:320px; animation:slideIn 0.3s ease;
    ${type === 'success' ? 'background:#065f46; color:#6ee7b7; border:1px solid #10b981;' :
      type === 'error' ? 'background:#7f1d1d; color:#fca5a5; border:1px solid #ef4444;' :
      'background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6;'}
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// Global exports for onclick attributes
window.addToPortfolio = addToPortfolio;
window.removeFromPortfolio = removeFromPortfolio;
window.loadPortfolio = loadPortfolio;
window.showToast = showToast;

