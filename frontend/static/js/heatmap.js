/**
 * Heatmap module - Sector heatmap visualization
 */

async function loadHeatmap() {
  const container = document.getElementById('heatmapContent');
  container.innerHTML = '<div class="loading-inline">Loading sector data...</div>';

  try {
    const res = await fetch('/api/heatmap');
    const data = await res.json();
    renderHeatmap(data.heatmap);
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">🗺️</div><h3>Could not load heatmap</h3><p>${e.message}</p></div>`;
  }
}

function renderHeatmap(sectorData) {
  const container = document.getElementById('heatmapContent');

  const legendHtml = `
    <div style="display:flex;gap:16px;align-items:center;margin-bottom:16px;font-size:12px;color:#94a3b8;">
      <div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:20px;border-radius:4px;background:#065f46;"></div> Strong Gain (&gt;2%)</div>
      <div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:20px;border-radius:4px;background:#10b981;"></div> Gain (0-2%)</div>
      <div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:20px;border-radius:4px;background:#374151;"></div> Flat</div>
      <div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:20px;border-radius:4px;background:#ef4444;"></div> Loss (0-2%)</div>
      <div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:20px;border-radius:4px;background:#7f1d1d;"></div> Strong Loss (&lt;-2%)</div>
    </div>`;

  let html = legendHtml + '<div class="heatmap-grid">';

  for (const [sector, stocks] of Object.entries(sectorData)) {
    if (!stocks || stocks.length === 0) continue;

    // Calculate sector average change
    const avgChange = stocks.reduce((sum, s) => sum + s.change_pct, 0) / stocks.length;

    html += `
      <div class="sector-block">
        <div class="sector-header">
          ${getSectorIcon(sector)} ${sector}
          <span style="float:right;font-size:12px;font-weight:500;color:${avgChange >= 0 ? '#10b981' : '#ef4444'}">${avgChange >= 0 ? '+' : ''}${avgChange.toFixed(2)}%</span>
        </div>
        <div class="sector-stocks">`;

    for (const stock of stocks) {
      const pct = stock.change_pct;
      const bgColor = getHeatmapColor(pct);
      const textColor = Math.abs(pct) > 1 ? '#ffffff' : '#e2e8f0';

      html += `
        <div class="heatmap-cell" style="background:${bgColor};" onclick="quickSelect('${stock.ticker}')">
          <div class="hm-ticker" style="color:${textColor}">${stock.ticker}</div>
          <div class="hm-pct" style="color:${textColor}">${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%</div>
        </div>`;
    }

    html += `</div></div>`;
  }

  html += '</div>';
  container.innerHTML = html;
}

function getHeatmapColor(pct) {
  if (pct > 3) return '#065f46';
  if (pct > 2) return '#047857';
  if (pct > 1) return '#059669';
  if (pct > 0) return '#10b981';
  if (pct > -1) return '#b91c1c';
  if (pct > -2) return '#dc2626';
  if (pct > -3) return '#ef4444';
  return '#7f1d1d';
}

function getSectorIcon(sector) {
  const icons = {
    Banking: '🏦', IT: '💻', Energy: '⚡', Pharma: '💊',
    Automobile: '🚗', FMCG: '🛒', Finance: '💰', Metals: '⚙️',
  };
  return icons[sector] || '📊';
}

// Global exports
window.loadHeatmap = loadHeatmap;

