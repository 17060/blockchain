(function () {
  const pulseEl = document.getElementById('pulse');
  const marketsEl = document.getElementById('markets-board');
  const forecastEl = document.getElementById('forecast-board');
  const registryEl = document.getElementById('registry-board');
  const briefingForm = document.getElementById('briefing-form');
  const briefingResult = document.getElementById('briefing-result');

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function title(value) {
    return String(value || '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, function (ch) { return ch.toUpperCase(); });
  }

  async function getJson(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Request failed');
    }
    return data;
  }

  function renderPulse(pulse) {
    const moon = pulse.sky.moon_phase;
    const lead = pulse.leading_sign;
    pulseEl.innerHTML = [
      '<article class="stat">',
      '  <div class="stat-label">Market aura</div>',
      '  <div class="aura-ring" style="--score:' + esc(pulse.market_aura) + '"><strong>' + esc(pulse.market_aura) + '</strong></div>',
      '  <p class="stat-note">' + esc(pulse.stance) + '</p>',
      '</article>',
      '<article class="stat">',
      '  <div class="stat-label">Sky now</div>',
      '  <p class="stat-value">' + esc(moon.name) + '</p>',
      '  <p class="stat-note">Sun in ' + esc(title(pulse.sky.sun_sign)) +
        ' · ' + esc(title(pulse.sky.planetary_day.ruler)) + ' day' +
        (pulse.sky.mercury_retrograde ? ' · Mercury retrograde' : '') + '</p>',
      '</article>',
      '<article class="stat">',
      '  <div class="stat-label">Leading sign</div>',
      '  <p class="stat-value">' + esc(lead.glyph) + ' ' + esc(title(lead.sign)) + '</p>',
      '  <p class="stat-note">Aura ' + esc(lead.score) + ' · ' + esc(lead.sectors.join(', ')) + '</p>',
      '</article>'
    ].join('');
  }

  function renderRows(items, mapper) {
    if (!items || !items.length) {
      return '<p class="empty">Nothing here yet.</p>';
    }
    return items.map(mapper).join('');
  }

  function renderMarkets(pulse) {
    marketsEl.innerHTML = [
      '<div class="market-block">',
      '  <h3>Cosmic watchlist</h3>',
      renderRows(pulse.watchlist, function (item) {
        return [
          '<div class="row">',
          '  <div class="symbol">' + esc(item.symbol) + '</div>',
          '  <div><div>' + esc(item.name) + '</div><div class="why">' + esc(item.why) + '</div></div>',
          '  <div class="score-pill">' + esc(item.aura_score) + '</div>',
          '</div>'
        ].join('');
      }),
      '</div>',
      '<div class="market-block">',
      '  <h3>Index picture</h3>',
      renderRows(pulse.indexes, function (item) {
        return [
          '<div class="row">',
          '  <div class="symbol">' + esc(item.symbol) + '</div>',
          '  <div><div>' + esc(item.name) + ' · ' + esc(item.glyph) + ' ' + esc(title(item.sign)) + '</div>',
          '  <div class="why">' + esc(item.sentiment) + ' · vol ' + esc(item.volatility) + '</div></div>',
          '  <div class="score-pill">' + esc(item.aura_score) + '</div>',
          '</div>'
        ].join('');
      }),
      '</div>'
    ].join('');
  }

  function renderForecast(pulse) {
    forecastEl.innerHTML = renderRows(pulse.forecast, function (day) {
      return [
        '<article class="forecast-row">',
        '  <strong>' + esc(title(day.weekday).slice(0, 3)) + '</strong>',
        '  <div class="meta">' + esc(day.date.slice(5)) + '</div>',
        '  <div class="intensity"><span style="width:' + esc(day.intensity) + '%"></span></div>',
        '  <div class="meta">' + esc(day.moon_phase) + '</div>',
        '  <div class="meta">' + esc(day.note) + '</div>',
        '</article>'
      ].join('');
    });
  }

  function renderRegistry(charts) {
    if (!charts.length) {
      registryEl.innerHTML = '<p class="empty">No charts registered yet. Generate a briefing with “Register chart on-chain” checked.</p>';
      return;
    }
    registryEl.innerHTML = charts.map(function (chart) {
      return [
        '<article class="registry-row">',
        '  <div class="glyph">' + esc(chart.glyph || '✦') + '</div>',
        '  <div>',
        '    <strong>' + esc(chart.sender) + '</strong>',
        '    <div class="meta">' + esc(title(chart.sun_sign)) + ' · born ' + esc(chart.birth_date) +
          ' · ' + esc(chart.element) + '/' + esc(chart.modality) + '</div>',
        '  </div>',
        '  <div class="meta">on-chain</div>',
        '</article>'
      ].join('');
    }).join('');
  }

  function renderBriefing(data) {
    const chart = data.chart;
    const horoscope = data.horoscope;
    briefingResult.hidden = false;
    briefingResult.innerHTML = [
      '<div class="brief-grid">',
      '  <div>',
      '    <div class="glyph">' + esc(chart.glyph) + '</div>',
      '    <h3>' + esc(title(chart.sun_sign)) + '</h3>',
      '    <p class="score-xl">' + esc(data.aura_score) + '</p>',
      '    <p class="meta">Personal aura · ' + esc(data.market_bias) + '</p>',
      '    <div class="chips">',
      data.sectors.map(function (sector) {
        return '<span class="chip">' + esc(sector) + '</span>';
      }).join(''),
      '    </div>',
      '  </div>',
      '  <div>',
      '    <h3>' + esc(horoscope.headline) + '</h3>',
      '    <p>' + esc(horoscope.reading) + '</p>',
      '    <p class="meta">' + esc(horoscope.moon_phase) + ' · ' +
        esc(title(horoscope.day_ruler)) + ' day' +
        (horoscope.mercury_retrograde ? ' · Mercury retrograde' : '') + '</p>',
      data.registered
        ? '<p class="meta">Registered in block #' + esc(data.block_index) + '</p>'
        : '',
      '  </div>',
      '</div>',
      '<div class="market-block">',
      '  <h3>Your aligned names</h3>',
      renderRows(data.watchlist, function (item) {
        return [
          '<div class="row">',
          '  <div class="symbol">' + esc(item.symbol) + '</div>',
          '  <div><div>' + esc(item.name) + '</div><div class="why">' + esc(item.why) + '</div></div>',
          '  <div class="score-pill">' + esc(item.aura_score) + '</div>',
          '</div>'
        ].join('');
      }),
      '</div>',
      '<p class="meta">' + esc(data.disclaimer) + '</p>'
    ].join('');
  }

  async function loadRegistry() {
    const data = await getJson('astrology/charts');
    renderRegistry(data.charts || []);
  }

  async function boot() {
    try {
      const pulse = await getJson('astroeconomics/pulse');
      renderPulse(pulse);
      renderMarkets(pulse);
      renderForecast(pulse);
      await loadRegistry();
    } catch (err) {
      pulseEl.innerHTML = '<p class="error">' + esc(err.message) + '</p>';
    }
  }

  briefingForm.addEventListener('submit', async function (event) {
    event.preventDefault();
    const form = new FormData(briefingForm);
    const payload = {
      owner: String(form.get('owner') || '').trim() || 'anonymous',
      birth_date: form.get('birth_date'),
      register: form.get('register') === 'on'
    };

    briefingResult.hidden = false;
    briefingResult.innerHTML = '<p class="meta">Calculating chart and market affinities…</p>';

    try {
      const data = await getJson('astroeconomics/briefing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      renderBriefing(data);
      if (data.registered) {
        await loadRegistry();
      }
      briefingResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      briefingResult.innerHTML = '<p class="error">' + esc(err.message) + '</p>';
    }
  });

  boot();
})();
