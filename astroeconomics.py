"""AstroEconomics — map planetary weather onto market themes and watchlists."""

from astrology import (
    SIGN_METADATA,
    SIGN_ORDER,
    build_chart,
    coerce_date,
    cosmic_weather,
    current_sun_sign,
    daily_horoscope,
    describe_sign,
    is_mercury_retrograde,
    moon_phase,
    next_mercury_station,
    planetary_day,
)

# Classical financial-astrology sector affinities.
SECTOR_MAP = {
    'aries': {
        'sectors': ('Energy', 'Defense', 'Automotive'),
        'assets': (
            {'symbol': 'XLE', 'name': 'Energy Select Sector SPDR'},
            {'symbol': 'TSLA', 'name': 'Tesla'},
            {'symbol': 'CAT', 'name': 'Caterpillar'},
        ),
        'bias': 'offensive growth',
    },
    'taurus': {
        'sectors': ('Banks', 'Real Estate', 'Consumer Staples'),
        'assets': (
            {'symbol': 'XLF', 'name': 'Financial Select Sector SPDR'},
            {'symbol': 'VNQ', 'name': 'Vanguard Real Estate ETF'},
            {'symbol': 'KO', 'name': 'Coca-Cola'},
        ),
        'bias': 'value preservation',
    },
    'gemini': {
        'sectors': ('Media', 'Telecom', 'Transport'),
        'assets': (
            {'symbol': 'XLC', 'name': 'Communication Services Select Sector'},
            {'symbol': 'UBER', 'name': 'Uber'},
            {'symbol': 'DIS', 'name': 'Disney'},
        ),
        'bias': 'information flow',
    },
    'cancer': {
        'sectors': ('Housing', 'Food', 'Retail'),
        'assets': (
            {'symbol': 'XHB', 'name': 'SPDR S&P Homebuilders'},
            {'symbol': 'COST', 'name': 'Costco'},
            {'symbol': 'WMT', 'name': 'Walmart'},
        ),
        'bias': 'defensive demand',
    },
    'leo': {
        'sectors': ('Entertainment', 'Luxury', 'Gold'),
        'assets': (
            {'symbol': 'GLD', 'name': 'SPDR Gold Shares'},
            {'symbol': 'NFLX', 'name': 'Netflix'},
            {'symbol': 'LVMUY', 'name': 'LVMH ADR'},
        ),
        'bias': 'visibility premium',
    },
    'virgo': {
        'sectors': ('Healthcare', 'Business Services', 'Software'),
        'assets': (
            {'symbol': 'XLV', 'name': 'Health Care Select Sector SPDR'},
            {'symbol': 'V', 'name': 'Visa'},
            {'symbol': 'ADP', 'name': 'ADP'},
        ),
        'bias': 'operational quality',
    },
    'libra': {
        'sectors': ('Fashion', 'Legal Tech', 'Partnerships'),
        'assets': (
            {'symbol': 'XLY', 'name': 'Consumer Discretionary Select Sector'},
            {'symbol': 'SPOT', 'name': 'Spotify'},
            {'symbol': 'ETSY', 'name': 'Etsy'},
        ),
        'bias': 'balanced rotation',
    },
    'scorpio': {
        'sectors': ('Insurance', 'Mining', 'Crypto'),
        'assets': (
            {'symbol': 'BTC-USD', 'name': 'Bitcoin'},
            {'symbol': 'XLE', 'name': 'Energy Select Sector SPDR'},
            {'symbol': 'MET', 'name': 'MetLife'},
        ),
        'bias': 'asymmetric risk',
    },
    'sagittarius': {
        'sectors': ('Travel', 'Education', 'Emerging Markets'),
        'assets': (
            {'symbol': 'EEM', 'name': 'iShares MSCI Emerging Markets'},
            {'symbol': 'BKNG', 'name': 'Booking Holdings'},
            {'symbol': 'DAL', 'name': 'Delta Air Lines'},
        ),
        'bias': 'global expansion',
    },
    'capricorn': {
        'sectors': ('Infrastructure', 'Industrials', 'Blue Chips'),
        'assets': (
            {'symbol': 'DIA', 'name': 'SPDR Dow Jones Industrial Average'},
            {'symbol': 'UNP', 'name': 'Union Pacific'},
            {'symbol': 'JPM', 'name': 'JPMorgan Chase'},
        ),
        'bias': 'institutional discipline',
    },
    'aquarius': {
        'sectors': ('Technology', 'Renewables', 'Networks'),
        'assets': (
            {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust'},
            {'symbol': 'ICLN', 'name': 'iShares Global Clean Energy'},
            {'symbol': 'NVDA', 'name': 'NVIDIA'},
        ),
        'bias': 'innovation beta',
    },
    'pisces': {
        'sectors': ('Pharma', 'Oil', 'Arts & Media'),
        'assets': (
            {'symbol': 'XBI', 'name': 'SPDR S&P Biotech'},
            {'symbol': 'USO', 'name': 'United States Oil Fund'},
            {'symbol': 'ETH-USD', 'name': 'Ethereum'},
        ),
        'bias': 'liquidity & intuition',
    },
}

INDEX_BOARD = (
    {'symbol': 'SPX', 'name': 'S&P 500', 'sign': 'capricorn'},
    {'symbol': 'NDX', 'name': 'Nasdaq 100', 'sign': 'aquarius'},
    {'symbol': 'DJI', 'name': 'Dow Jones', 'sign': 'taurus'},
    {'symbol': 'BTC', 'name': 'Bitcoin', 'sign': 'scorpio'},
    {'symbol': 'ETH', 'name': 'Ethereum', 'sign': 'pisces'},
    {'symbol': 'GLD', 'name': 'Gold', 'sign': 'leo'},
)


def sign_market_profile(sign):
    """Return sector/asset affinities for a zodiac sign."""
    meta = describe_sign(sign)
    mapping = SECTOR_MAP[meta['sign']]
    return {
        **meta,
        'sectors': list(mapping['sectors']),
        'assets': [dict(asset) for asset in mapping['assets']],
        'bias': mapping['bias'],
    }


def _score_sign(sign, on_date):
    """Compute a 0–100 cosmic aura score for a sign on a date."""
    target = coerce_date(on_date)
    meta = SIGN_METADATA[sign]
    phase = moon_phase(target)
    day = planetary_day(target)
    transit_sun = current_sun_sign(target)
    score = 52

    # Element harmony with the day's planetary ruler.
    ruler = day['ruler']
    fire_rulers = {'sun', 'mars'}
    earth_rulers = {'saturn', 'venus'}
    air_rulers = {'mercury', 'uranus'}
    water_rulers = {'moon', 'neptune', 'pluto'}
    if meta['element'] == 'fire' and ruler in fire_rulers:
        score += 12
    if meta['element'] == 'earth' and ruler in earth_rulers:
        score += 12
    if meta['element'] == 'air' and ruler in air_rulers:
        score += 12
    if meta['element'] == 'water' and ruler in water_rulers:
        score += 12

    if sign == transit_sun:
        score += 10

    # Jupiter expands mutable signs; Saturn steadies cardinal earth/air.
    if ruler == 'jupiter' and meta['modality'] == 'mutable':
        score += 8
    if ruler == 'saturn' and meta['modality'] == 'cardinal':
        score += 6

    # Full/New moons amplify water and fixed signs.
    if phase['name'] in ('Full Moon', 'New Moon'):
        if meta['element'] == 'water' or meta['modality'] == 'fixed':
            score += 8
        else:
            score += 3

    if is_mercury_retrograde(target):
        if meta['ruler'] == 'mercury' or meta['element'] == 'air':
            score -= 10
        else:
            score -= 4

    # Deterministic day-to-day wobble so scores feel alive but stable.
    wobble = ((target.toordinal() + SIGN_ORDER.index(sign) * 17) % 9) - 4
    score += wobble
    return max(18, min(96, score))


def aura_board(on_date=None):
    """Score every sign for the day and rank them."""
    target = coerce_date(on_date)
    rows = []
    for sign in SIGN_ORDER:
        profile = sign_market_profile(sign)
        score = _score_sign(sign, target)
        rows.append({
            'sign': sign,
            'glyph': profile['glyph'],
            'element': profile['element'],
            'score': score,
            'bias': profile['bias'],
            'sectors': profile['sectors'],
            'top_asset': profile['assets'][0],
        })
    rows.sort(key=lambda row: row['score'], reverse=True)
    return rows


def market_watchlist(on_date=None, limit=6):
    """Build a cosmically aligned asset watchlist for the day."""
    ranked = aura_board(on_date)
    picks = []
    seen = set()
    for row in ranked:
        profile = sign_market_profile(row['sign'])
        for asset in profile['assets']:
            if asset['symbol'] in seen:
                continue
            seen.add(asset['symbol'])
            momentum = 'rising' if row['score'] >= 70 else 'steady' if row['score'] >= 55 else 'soft'
            picks.append({
                'symbol': asset['symbol'],
                'name': asset['name'],
                'sign': row['sign'],
                'glyph': row['glyph'],
                'aura_score': row['score'],
                'momentum': momentum,
                'why': '{0} affinity ({1}) with aura {2}'.format(
                    row['sign'].title(), profile['bias'], row['score']
                ),
            })
            if len(picks) >= limit:
                return picks
    return picks


def index_picture(on_date=None):
    """Major indexes/crypto with astro sentiment overlays."""
    target = coerce_date(on_date)
    board = {row['sign']: row for row in aura_board(target)}
    picture = []
    for item in INDEX_BOARD:
        row = board[item['sign']]
        score = row['score']
        if score >= 72:
            sentiment = 'bullish tilt'
            volatility = 'elevated'
        elif score >= 58:
            sentiment = 'constructive'
            volatility = 'normal'
        elif score >= 45:
            sentiment = 'mixed'
            volatility = 'compressed'
        else:
            sentiment = 'defensive'
            volatility = 'fragile'
        picture.append({
            'symbol': item['symbol'],
            'name': item['name'],
            'sign': item['sign'],
            'glyph': row['glyph'],
            'aura_score': score,
            'sentiment': sentiment,
            'volatility': volatility,
        })
    return picture


def personal_briefing(birth_date, on_date=None, owner=None):
    """Full daily briefing for a birth date (chart + markets)."""
    target = coerce_date(on_date)
    chart = build_chart(birth_date)
    sign = chart['sun_sign']
    profile = sign_market_profile(sign)
    score = _score_sign(sign, target)
    horoscope = daily_horoscope(sign, target)
    watchlist = [
        pick for pick in market_watchlist(target, limit=9)
        if pick['sign'] == sign
    ]
    if len(watchlist) < 3:
        # Always surface the sign's own assets first.
        watchlist = []
        for asset in profile['assets']:
            watchlist.append({
                'symbol': asset['symbol'],
                'name': asset['name'],
                'sign': sign,
                'glyph': profile['glyph'],
                'aura_score': score,
                'momentum': 'rising' if score >= 70 else 'steady',
                'why': 'Direct {0} market affinity'.format(sign.title()),
            })

    return {
        'owner': owner,
        'as_of': target.isoformat(),
        'chart': chart,
        'aura_score': score,
        'horoscope': horoscope,
        'market_bias': profile['bias'],
        'sectors': profile['sectors'],
        'watchlist': watchlist,
        'disclaimer': 'For entertainment and education only. Not financial advice.',
    }


def daily_market_pulse(on_date=None):
    """Aggregate sky + market pulse used by the home screen."""
    target = coerce_date(on_date)
    phase = moon_phase(target)
    day = planetary_day(target)
    mercury = is_mercury_retrograde(target)
    station = next_mercury_station(target)
    ranked = aura_board(target)
    top = ranked[0]
    bottom = ranked[-1]

    base = 50 + int(phase['illumination'] * 20)
    if mercury:
        base -= 8
    if day['ruler'] in ('jupiter', 'venus'):
        base += 8
    if day['ruler'] in ('mars', 'saturn'):
        base += 4
    market_aura = max(20, min(92, base + ((target.toordinal() % 7) - 3)))

    if market_aura >= 70:
        stance = 'Risk-on lean'
    elif market_aura >= 55:
        stance = 'Selective engagement'
    elif market_aura >= 40:
        stance = 'Neutral / wait for clarity'
    else:
        stance = 'Capital preservation'

    return {
        'date': target.isoformat(),
        'brand': 'AstroEconomics',
        'sky': {
            'sun_sign': current_sun_sign(target),
            'moon_phase': phase,
            'planetary_day': day,
            'mercury_retrograde': mercury,
            'next_mercury_station': station,
        },
        'market_aura': market_aura,
        'stance': stance,
        'leading_sign': {
            'sign': top['sign'],
            'glyph': top['glyph'],
            'score': top['score'],
            'sectors': top['sectors'],
        },
        'lagging_sign': {
            'sign': bottom['sign'],
            'glyph': bottom['glyph'],
            'score': bottom['score'],
            'sectors': bottom['sectors'],
        },
        'watchlist': market_watchlist(target),
        'indexes': index_picture(target),
        'forecast': cosmic_weather(target, days=7),
        'aura_board': ranked,
        'disclaimer': 'For entertainment and education only. Not financial advice.',
    }
