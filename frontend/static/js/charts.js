/**
 * Charts module - Candlestick, Prediction, Technical charts using Chart.js
 * and Lightweight Charts (TradingView-like)
 */

// NOTE: API constant is defined in main.js - do not re-declare here
let candlestickInstance = null;
let predChart = null;
let rsiChart = null;
let volChart = null;
let backtestChart = null;

// ─── Lightweight Charts Candlestick ───────────────────────
function renderCandlestick(ticker, period = '1y') {
  const container = document.getElementById('candlestickChart');
  if (!container) return;

  // Clear previous
  container.innerHTML = '';

  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: 350,
    layout: {
      background: { color: '#141c2e' },
      textColor: '#94a3b8',
    },
    grid: {
      vertLines: { color: 'rgba(255,255,255,0.04)' },
      horzLines: { color: 'rgba(255,255,255,0.04)' },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
    },
    rightPriceScale: {
      borderColor: 'rgba(255,255,255,0.1)',
    },
    timeScale: {
      borderColor: 'rgba(255,255,255,0.1)',
      timeVisible: true,
    },
  });

  candlestickInstance = chart;

  const candleSeries = chart.addCandlestickSeries({
    upColor: '#10b981',
    downColor: '#ef4444',
    borderDownColor: '#ef4444',
    borderUpColor: '#10b981',
    wickDownColor: '#ef4444',
    wickUpColor: '#10b981',
  });

  const volumeSeries = chart.addHistogramSeries({
    color: '#3b82f6',
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
    scaleMargins: { top: 0.8, bottom: 0 },
  });

  // Add SMA lines
  const sma20Series = chart.addLineSeries({
    color: '#f59e0b',
    lineWidth: 1,
    title: 'SMA 20',
  });
  const sma50Series = chart.addLineSeries({
    color: '#8b5cf6',
    lineWidth: 1,
    title: 'SMA 50',
  });

  // Fetch OHLCV data
  fetch(`${API}/ohlcv/${ticker}?period=${period}`)
    .then(r => r.json())
    .then(d => {
      const ohlcv = d.data || [];

        const validDate = typeof r.date === 'string' && r.date.includes('T') ? r.date.split('T')[0] : r.date;
        const candles = ohlcv.map(r => {
          const dt = typeof r.date === 'string' && r.date.includes('T') ? r.date.split('T')[0] : r.date;
          return {
            time: dt,
            open: r.open,
            high: r.high,
            low: r.low,
            close: r.close,
          };
        });

      const volumes = ohlcv.map(r => {
        const dt = typeof r.date === 'string' && r.date.includes('T') ? r.date.split('T')[0] : r.date;
        return {
          time: dt,
          value: r.volume,
          color: r.close >= r.open ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
        };
      });

      // Compute SMA 20 & 50
      const closes = ohlcv.map(r => r.close);
      const sma20 = computeSMA(closes, 20).map((v, i) => {
        const dt = typeof ohlcv[i].date === 'string' && ohlcv[i].date.includes('T') ? ohlcv[i].date.split('T')[0] : ohlcv[i].date;
        return { time: dt, value: v };
      }).filter(x => x.value !== null);
      
      const sma50 = computeSMA(closes, 50).map((v, i) => {
        const dt = typeof ohlcv[i].date === 'string' && ohlcv[i].date.includes('T') ? ohlcv[i].date.split('T')[0] : ohlcv[i].date;
        return { time: dt, value: v };
      }).filter(x => x.value !== null);

      candleSeries.setData(candles);
      volumeSeries.setData(volumes);
      sma20Series.setData(sma20);
      sma50Series.setData(sma50);

      chart.timeScale().fitContent();
    })
    .catch(err => {
      container.innerHTML = `<div style="padding:40px;text-align:center;color:#64748b">Could not load chart data</div>`;
    });

  // Resize handler
  window.addEventListener('resize', () => {
    chart.applyOptions({ width: container.clientWidth });
  });
}

function computeSMA(closes, period) {
  return closes.map((_, i) => {
    if (i < period - 1) return null;
    const slice = closes.slice(i - period + 1, i + 1);
    return slice.reduce((a, b) => a + b, 0) / period;
  });
}

// ─── Prediction Chart (Actual vs Predicted) ───────────────
function renderPredictionChart(chartData) {
  const canvas = document.getElementById('predChart');
  if (!canvas) return;

  if (predChart) predChart.destroy();

  predChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: chartData.dates,
      datasets: [
        {
          label: 'Actual Price',
          data: chartData.actual,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,0.1)',
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          tension: 0.3,
        },
        {
          label: 'LSTM Predicted',
          data: chartData.predicted,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16,185,129,0.05)',
          borderWidth: 2,
          borderDash: [5, 3],
          pointRadius: 0,
          fill: false,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#94a3b8', boxWidth: 12 },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 2})}`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: '#475569', maxTicksLimit: 8 },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
        y: {
          ticks: {
            color: '#94a3b8',
            callback: v => '₹' + v.toLocaleString('en-IN'),
          },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
      },
      interaction: { mode: 'index', intersect: false },
    },
  });
}

// ─── RSI Chart ────────────────────────────────────────────
function renderRSIGauge(rsiValue) {
  const canvas = document.getElementById('rsiChart');
  if (!canvas) return;
  if (rsiChart) rsiChart.destroy();

  const color = rsiValue < 30 ? '#10b981' : rsiValue > 70 ? '#ef4444' : '#f59e0b';

  rsiChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [rsiValue, 100 - rsiValue],
        backgroundColor: [color, 'rgba(255,255,255,0.05)'],
        borderWidth: 0,
      }],
    },
    options: {
      cutout: '75%',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
      },
    },
    plugins: [{
      id: 'centerText',
      beforeDraw(chart) {
        const { ctx, width, height } = chart;
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = color;
        ctx.font = 'bold 20px Inter, sans-serif';
        ctx.fillText(rsiValue.toFixed(1), width / 2, height / 2 - 8);
        ctx.fillStyle = '#64748b';
        ctx.font = '11px Inter, sans-serif';
        ctx.fillText('RSI', width / 2, height / 2 + 12);
        ctx.restore();
      },
    }],
  });
}

// ─── MACD Chart ───────────────────────────────────────────
function renderMACDChart(macdVal, signalVal, histVal) {
  const canvas = document.getElementById('macdDisplayChart');
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: ['MACD', 'Signal', 'Histogram'],
      datasets: [{
        data: [macdVal, signalVal, histVal],
        backgroundColor: [
          'rgba(59,130,246,0.6)',
          'rgba(245,158,11,0.6)',
          histVal >= 0 ? 'rgba(16,185,129,0.6)' : 'rgba(239,68,68,0.6)',
        ],
        borderColor: [
          '#3b82f6', '#f59e0b',
          histVal >= 0 ? '#10b981' : '#ef4444',
        ],
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.04)' } },
      },
    },
  });
}

// ─── Backtest Portfolio Value Chart ───────────────────────
function renderBacktestChart(strategies) {
  const canvas = document.getElementById('backtestChart');
  if (!canvas) return;
  if (backtestChart) backtestChart.destroy();

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
  const datasets = Object.entries(strategies).map(([name, data], i) => ({
    label: name,
    data: data.portfolio_values || [],
    borderColor: colors[i % colors.length],
    backgroundColor: `${colors[i % colors.length]}20`,
    borderWidth: 2,
    pointRadius: 0,
    fill: i === 0,
    tension: 0.3,
  }));

  backtestChart = new Chart(canvas, {
    type: 'line',
    data: { labels: datasets[0]?.data.map((_, i) => `Day ${i + 1}`) || [], datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8', boxWidth: 12 } },
        tooltip: {
          mode: 'index', intersect: false,
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 0})}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: '#475569', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: {
          ticks: { color: '#94a3b8', callback: v => '₹' + (v/1000).toFixed(0) + 'K' },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
      },
    },
  });
}
