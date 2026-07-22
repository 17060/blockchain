(function () {
  const briefingForm = document.getElementById('briefing-form');
  const briefingResult = document.getElementById('briefing-result');
  const registryEl = document.getElementById('registry-board');
  const statusEl = document.getElementById('client-status');

  // Root-absolute paths so API calls work whether the page URL has a trailing slash.
  function api(path) {
    return path.charAt(0) === '/' ? path : '/' + path;
  }

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

  function setStatus(message, isError) {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = message || '';
    statusEl.hidden = !message;
    statusEl.className = isError ? 'status error' : 'status';
  }

  async function getJson(path, options) {
    const response = await fetch(api(path), options);
    const text = await response.text();
    var data = null;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (err) {
      throw new Error('Server returned a non-JSON response (' + response.status + ')');
    }
    if (!response.ok) {
      throw new Error((data && data.error) || ('Request failed (' + response.status + ')'));
    }
    return data;
  }

  function renderRows(items, mapper) {
    if (!items || !items.length) {
      return '<p class="empty">Nothing here yet.</p>';
    }
    return items.map(mapper).join('');
  }

  function renderRegistry(charts) {
    if (!registryEl) {
      return;
    }
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
      (data.sectors || []).map(function (sector) {
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
    const data = await getJson('/astrology/charts');
    renderRegistry(data.charts || []);
  }

  if (briefingForm) {
    briefingForm.addEventListener('submit', async function (event) {
      event.preventDefault();
      const form = new FormData(briefingForm);
      const birthDate = form.get('birth_date');
      if (!birthDate) {
        setStatus('Choose a birth date first.', true);
        return;
      }

      const payload = {
        owner: String(form.get('owner') || '').trim() || 'anonymous',
        birth_date: birthDate,
        register: form.get('register') === 'on'
      };

      briefingResult.hidden = false;
      briefingResult.innerHTML = '<p class="meta">Calculating chart and market affinities…</p>';
      setStatus('Working…');

      try {
        const data = await getJson('/astroeconomics/briefing', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        renderBriefing(data);
        if (data.registered) {
          await loadRegistry();
        }
        setStatus(data.registered
          ? 'Chart registered in block #' + data.block_index + '.'
          : 'Briefing ready.');
        briefingResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } catch (err) {
        briefingResult.innerHTML = '<p class="error">' + esc(err.message) + '</p>';
        setStatus(err.message, true);
      }
    });
  }

  // Server already rendered pulse/markets/forecast/registry. Never wipe them on load.
  setStatus('');
})();
