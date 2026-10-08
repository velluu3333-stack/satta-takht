// ============================================================
// Satta Takht — Mobile-First Frontend JS (by Saurav)
// Dynamic Cities + Scraped Live Results + 4 Khaiwal Boards + Live Chart
// English & Hinglish Clean Presentation
// ============================================================

// Live Render backend URL for Hostinger / production
const LIVE_BACKEND_URL = 'https://satta-takht.onrender.com';

const API_BASE = (window.location.origin && window.location.origin.includes('onrender.com'))
  ? `${window.location.origin}/api`
  : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? `${window.location.origin}/api`
    : `${LIVE_BACKEND_URL}/api`;

// PWA Install prompt or Custom APK / Play Store Link handling
let deferredPrompt;
let customAppLink = '';

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const banner = document.getElementById('app-download-banner');
  if (banner) banner.style.display = 'flex';
});

function installApp() {
  if (customAppLink && customAppLink.trim() !== '') {
    window.open(customAppLink, '_blank');
    return;
  }

  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the app install prompt');
      }
      deferredPrompt = null;
    });
  } else {
    alert('To install app: Tap your browser menu (⋮) and select "Add to Home screen" or "Install app".');
  }
}

// Live simulated online users
function updateOnlineUsers() {
  const base = 1450;
  const variance = Math.floor(Math.random() * 80) - 40;
  const el = document.getElementById('online-users');
  if (el) el.textContent = (base + variance).toLocaleString('en-IN');
}
setInterval(updateOnlineUsers, 8000);

// Live Clock
function updateClock() {
  const now = new Date();
  const el = document.getElementById('live-clock');
  if (el) {
    el.textContent = now.toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric'
    }) + ' • ' + now.toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
  }
}
setInterval(updateClock, 1000);
updateClock();

// ---- Main Data Loader ----
async function loadAllData() {
  try {
    const [citiesRes, resultsRes, khaiwalsRes, settingsRes] = await Promise.all([
      fetch(`${API_BASE}/cities`),
      fetch(`${API_BASE}/results/today`),
      fetch(`${API_BASE}/khaiwals`),
      fetch(`${API_BASE}/settings`)
    ]);

    const cities   = await citiesRes.json();
    const results  = await resultsRes.json();
    const khaiwals = await khaiwalsRes.json();
    const settings = await settingsRes.json();

    renderHeroHighlight(cities, results);
    renderResultsGrid(cities, results);
    renderKhaiwalBoards(khaiwals);
    renderChart(cities);
    applySiteSettings(settings);

    const upEl = document.getElementById('last-updated');
    if (upEl) upEl.textContent = `Updated: ${new Date().toLocaleTimeString('en-IN')}`;

  } catch (err) {
    console.warn('API fetch error, using fallback:', err);
    loadFallbackData();
  }
}

// Global settings cache
let currentSettings = {};

// Apply Dynamic Telegram & WhatsApp Links, Themes, and Leak Jodi across Website
function applySiteSettings(settings) {
  if (!settings) return;
  currentSettings = settings;

  // 1. Separate Chatbot Links (Floating Bottom Buttons)
  const cbTgLink = settings.chatbot_telegram || settings.telegram_link || 'https://t.me/';
  const cbWaNum  = settings.chatbot_whatsapp || settings.whatsapp_number || '919999999999';
  const cbWaLink = `https://wa.me/${cbWaNum}?text=Hello%20Satta%20Takht%20Chatbot`;

  const fabTg = document.querySelector('.fab-tg');
  if (fabTg) fabTg.href = cbTgLink;

  const fabWa = document.querySelector('.fab-wa');
  if (fabWa) fabWa.href = cbWaLink;

  // 2. Separate Support Helpline & Community Links (Cards at bottom)
  const spTgLink = settings.support_telegram || settings.telegram_link || 'https://t.me/';
  const spWaNum  = settings.support_whatsapp || settings.whatsapp_number || '919999999999';
  const spWaLink = `https://wa.me/${spWaNum}?text=Hello%20Satta%20Takht%20Support`;

  const commTg = document.querySelector('.tg-btn');
  if (commTg) commTg.href = spTgLink;

  const commWa = document.querySelector('.wa-btn');
  if (commWa) commWa.href = spWaLink;

  // 3. Custom APK or Play Store link
  customAppLink = settings.app_download_link || '';

  // 4. Site-Wide Theme Switcher
  const theme = settings.site_theme || 'theme-classic-dark';
  document.body.className = theme;

  // 5. VIP Leak Jodi Board (Below APK Box)
  const leakSection = document.getElementById('leak-jodi-section');
  if (leakSection) {
    if (settings.leak_jodi_active === '1' || settings.leak_jodi_active === undefined) {
      leakSection.style.display = 'block';
      const titleEl = document.getElementById('leak-title');
      const tagEl   = document.getElementById('leak-tagline');
      const gamesEl = document.getElementById('leak-games');
      const noteEl  = document.getElementById('leak-note');
      const btnWa   = document.getElementById('leak-btn-wa');
      const btnTg   = document.getElementById('leak-btn-tg');

      if (titleEl && settings.leak_jodi_title) titleEl.textContent = settings.leak_jodi_title;
      if (tagEl && settings.leak_jodi_tagline) tagEl.textContent = settings.leak_jodi_tagline;
      if (gamesEl && settings.leak_jodi_games) gamesEl.textContent = settings.leak_jodi_games;
      if (noteEl && settings.leak_jodi_note) noteEl.textContent = settings.leak_jodi_note;

      const leakWa = settings.leak_jodi_whatsapp || '919999999999';
      if (btnWa) btnWa.href = `https://wa.me/${leakWa}?text=Hello%20Mujhe%20VIP%20Leak%20Jodi%20Chahiye`;

      const leakTg = settings.leak_jodi_telegram || 'https://t.me/';
      if (btnTg) btnTg.href = leakTg;
    } else {
      leakSection.style.display = 'none';
    }
  }
}

// 1. Render Top Hero Highlight (Desawar or First Live Result)
function renderHeroHighlight(cities, results) {
  const heroName   = document.getElementById('hero-city-name');
  const heroTime   = document.getElementById('hero-city-time');
  const heroNum    = document.getElementById('hero-city-num');
  const heroStatus = document.getElementById('hero-city-status');
  if (!heroName || !heroNum) return;

  // Find Desawar or first city
  let highlightCity = cities.find(c => c.city_key === 'desawar') || cities[0];
  if (!highlightCity) return;

  const num = results[highlightCity.city_key] || '';
  const isDeclared = num && num.toUpperCase() !== 'XX';

  heroName.textContent = `${highlightCity.display_name}`;
  heroTime.textContent = `⏰ ${highlightCity.result_time || ''}`;
  
  if (isDeclared) {
    heroNum.textContent = num;
    heroNum.classList.add('live-val');
    if (heroStatus) heroStatus.textContent = 'RESULT DECLARED (LIVE)';
  } else {
    heroNum.textContent = '--';
    heroNum.classList.remove('live-val');
    if (heroStatus) heroStatus.textContent = 'Waiting for Result...';
  }
}

// 2. Render 2-Column Clean Mobile Cards
function renderResultsGrid(cities, results) {
  const grid = document.getElementById('results-grid');
  if (!grid) return;
  grid.innerHTML = '';

  cities.forEach((city, idx) => {
    const val = results[city.city_key] || '';
    const isDeclared = val && val.toUpperCase() !== 'XX';
    const isFeatured = idx < 2; // Desawar & Delhi Bazar highlighted

    const card = document.createElement('div');
    card.className = `result-card ${isFeatured ? 'card-featured' : ''}`;
    card.innerHTML = `
      <div class="card-city">${city.display_name}</div>
      <div class="card-time">Time: ${city.result_time || ''}</div>
      <div class="card-num ${isDeclared ? 'live' : 'pending'}">
        ${isDeclared ? val : 'XX'}
      </div>
      <div class="card-status-text ${isDeclared ? 'live-text' : ''}">
        ${isDeclared ? 'RESULT OUT' : 'WAITING'}
      </div>
    `;
    grid.appendChild(card);
  });
}

// 3. Render Khaiwal Boards (Redesigned with Dual WhatsApp + Telegram & Dynamic Themes)
function renderKhaiwalBoards(khaiwals) {
  const container = document.getElementById('khaiwal-container');
  if (!container) return;
  container.innerHTML = '';

  if (!khaiwals || !khaiwals.length) {
    container.innerHTML = '<p style="text-align:center;color:#666;">No Khaiwal Boards Active.</p>';
    return;
  }

  khaiwals.forEach(b => {
    const card = document.createElement('div');
    const themeClass = b.board_theme || 'theme-blue';
    card.className = `khaiwal-board-card ${themeClass}`;

    // Format timings cleanly if separated by pipe |
    let timingsHtml = '';
    if (b.timings && b.timings.trim()) {
      const parts = b.timings.split('|').map(s => s.trim()).filter(Boolean);
      if (parts.length > 1) {
        timingsHtml = `<div class="khaiwal-timing-grid">` +
          parts.map(p => `<div class="timing-chip"><span class="check-icon">✅</span> ${p}</div>`).join('') +
          `</div>`;
      } else {
        timingsHtml = `<div class="khaiwal-timings-line">⏰ ${b.timings}</div>`;
      }
    }

    const waNum = b.whatsapp || '919999999999';
    const waUrl = `https://wa.me/${waNum}?text=Hello%20${encodeURIComponent(b.name || 'Khaiwal')}%20bhai`;
    const tgUrl = (b.telegram && b.telegram.trim()) 
      ? (b.telegram.startsWith('http') ? b.telegram : `https://t.me/${b.telegram.replace('@', '')}`)
      : (currentSettings.support_telegram || 'https://t.me/');

    card.innerHTML = `
      <div class="khaiwal-header">
        ${b.badge ? `<span class="khaiwal-badge">${b.badge}</span>` : ''}
        <h3 class="khaiwal-name">[ ✅ ${b.name} ✅ ]</h3>
        ${b.tagline ? `<p class="khaiwal-tagline">${b.tagline}</p>` : ''}
      </div>

      <div class="khaiwal-rates">
        <div class="rate-box jodi-box">
          <div class="rate-label">🎯 जोड़ी रेट</div>
          <div class="rate-value">➔ ${b.rate_jodi || '10 का 950'}</div>
        </div>
        <div class="rate-box haruf-box">
          <div class="rate-label">⭐ हरूफ रेट</div>
          <div class="rate-value">➔ ${b.rate_haruf || '100 का 950'}</div>
        </div>
      </div>

      <div class="khaiwal-beads">
        <span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span>
      </div>

      ${timingsHtml}

      <div class="khaiwal-payment-info">
        💰 पेमेंट लेन-देन <strong>ALL IN UPI</strong> (PhonePe / GPay / Paytm QR Code)
      </div>

      <div class="khaiwal-diamonds">
        💎 💎 💎 💎 💎 💎 💎 💎
      </div>

      <div class="khaiwal-contact-display">
        WhatsApp: <span>+${waNum}</span>
      </div>

      <div class="khaiwal-actions-dual">
        <a href="${waUrl}" target="_blank" class="btn-khaiwal-wa">
          <span class="btn-icon">💬</span> WHATSAPP पर खेलें
        </a>
        <a href="${tgUrl}" target="_blank" class="btn-khaiwal-tg">
          <span class="btn-icon">📢</span> TELEGRAM
        </a>
      </div>
    `;
    container.appendChild(card);
  });
}

// 4. Render Monthly Record Chart
async function renderChart(cities) {
  try {
    const res = await fetch(`${API_BASE}/results/chart`);
    const rows = await res.json();

    const thead = document.querySelector('#chart-table thead tr');
    if (thead) {
      const displayCities = cities.slice(0, 6);
      thead.innerHTML = '<th>Date</th>' + displayCities.map(c => `<th>${c.display_name}</th>`).join('');

      const tbody = document.getElementById('chart-body');
      if (tbody) {
        tbody.innerHTML = '';
        if (!rows.length) {
          tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:16px;color:#666;">No Chart Data Available.</td></tr>';
          return;
        }

        rows.forEach(row => {
          const tr = document.createElement('tr');
          const dateTd = `<td>${row.date || ''}</td>`;
          const cityTds = displayCities.map(c => {
            const val = row[c.city_key];
            return val ? `<td class="num">${val}</td>` : `<td class="empty">—</td>`;
          }).join('');
          tr.innerHTML = dateTd + cityTds;
          tbody.appendChild(tr);
        });
      }
    }
  } catch (err) {
    console.warn('Error loading chart:', err);
  }
}

// Fallback in case of server delay
function loadFallbackData() {
  const fallbackCities = [
    { city_key: 'desawar', display_name: 'DESAWAR', result_time: '05:00 AM' },
    { city_key: 'delhi_bazar', display_name: 'DELHI BAZAR', result_time: '03:00 PM' },
    { city_key: 'shree_ganesh', display_name: 'SHREE GANESH', result_time: '04:30 PM' },
    { city_key: 'faridabad', display_name: 'FARIDABAD', result_time: '06:00 PM' },
    { city_key: 'ghaziabad', display_name: 'GHAZIABAD', result_time: '09:30 PM' },
    { city_key: 'gali', display_name: 'GALI', result_time: '11:25 PM' }
  ];
  renderResultsGrid(fallbackCities, {});
}

// Manual Refresh Trigger
function manualRefresh() {
  const icon = document.getElementById('refresh-icon');
  if (icon) icon.style.transform = 'rotate(360deg)';
  loadAllData().finally(() => {
    setTimeout(() => {
      if (icon) icon.style.transform = 'rotate(0deg)';
    }, 500);
  });
}

// Auto Refresh every 3 minutes
loadAllData();
setInterval(loadAllData, 3 * 60 * 1000);
