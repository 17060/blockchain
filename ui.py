"""Plain HTML UI for AstroEconomics — no JS required to render."""

from html import escape


def _e(value):
    return escape(str(value if value is not None else ''), quote=True)


def _title(value):
    return _e(str(value or '').replace('_', ' ').title())


def render_app(pulse=None, charts=None, briefing=None, error=None, form=None):
    """Return a full HTML document with inline styles and a classic form POST."""
    charts = charts or []
    form = form or {}
    owner = form.get('owner', '')
    birth_date = form.get('birth_date', '')
    register_checked = 'checked' if form.get('register', True) else ''

    parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>AstroEconomics</title>',
        '<style>',
        'body{margin:0;font-family:Georgia,Times,serif;background:#eef3f0;color:#10233a;line-height:1.45}',
        'a{color:#065f5a}',
        '.banner{background:#10233a;color:#fff;padding:12px 16px;font-family:Arial,Helvetica,sans-serif;font-size:14px}',
        '.banner strong{font-size:16px}',
        '.wrap{max-width:960px;margin:0 auto;padding:24px 16px 48px}',
        'h1{font-size:42px;line-height:1;margin:0 0 8px;letter-spacing:-1px;color:#10233a}',
        'h2{font-size:24px;margin:32px 0 8px;border-top:1px solid #c5d0c9;padding-top:20px;color:#10233a}',
        'p.lead{font-size:18px;color:#3a4f66;max-width:36em}',
        '.grid{display:block}',
        '.card{background:#fff;border:1px solid #c5d0c9;padding:14px 16px;margin:10px 0}',
        'label{display:block;margin:10px 0 4px;font-weight:bold}',
        'input[type=text],input[type=date]{width:100%;max-width:320px;padding:10px;font:inherit;border:1px solid #8aa;background:#fff;color:#10233a}',
        'button,.btn{display:inline-block;margin-top:14px;padding:10px 16px;background:#10233a;color:#fff;',
        'border:0;font:inherit;cursor:pointer;text-decoration:none}',
        'table{width:100%;border-collapse:collapse;margin-top:10px;background:#fff}',
        'th,td{border:1px solid #c5d0c9;padding:8px;text-align:left;vertical-align:top;color:#10233a}',
        'th{background:#dfe9e4}',
        '.error{color:#8a2a2a;background:#f8eaea;padding:10px;border:1px solid #e0b4b4}',
        '.ok{color:#065f5a;background:#e7f4f1;padding:10px;border:1px solid #9cc}',
        '.muted{color:#3a4f66}',
        '@media(min-width:800px){.grid{display:flex;gap:12px}.grid .card{flex:1}}',
        '</style>',
        '</head>',
        '<body>',
        '<div class="banner"><strong>AstroEconomics</strong> &mdash; app is running. '
        'Enter a birth date below for your market briefing.</div>',
        '<div class="wrap">',
        '<h1>Read the sky. Time the market.</h1>',
        '<p class="lead">Daily planetary weather mapped to sectors, indexes, and your birth chart, '
        'then sealed on a local blockchain registry.</p>',
        '<p class="muted">Entertainment and education only. Not financial advice.</p>',
    ]

    if error:
        parts.append('<p class="error">%s</p>' % _e(error))

    # Pulse
    parts.append('<h2>Today\'s market pulse</h2>')
    if pulse:
        sky = pulse.get('sky') or {}
        moon = sky.get('moon_phase') or {}
        day = sky.get('planetary_day') or {}
        lead = pulse.get('leading_sign') or {}
        parts.append('<div class="grid">')
        parts.append(
            '<div class="card"><strong>Market aura</strong><br>'
            '<span style="font-size:36px">%s</span><br>%s</div>'
            % (_e(pulse.get('market_aura')), _e(pulse.get('stance')))
        )
        parts.append(
            '<div class="card"><strong>Sky now</strong><br>%s<br>'
            'Sun in %s · %s day%s</div>'
            % (
                _e(moon.get('name')),
                _title(sky.get('sun_sign')),
                _title(day.get('ruler')),
                ' · Mercury retrograde' if sky.get('mercury_retrograde') else '',
            )
        )
        parts.append(
            '<div class="card"><strong>Leading sign</strong><br>%s %s<br>'
            'Aura %s · %s</div>'
            % (
                _e(lead.get('glyph')),
                _title(lead.get('sign')),
                _e(lead.get('score')),
                _e(', '.join(lead.get('sectors') or [])),
            )
        )
        parts.append('</div>')
    else:
        parts.append('<p class="error">Pulse data unavailable.</p>')

    # Briefing form — classic POST, no JavaScript
    parts.append('<h2>Your chart briefing</h2>')
    parts.append('<div class="card">')
    parts.append('<form method="post" action="/">')
    parts.append('<label for="owner">Your name</label>')
    parts.append(
        '<input id="owner" name="owner" type="text" value="%s" placeholder="Ada">'
        % _e(owner)
    )
    parts.append('<label for="birth_date">Birth date</label>')
    parts.append(
        '<input id="birth_date" name="birth_date" type="date" required value="%s">'
        % _e(birth_date)
    )
    parts.append(
        '<label><input type="checkbox" name="register" value="1" %s> '
        'Register chart on-chain</label>' % register_checked
    )
    parts.append('<button type="submit">Get briefing</button>')
    parts.append('</form>')
    parts.append('</div>')

    if briefing:
        chart = briefing.get('chart') or {}
        horoscope = briefing.get('horoscope') or {}
        parts.append('<div class="card ok">')
        parts.append(
            '<p><strong>%s %s</strong> · personal aura %s · %s</p>'
            % (
                _e(chart.get('glyph')),
                _title(chart.get('sun_sign')),
                _e(briefing.get('aura_score')),
                _e(briefing.get('market_bias')),
            )
        )
        parts.append('<p>%s</p>' % _e(horoscope.get('headline')))
        parts.append('<p>%s</p>' % _e(horoscope.get('reading')))
        parts.append(
            '<p class="muted">%s · %s day%s</p>'
            % (
                _e(horoscope.get('moon_phase')),
                _title(horoscope.get('day_ruler')),
                ' · Mercury retrograde' if horoscope.get('mercury_retrograde') else '',
            )
        )
        if briefing.get('registered'):
            parts.append(
                '<p><strong>Registered in block #%s</strong></p>'
                % _e(briefing.get('block_index'))
            )
        sectors = briefing.get('sectors') or []
        if sectors:
            parts.append('<p>Sectors: %s</p>' % _e(', '.join(sectors)))
        watchlist = briefing.get('watchlist') or []
        if watchlist:
            parts.append('<table><tr><th>Symbol</th><th>Name</th><th>Aura</th><th>Why</th></tr>')
            for item in watchlist:
                parts.append(
                    '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                    % (
                        _e(item.get('symbol')),
                        _e(item.get('name')),
                        _e(item.get('aura_score')),
                        _e(item.get('why')),
                    )
                )
            parts.append('</table>')
        parts.append('</div>')

    # Markets
    parts.append('<h2>Market pulse</h2>')
    if pulse:
        parts.append('<h3>Cosmic watchlist</h3>')
        parts.append('<table><tr><th>Symbol</th><th>Name</th><th>Aura</th><th>Why</th></tr>')
        for item in pulse.get('watchlist') or []:
            parts.append(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                % (
                    _e(item.get('symbol')),
                    _e(item.get('name')),
                    _e(item.get('aura_score')),
                    _e(item.get('why')),
                )
            )
        parts.append('</table>')

        parts.append('<h3>Index picture</h3>')
        parts.append(
            '<table><tr><th>Symbol</th><th>Name</th><th>Sign</th>'
            '<th>Aura</th><th>Sentiment</th></tr>'
        )
        for item in pulse.get('indexes') or []:
            parts.append(
                '<tr><td>%s</td><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td></tr>'
                % (
                    _e(item.get('symbol')),
                    _e(item.get('name')),
                    _e(item.get('glyph')),
                    _title(item.get('sign')),
                    _e(item.get('aura_score')),
                    _e(item.get('sentiment')),
                )
            )
        parts.append('</table>')

    # Forecast
    parts.append('<h2>Seven-day sky</h2>')
    if pulse:
        parts.append(
            '<table><tr><th>Day</th><th>Date</th><th>Moon</th>'
            '<th>Intensity</th><th>Note</th></tr>'
        )
        for day in pulse.get('forecast') or []:
            parts.append(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                % (
                    _title((day.get('weekday') or '')[:3]),
                    _e((day.get('date') or '')[5:]),
                    _e(day.get('moon_phase')),
                    _e(day.get('intensity')),
                    _e(day.get('note')),
                )
            )
        parts.append('</table>')

    # Registry
    parts.append('<h2>On-chain chart registry</h2>')
    if charts:
        parts.append(
            '<table><tr><th>Owner</th><th>Sign</th><th>Birth date</th>'
            '<th>Element</th></tr>'
        )
        for chart in charts:
            parts.append(
                '<tr><td>%s</td><td>%s %s</td><td>%s</td><td>%s / %s</td></tr>'
                % (
                    _e(chart.get('sender')),
                    _e(chart.get('glyph') or '✦'),
                    _title(chart.get('sun_sign')),
                    _e(chart.get('birth_date')),
                    _e(chart.get('element')),
                    _e(chart.get('modality')),
                )
            )
        parts.append('</table>')
    else:
        parts.append(
            '<p class="muted">No charts registered yet. Submit a briefing with '
            '“Register chart on-chain” checked.</p>'
        )

    parts.append(
        '<p class="muted" style="margin-top:32px">API: '
        '<a href="/health">/health</a> · '
        '<a href="/astroeconomics/pulse">/astroeconomics/pulse</a> · '
        '<a href="/astrology/charts">/astrology/charts</a></p>'
    )
    parts.append('</div></body></html>')
    return '\n'.join(parts)
