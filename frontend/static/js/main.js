/**
 * StockAI Pro - Main Application Orchestrator
 * Coordinates all sections, API calls, and UI rendering
 */

const API = '/api';
let currentTicker = '';
let currentPeriod = '1y';
let predictionData = null;
let riskGlobalData = null;

// ══════════════════════════════════════════════════════════
// SECTION NAVIGATION
// ══════════════════════════════════════════════════════════

function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const target = document.getElementById(`section-${name}`);
  if (target) target.classList.add('active');
  const navItem = document.querySelector(`[data-section="${name}"]`);
  if (navItem) navItem.classList.add('active');

  // Lazy load heatmap and portfolio when visited
  if (name === 'heatmap') loadHeatmap();
  if (name === 'portfolio') loadPortfolio();
}

// ══════════════════════════════════════════════════════════
// QUICK STOCK SELECT
// ══════════════════════════════════════════════════════════

function quickSelect(ticker) {
  document.getElementById('stockSearch').value = ticker;
  analyzeStock();
}

// ══════════════════════════════════════════════════════════
// STOCK SEARCH AUTOCOMPLETE
// ══════════════════════════════════════════════════════════

const searchInput = document.getElementById('stockSearch');
const suggestionsBox = document.getElementById('suggestions');

searchInput.addEventListener('input', debounce(async () => {
  const q = searchInput.value.trim();
  if (q.length < 1) { hideSuggestions(); return; }

  try {
    const res = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderSuggestions(data.results || []);
  } catch { hideSuggestions(); }
}, 250));

searchInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { hideSuggestions(); analyzeStock(); }
  if (e.key === 'Escape') hideSuggestions();
});

document.addEventListener('click', e => {
  if (!e.target.closest('.search-section')) hideSuggestions();
});

function renderSuggestions(results) {
  if (!results.length) { hideSuggestions(); return; }
  suggestionsBox.style.display = 'block';
  suggestionsBox.innerHTML = results.map(r => `
    <div class="suggestion-item" onclick="selectSuggestion('${r.symbol.replace('.NS','').replace('.BO','')}')">
      <span class="sug-symbol">${r.symbol.replace('.NS','').replace('.BO','')}</span>
      <span class="sug-name">${r.name}</span>
      <span class="sug-sector">${r.sector}</span>
    </div>`).join('');
}

function selectSuggestion(symbol) {
  searchInput.value = symbol;
  hideSuggestions();
  analyzeStock();
}

function hideSuggestions() {
  suggestionsBox.style.display = 'none';
}

function debounce(fn, delay) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ══════════════════════════════════════════════════════════
// GLOBAL DATA CACHE - shared across all sections
// ══════════════════════════════════════════════════════════
const _cache = {};   // { ticker: { stock, rec, pred, tech, sent, risk } }
let _loadingTicker = '';

function getCached(ticker) {
  return _cache[ticker] || null;
}

// ══════════════════════════════════════════════════════════
// MAIN ANALYSIS FUNCTION - fires ALL APIs in parallel
// ══════════════════════════════════════════════════════════

async function analyzeStock() {
  const ticker = searchInput.value.trim().toUpperCase().replace('.NS','').replace('.BO','');
  if (!ticker) { showToast('Please enter a stock symbol', 'error'); return; }

  currentTicker = ticker;
  hideSuggestions();

  // If already fully cached, just render immediately
  const cached = getCached(ticker);
  if (cached && cached._complete) {
    renderAllSections(ticker, cached);
    setLoading(false);
    return;
  }

  // Show loading state in all sections immediately
  setLoading(true, `Analyzing ${ticker}...`);
  showSectionSpinners(ticker);

  try {
    // Fire ALL 6 API calls simultaneously - no waiting for each other
    const [stockRes, recRes, predRes, techRes, sentRes, riskRes] = await Promise.allSettled([
      fetch(`${API}/stock/${ticker}`).then(r => r.json()),
      fetch(`${API}/recommendation/${ticker}`).then(r => r.json()),
      fetch(`${API}/predict/${ticker}`).then(r => r.json()),
      fetch(`${API}/technical/${ticker}`).then(r => r.json()),
      fetch(`${API}/sentiment/${ticker}`).then(r => r.json()),
      fetch(`${API}/risk/${ticker}`).then(r => r.json()),
    ]);

    const getData = (res) => res.status === 'fulfilled' ? res.value : {};

    const data = {
      stock: getData(stockRes),
      rec:   getData(recRes),
      pred:  getData(predRes),
      tech:  getData(techRes),
      sent:  getData(sentRes),
      risk:  getData(riskRes),
      _complete: true,
    };

    // Cache it
    _cache[ticker] = data;
    predictionData = data.rec;
    riskGlobalData = data.risk;

    // Render ALL sections at once
    renderAllSections(ticker, data);

    setLoading(false);

  } catch (err) {
    setLoading(false);
    showToast(`Error: ${err.message}`, 'error');
  }
}

// ══════════════════════════════════════════════════════════
// SHOW LOADING SPINNERS IN ALL SECTIONS IMMEDIATELY
// ══════════════════════════════════════════════════════════

function showSectionSpinners(ticker) {
  const spinner = `<div class="section-loading"><div class="spinner-ring"></div><div style="color:#64748b;font-size:13px;margin-top:12px">Fetching ${ticker} data...<br><span style="font-size:11px">Running LSTM Model &middot; Calculating Indicators</span></div></div>`;
  const ids = ['predictionContent','technicalContent','sentimentContent','riskContent'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = spinner;
  });
  // Show empty header placeholders
  document.getElementById('emptyDashboard')?.classList.add('hidden');
  document.getElementById('stockHeaderCard')?.classList.remove('hidden');
  document.getElementById('recommendationBanner')?.classList.remove('hidden');
}

// ══════════════════════════════════════════════════════════
// RENDER ALL SECTIONS FROM CACHED DATA
// ══════════════════════════════════════════════════════════

function renderAllSections(ticker, data) {
  // 1. Dashboard
  if (data.stock && data.stock.current_price !== undefined) {
    renderStockHeader(data.stock);
    document.getElementById('emptyDashboard')?.classList.add('hidden');
    document.getElementById('stockHeaderCard')?.classList.remove('hidden');
    document.getElementById('recommendationBanner')?.classList.remove('hidden');
  }

  // 2. Recommendation banner
  if (data.rec && data.rec.recommendation) {
    updateRecommendationBanner(data.rec);
  }

  // 3. Candlestick chart
  renderCandlestick(ticker, currentPeriod);

  // 4. Prediction section
  loadPredictionSection(ticker, data.rec, data.pred);

  // 5. Technical section
  loadTechnicalSection(ticker, data.tech);

  // 6. Sentiment section
  loadSentimentSection(ticker, data.sent);

  // 7. Risk section
  loadRiskSection(ticker, data.risk);
}


// ══════════════════════════════════════════════════════════
// STOCK HEADER
// ══════════════════════════════════════════════════════════

function renderStockHeader(info) {
  setText('hdrTicker', info.ticker?.replace('.NS','').replace('.BO','') || '--');
  setText('hdrName', info.name || '--');
  setText('hdrSector', info.sector || 'NSE');
  setText('hdrExchange', info.exchange || 'NSE');

  const price = info.current_price || 0;
  const prevClose = info.previous_close || 0;
  const change = info.change || 0;
  const changePct = info.change_pct || 0;

  setText('hdrPrice', `₹${fmtPrice(price)}`);
  const changeEl = document.getElementById('hdrChange');
  changeEl.textContent = `${changePct >= 0 ? '▲' : '▼'} ${Math.abs(changePct).toFixed(2)}%  (${changePct >= 0 ? '+' : ''}₹${Math.abs(change).toFixed(2)})`;
  changeEl.className = `price-change-display ${changePct >= 0 ? 'up' : 'down'}`;

  setText('hdrOpen', `₹${fmtPrice(info.open_price)}`);
  setText('hdrHigh', `₹${fmtPrice(info.day_high)}`);
  setText('hdrLow', `₹${fmtPrice(info.day_low)}`);
  setText('hdrVolume', fmtVol(info.volume));
  setText('hdr52H', `₹${fmtPrice(info.week52_high)}`);
  setText('hdr52L', `₹${fmtPrice(info.week52_low)}`);
  setText('hdrPE', info.pe_ratio > 0 ? info.pe_ratio.toFixed(2) : 'N/A');
  setText('hdrMarketCap', fmtMarketCap(info.market_cap));
}

// ══════════════════════════════════════════════════════════
// RECOMMENDATION BANNER
// ══════════════════════════════════════════════════════════

function updateRecommendationBanner(recData) {
  const rec = recData.recommendation || {};
  const signal = rec.recommendation || 'HOLD';
  const conf = rec.confidence || 0;
  const reasons = rec.reasons || [];

  const sigEl = document.getElementById('recSignal');
  sigEl.textContent = signal;
  sigEl.className = 'rec-signal ' + (
    signal.includes('BUY') ? 'buy' :
    signal.includes('SELL') ? 'sell' : 'hold'
  );
  sigEl.style.background = rec.color ? rec.color + '20' : '';
  sigEl.style.color = rec.color || '';
  sigEl.style.borderColor = rec.color ? rec.color + '50' : '';

  setText('recConfidence', conf.toFixed(0));

  const reasonsEl = document.getElementById('recReasons');
  reasonsEl.innerHTML = reasons.map(r => `<span class="rec-reason-tag">${r}</span>`).join('');
}

// ══════════════════════════════════════════════════════════
// PREDICTION SECTION
// ══════════════════════════════════════════════════════════

async function loadPredictionSection(ticker, recData, fullPredData) {
  const container = document.getElementById('predictionContent');

  try {
    // Use pre-fetched data if provided, otherwise fetch
    const fullPred = fullPredData && fullPredData.current_price
      ? fullPredData
      : await fetch(`${API}/predict/${ticker}`).then(r => r.json());

    const cp = fullPred.current_price || 0;
    const nd = fullPred.next_day_price || 0;
    const nw = fullPred.next_week_trend || 0;
    const nm = fullPred.next_month_trend || 0;
    const pct = fullPred.price_change_pct || 0;

    container.innerHTML = `
      <div class="prediction-metrics">
        <div class="prediction-card">
          <div class="pred-label">Current Price</div>
          <div class="pred-value blue">₹${fmtPrice(cp)}</div>
          <div class="pred-change" style="color:#94a3b8">Live price</div>
        </div>
        <div class="prediction-card">
          <div class="pred-label">🎯 Next Day Prediction</div>
          <div class="pred-value ${pct >= 0 ? 'green' : 'red'}">₹${fmtPrice(nd)}</div>
          <div class="pred-change ${pct >= 0 ? 'up' : 'down'}">${pct >= 0 ? '▲' : '▼'} ${Math.abs(pct).toFixed(2)}%</div>
        </div>
        <div class="prediction-card">
          <div class="pred-label">📅 Next Week Trend</div>
          <div class="pred-value ${nw >= cp ? 'green' : 'red'}">₹${fmtPrice(nw)}</div>
          <div class="pred-change ${nw >= cp ? 'up' : 'down'}">${nw >= cp ? '▲' : '▼'} ${Math.abs((nw-cp)/cp*100).toFixed(2)}%</div>
        </div>
      </div>

      <div class="cards-grid">
        <div class="metric-card">
          <div class="card-label">Next Month Trend</div>
          <div class="card-value ${nm >= cp ? 'green' : 'red'}">₹${fmtPrice(nm)}</div>
          <div class="card-sub">${nm >= cp ? '▲' : '▼'} ${Math.abs((nm-cp)/cp*100).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Model Used</div>
          <div class="card-value" style="font-size:16px">${fullPred.model_used || 'LSTM'}</div>
          <div class="card-sub">Neural Network</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Confidence</div>
          <div class="card-value ${fullPred.confidence_score > 70 ? 'green' : fullPred.confidence_score > 40 ? 'yellow' : 'red'}">${(fullPred.confidence_score||0).toFixed(0)}%</div>
          <div class="card-sub">Model confidence</div>
        </div>
        <div class="metric-card">
          <div class="card-label">RMSE Error</div>
          <div class="card-value">₹${(fullPred.rmse||0).toFixed(2)}</div>
          <div class="card-sub">Root Mean Squared</div>
        </div>
        <div class="metric-card">
          <div class="card-label">MAE Error</div>
          <div class="card-value">₹${(fullPred.mae||0).toFixed(2)}</div>
          <div class="card-sub">Mean Absolute</div>
        </div>
        <div class="metric-card">
          <div class="card-label">MAPE</div>
          <div class="card-value">${(fullPred.mape||0).toFixed(2)}%</div>
          <div class="card-sub">Mean Abs % Error</div>
        </div>
      </div>

      <!-- Actual vs Predicted Chart -->
      <div class="chart-card">
        <div class="chart-header"><h3>📈 Actual vs LSTM Predicted Price</h3></div>
        <div style="height:260px"><canvas id="predChart"></canvas></div>
      </div>

      <!-- Explainability -->
      <div class="chart-card">
        <div class="chart-header"><h3>🔍 Model Explainability - What Drove This Prediction?</h3></div>
        <div id="explainSection">${renderExplainability(fullPred)}</div>
      </div>`;

    // Render actual vs predicted chart
    if (fullPred.chart_actual && fullPred.chart_predicted) {
      setTimeout(() => {
        renderPredictionChart({
          actual: fullPred.chart_actual,
          predicted: fullPred.chart_predicted,
          dates: fullPred.chart_dates || [],
        });
      }, 100);
    }

  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Prediction failed</h3><p>${e.message}</p></div>`;
  }
}

function renderExplainability(fullPred) {
  const ta = fullPred.technical_analysis || {};
  const sigs = ta.signals || {};
  const sent = fullPred.sentiment_data || {};
  const pct = fullPred.price_change_pct || 0;

  const factors = [];
  if (Math.abs(pct) > 2) factors.push({ label: 'Price momentum is ' + (pct > 0 ? 'bullish' : 'bearish'), icon: pct > 0 ? '▲' : '▼', color: pct > 0 ? '#10b981' : '#ef4444' });
  if (sigs.RSI?.signal === 'BUY') factors.push({ label: `RSI = ${sigs.RSI?.value} (Oversold - Buy signal)`, icon: '📉', color: '#10b981' });
  if (sigs.RSI?.signal === 'SELL') factors.push({ label: `RSI = ${sigs.RSI?.value} (Overbought - Sell signal)`, icon: '📈', color: '#ef4444' });
  if (sigs.MACD?.signal === 'BUY') factors.push({ label: 'MACD bullish crossover', icon: '✅', color: '#10b981' });
  if (sigs.MACD?.signal === 'SELL') factors.push({ label: 'MACD bearish crossover', icon: '❌', color: '#ef4444' });
  if (sent.sentiment_score > 0.15) factors.push({ label: `Positive news sentiment (${sent.sentiment_label})`, icon: '📰', color: '#10b981' });
  if (sent.sentiment_score < -0.15) factors.push({ label: `Negative news sentiment (${sent.sentiment_label})`, icon: '📰', color: '#ef4444' });
  if (sigs.Moving_Average?.signal === 'BUY') factors.push({ label: 'Price above key moving averages', icon: '📊', color: '#10b981' });
  if (sigs.MA_Cross?.signal === 'BUY') factors.push({ label: 'Golden Cross signal (SMA50 > SMA200)', icon: '⭐', color: '#f59e0b' });

  if (factors.length === 0) factors.push({ label: 'Mixed signals - model is uncertain', icon: '⚖️', color: '#94a3b8' });

  return `<div style="display:flex;flex-direction:column;gap:10px;padding:4px 0">
    ${factors.map(f => `
      <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid rgba(255,255,255,0.05)">
        <span style="font-size:18px">${f.icon}</span>
        <span style="font-size:13px;color:${f.color}">${f.label}</span>
      </div>`).join('')}
  </div>`;
}

// ══════════════════════════════════════════════════════════
// TECHNICAL ANALYSIS SECTION
// ══════════════════════════════════════════════════════════

async function loadTechnicalSection(ticker, techData) {
  const container = document.getElementById('technicalContent');
  try {
    // Use pre-fetched data or fetch
    const data = techData && techData.technical_analysis
      ? techData
      : await fetch(`${API}/technical/${ticker}`).then(r => r.json());
    const ta = data.technical_analysis || {};
    const fib = data.fibonacci || {};
    const sigs = ta.signals || {};
    const iv = ta.indicator_values || {};
    const overall = ta.overall_signal || 'HOLD';

    const overallColor = overall.includes('BUY') ? '#10b981' : overall.includes('SELL') ? '#ef4444' : '#f59e0b';

    container.innerHTML = `
      <div class="ta-overview">
        <div class="ta-signal-card">
          <div style="font-size:14px;color:#94a3b8">Overall Signal</div>
          <div class="ta-signal-big" style="color:${overallColor}">${overall}</div>
          <div class="ta-signal-score">Score: ${(ta.signal_score||0).toFixed(3)}</div>
          <div style="margin-top:16px;display:flex;flex-direction:column;gap:8px;width:100%">
            ${renderCompactIndicators(iv)}
          </div>
        </div>
        <div class="ta-indicators">
          <h4>Technical Signals Breakdown</h4>
          <div class="indicator-rows">
            ${Object.entries(sigs).map(([name, sig]) => `
              <div class="indicator-row">
                <div class="ind-name">${name.replace(/_/g,' ')}</div>
                <div class="ind-value">${formatSigValue(sig.value)}</div>
                <div class="ind-reason">${sig.reason || ''}</div>
                <div class="signal-pill ${getSigClass(sig.signal)}">${sig.signal}</div>
              </div>`).join('')}
          </div>
        </div>
      </div>

      <!-- Charts: RSI + MACD -->
      <div class="charts-row">
        <div class="chart-panel">
          <h4>RSI Gauge</h4>
          <div style="height:200px"><canvas id="rsiChart"></canvas></div>
          <div style="text-align:center;margin-top:8px;font-size:12px;color:#64748b">
            Oversold &lt;30 | Neutral 30-70 | Overbought &gt;70
          </div>
        </div>
        <div class="chart-panel">
          <h4>MACD</h4>
          <div style="height:200px"><canvas id="macdDisplayChart"></canvas></div>
        </div>
      </div>

      <!-- Fibonacci Retracement -->
      <div class="fib-card">
        <h4>📐 Fibonacci Retracement Levels</h4>
        <div class="fib-levels">
          ${renderFibLevels(fib)}
        </div>
      </div>`;

    // Render charts
    setTimeout(() => {
      renderRSIGauge(iv.RSI || 50);
      renderMACDChart(iv.MACD || 0, 0, 0);
    }, 100);

  } catch (e) {
    container.innerHTML = `<div class="empty-state"><h3>Technical analysis failed</h3><p>${e.message}</p></div>`;
  }
}

function renderCompactIndicators(iv) {
  const items = [
    ['RSI', iv.RSI, ''],
    ['SMA 20', iv.SMA_20, '₹'],
    ['SMA 50', iv.SMA_50, '₹'],
    ['EMA 12', iv.EMA_12, '₹'],
    ['ATR', iv.ATR, '₹'],
  ];
  return items.map(([n, v, pfx]) => `
    <div style="display:flex;justify-content:space-between;font-size:12px">
      <span style="color:#64748b">${n}</span>
      <span style="font-weight:600">${pfx}${(v||0).toFixed(2)}</span>
    </div>`).join('');
}

function renderFibLevels(fib) {
  const high = fib.level_0 || 0;
  const low = fib.level_100 || 0;
  const range = high - low;
  const levels = [
    ['0%', fib.level_0],
    ['23.6%', fib.level_236],
    ['38.2%', fib.level_382],
    ['50%', fib.level_500],
    ['61.8%', fib.level_618],
    ['100%', fib.level_100],
  ];
  return levels.map(([pct, price]) => {
    const fillPct = range > 0 ? Math.max(0, Math.min(100, (price - low) / range * 100)) : 50;
    return `
      <div class="fib-level">
        <div class="fib-pct">${pct}</div>
        <div class="fib-bar"><div class="fib-fill" style="width:${fillPct}%"></div></div>
        <div class="fib-price">₹${fmtPrice(price)}</div>
      </div>`;
  }).join('');
}

function getSigClass(signal) {
  if (!signal) return 'normal';
  const s = signal.toLowerCase();
  if (s.includes('buy')) return 'buy';
  if (s.includes('sell')) return 'sell';
  if (s === 'strong') return 'strong';
  if (s === 'normal') return 'normal';
  return 'hold';
}

function formatSigValue(v) {
  if (v === undefined || v === null) return '--';
  return typeof v === 'number' ? (v > 10 ? v.toFixed(2) : v.toFixed(4)) : String(v);
}

// ══════════════════════════════════════════════════════════
// SENTIMENT SECTION
// ══════════════════════════════════════════════════════════

async function loadSentimentSection(ticker, sentData) {
  const container = document.getElementById('sentimentContent');
  try {
    // Use pre-fetched data or fetch
    const data = sentData && sentData.overall_sentiment
      ? sentData
      : await fetch(`${API}/sentiment/${ticker}`).then(r => r.json());
    const overall = data.overall_sentiment || {};
    const articles = data.articles || [];

    const score = overall.sentiment_score || 0;
    const label = overall.sentiment_label || 'Neutral';
    const scoreColor = score > 0.1 ? '#10b981' : score < -0.1 ? '#ef4444' : '#f59e0b';

    container.innerHTML = `
      <div class="sentiment-overview">
        <div class="sentiment-meter">
          <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Sentiment Score</div>
          <div class="sentiment-score-big" style="color:${scoreColor}">${score >= 0 ? '+' : ''}${(score * 100).toFixed(0)}</div>
          <div class="sentiment-label-big" style="color:${scoreColor}">${label}</div>
          <div style="font-size:12px;color:#64748b;margin-top:4px">${overall.articles_analyzed || 0} articles analyzed</div>
          <div class="sentiment-bars">
            <div class="sentiment-bar-row">
              <div class="s-label">Positive</div>
              <div class="s-bar"><div class="s-fill positive" style="width:${(overall.positive||0)*100}%"></div></div>
              <div class="s-pct">${((overall.positive||0)*100).toFixed(0)}%</div>
            </div>
            <div class="sentiment-bar-row">
              <div class="s-label">Neutral</div>
              <div class="s-bar"><div class="s-fill neutral" style="width:${(overall.neutral||0)*100}%"></div></div>
              <div class="s-pct">${((overall.neutral||0)*100).toFixed(0)}%</div>
            </div>
            <div class="sentiment-bar-row">
              <div class="s-label">Negative</div>
              <div class="s-bar"><div class="s-fill negative" style="width:${(overall.negative||0)*100}%"></div></div>
              <div class="s-pct">${((overall.negative||0)*100).toFixed(0)}%</div>
            </div>
          </div>
        </div>
        <div class="news-list">
          ${articles.map(a => {
            const s = a.sentiment || 0;
            const sColor = s > 0.1 ? '#10b981' : s < -0.1 ? '#ef4444' : '#f59e0b';
            const sLabel = s > 0.1 ? 'pos' : s < -0.1 ? 'neg' : 'neu';
            return `
              <div class="news-item">
                <div class="news-sentiment" style="background:${sColor}"></div>
                <div style="flex:1">
                  <div class="news-sentence">${a.title || ''}</div>
                  <div class="news-meta">
                    <span>${a.source || ''}</span>
                    <span>${formatDate(a.publishedAt)}</span>
                  </div>
                </div>
                <div class="news-score ${sLabel}">${s >= 0 ? '+' : ''}${(s*100).toFixed(0)}</div>
              </div>`;
          }).join('')}
        </div>
      </div>`;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><h3>Sentiment failed</h3><p>${e.message}</p></div>`;
  }
}

// ══════════════════════════════════════════════════════════
// RISK SECTION
// ══════════════════════════════════════════════════════════

async function loadRiskSection(ticker, riskData) {
  const container = document.getElementById('riskContent');
  try {
    // Use pre-fetched data or fetch
    const data = riskData && riskData.risk_level
      ? riskData
      : await fetch(`${API}/risk/${ticker}`).then(r => r.json());
    riskGlobalData = data;

    const riskScore = data.risk_score || 0;
    const riskLevel = data.risk_level || 'Medium Risk';
    const riskColor = riskScore < 33 ? '#10b981' : riskScore < 66 ? '#f59e0b' : '#ef4444';

    container.innerHTML = `
      <div class="risk-overview">
        <div class="risk-gauge">
          <div style="font-size:13px;color:#64748b;margin-bottom:12px">Risk Assessment</div>
          <div class="risk-score-ring" style="border-color:${riskColor}">
            <div class="rscore" style="color:${riskColor}">${riskScore.toFixed(0)}</div>
            <div class="rlabel">/ 100</div>
          </div>
          <div class="risk-level-text" style="color:${riskColor}">${riskLevel}</div>
          <div style="font-size:12px;color:#64748b;margin-top:8px">Based on volatility,<br>beta & drawdown</div>
        </div>
        <div class="risk-metrics">
          <h4 style="margin-bottom:12px">Risk Metrics</h4>
          <div class="risk-metric-grid">
            <div class="risk-metric-item">
              <div class="rm-label">Volatility</div>
              <div class="rm-value ${data.volatility > 40 ? 'red' : data.volatility > 20 ? 'yellow' : 'green'}">${(data.volatility||0).toFixed(2)}%</div>
              <div class="rm-sub">Annualized std dev</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">Beta</div>
              <div class="rm-value">${(data.beta||0).toFixed(2)}</div>
              <div class="rm-sub">vs NIFTY 50</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">Sharpe Ratio</div>
              <div class="rm-value ${data.sharpe_ratio > 1 ? 'green' : data.sharpe_ratio > 0 ? 'yellow' : 'red'}">${(data.sharpe_ratio||0).toFixed(2)}</div>
              <div class="rm-sub">Risk-adjusted return</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">Sortino Ratio</div>
              <div class="rm-value">${(data.sortino_ratio||0).toFixed(2)}</div>
              <div class="rm-sub">Downside risk</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">Max Drawdown</div>
              <div class="rm-value red">-${(data.max_drawdown||0).toFixed(1)}%</div>
              <div class="rm-sub">Largest peak-trough</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">VaR (95%)</div>
              <div class="rm-value red">${(data.var_95||0).toFixed(2)}%</div>
              <div class="rm-sub">1-day 95% confidence</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06)">
            <div class="risk-metric-item">
              <div class="rm-label">Suggested Stop Loss</div>
              <div class="rm-value red">₹${fmtPrice(data.stop_loss)}</div>
              <div class="rm-sub">2x ATR below</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">Support Level</div>
              <div class="rm-value green">₹${fmtPrice(data.support_level)}</div>
              <div class="rm-sub">60-day low</div>
            </div>
            <div class="risk-metric-item">
              <div class="rm-label">Resistance Level</div>
              <div class="rm-value">₹${fmtPrice(data.resistance_level)}</div>
              <div class="rm-sub">60-day high</div>
            </div>
          </div>
        </div>
      </div>`;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><h3>Risk analysis failed</h3><p>${e.message}</p></div>`;
  }
}

// ══════════════════════════════════════════════════════════
// BACKTEST
// ══════════════════════════════════════════════════════════

async function runBacktest() {
  if (!currentTicker) { showToast('Please analyze a stock first', 'error'); return; }

  const strategy = document.getElementById('strategySelect').value;
  const capital = parseFloat(document.getElementById('capitalInput').value) || 100000;
  const container = document.getElementById('backtestContent');

  container.innerHTML = '<div class="loading-inline">Running backtest...</div>';

  try {
    const data = await fetch(`${API}/backtest/${currentTicker}?strategy=${strategy}&capital=${capital}`).then(r => r.json());
    const allStrategies = data.all_strategies || {};
    const result = data.result || {};

    // Find best strategy
    const best = Object.entries(allStrategies).reduce((a, b) => b[1].total_return > a[1].total_return ? b : a, ['', { total_return: -Infinity }]);

    container.innerHTML = `
      <div class="strategies-comparison">
        ${Object.entries(allStrategies).map(([name, s]) => {
          const isWinner = name === best[0];
          return `
            <div class="strategy-card ${isWinner ? 'winner' : ''}">
              ${isWinner ? '<div style="font-size:10px;color:#10b981;margin-bottom:4px">⭐ BEST</div>' : ''}
              <div class="strategy-name">${name}</div>
              <div class="strategy-return ${s.total_return >= 0 ? 'pos' : 'neg'}">${s.total_return >= 0 ? '+' : ''}${(s.total_return||0).toFixed(2)}%</div>
              <div class="strategy-meta">Sharpe: ${(s.sharpe_ratio||0).toFixed(2)} | Trades: ${s.total_trades || 0}</div>
              <div class="strategy-meta">Win Rate: ${(s.win_rate||0).toFixed(1)}% | DD: -${(s.max_drawdown||0).toFixed(1)}%</div>
            </div>`;
        }).join('')}
      </div>

      <!-- Detailed Result -->
      <div class="cards-grid">
        <div class="metric-card">
          <div class="card-label">Initial Capital</div>
          <div class="card-value blue">₹${fmtNum(result.initial_capital)}</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Final Capital</div>
          <div class="card-value ${result.total_return >= 0 ? 'green' : 'red'}">₹${fmtNum(result.final_capital)}</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Total Return</div>
          <div class="card-value ${result.total_return >= 0 ? 'green' : 'red'}">${result.total_return >= 0 ? '+' : ''}${(result.total_return||0).toFixed(2)}%</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Win Rate</div>
          <div class="card-value">${(result.win_rate||0).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Sharpe Ratio</div>
          <div class="card-value">${(result.sharpe_ratio||0).toFixed(3)}</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Max Drawdown</div>
          <div class="card-value red">-${(result.max_drawdown||0).toFixed(2)}%</div>
        </div>
        <div class="metric-card">
          <div class="card-label">Total Trades</div>
          <div class="card-value">${result.total_trades || 0}</div>
        </div>
      </div>

      <!-- Portfolio Value Chart -->
      <div class="chart-card">
        <div class="chart-header"><h3>📈 Strategy Portfolio Value Comparison</h3></div>
        <div style="height:280px"><canvas id="backtestChart"></canvas></div>
      </div>`;

    setTimeout(() => renderBacktestChart(allStrategies), 100);

  } catch (e) {
    container.innerHTML = `<div class="empty-state"><h3>Backtest failed</h3><p>${e.message}</p></div>`;
  }
}

// ══════════════════════════════════════════════════════════
// PERIOD SWITCH
// ══════════════════════════════════════════════════════════

function switchPeriod(period) {
  currentPeriod = period;
  document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  if (currentTicker) renderCandlestick(currentTicker, period);
}

// ══════════════════════════════════════════════════════════
// MARKET INDICES TICKER
// ══════════════════════════════════════════════════════════

async function loadIndicesTicker() {
  try {
    const res = await fetch(`${API}/indices`);
    const data = await res.json();
    const indices = data.indices || [];

    if (indices.length === 0) return;

    const tickerInner = document.getElementById('tickerInner');
    // Duplicate for seamless scroll
    const items = [...indices, ...indices].map(idx => {
      const up = idx.change_pct >= 0;
      return `<span class="ticker-item">
        <span class="idx-name">${idx.name}</span>
        <span class="idx-price">${idx.price.toLocaleString('en-IN')}</span>
        <span class="idx-chg ${up ? 'up' : 'down'}">${up ? '▲' : '▼'} ${Math.abs(idx.change_pct).toFixed(2)}%</span>
      </span>`;
    }).join('');

    tickerInner.innerHTML = items;
  } catch (e) {
    console.warn('Could not load indices:', e);
  }
}

// ══════════════════════════════════════════════════════════
// MARKET TIME
// ══════════════════════════════════════════════════════════

function updateMarketTime() {
  const el = document.getElementById('marketTime');
  if (!el) return;
  const now = new Date();
  const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const h = ist.getHours(), m = ist.getMinutes();
  const isMarketOpen = (h > 9 || (h === 9 && m >= 15)) && (h < 15 || (h === 15 && m <= 30));
  const timeStr = ist.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  el.innerHTML = `<span style="color:${isMarketOpen ? '#10b981' : '#ef4444'}">${isMarketOpen ? '🟢' : '🔴'}</span> NSE ${timeStr} IST`;
}

// ══════════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════════

function setLoading(show, msg = 'Loading...') {
  const el = document.getElementById('globalLoading');
  const msgEl = document.getElementById('loadingMsg');
  if (el) el.classList.toggle('hidden', !show);
  if (msgEl && msg) msgEl.textContent = msg;
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? '--';
}

function fmtPrice(n) {
  if (!n && n !== 0) return '--';
  return parseFloat(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtVol(n) {
  if (!n) return '--';
  if (n >= 1e7) return (n / 1e7).toFixed(2) + 'Cr';
  if (n >= 1e5) return (n / 1e5).toFixed(2) + 'L';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function fmtMarketCap(n) {
  if (!n) return '--';
  if (n >= 1e12) return '₹' + (n / 1e12).toFixed(2) + 'T';
  if (n >= 1e9) return '₹' + (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e7) return '₹' + (n / 1e7).toFixed(2) + 'Cr';
  return '₹' + n.toLocaleString('en-IN');
}

function fmtNum(n) {
  if (!n) return '0';
  return n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  } catch { return ''; }
}

// ══════════════════════════════════════════════════════════
// INITIALIZATION
// ══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  // Load indices ticker
  loadIndicesTicker();

  // Update market time every minute
  updateMarketTime();
  setInterval(updateMarketTime, 60000);

  // Default to dashboard
  showSection('dashboard');

  // Theme toggle
  document.getElementById('themeToggle').addEventListener('click', () => {
    document.documentElement.classList.toggle('light-mode');
  });
});

// ══════════════════════════════════════════════════════════
// GLOBAL EXPORTS - required for HTML onclick attributes
// ══════════════════════════════════════════════════════════
window.showSection = showSection;
window.quickSelect = quickSelect;
window.analyzeStock = analyzeStock;
window.switchPeriod = switchPeriod;
window.runBacktest = runBacktest;
window.selectSuggestion = selectSuggestion;
