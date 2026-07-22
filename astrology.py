"""Western tropical astrology helpers used by the AstroEconomics app."""

from datetime import date, datetime, timedelta
from math import cos, floor, pi

ZODIAC_SIGNS = (
    ('capricorn', (1, 1), (1, 19)),
    ('aquarius', (1, 20), (2, 18)),
    ('pisces', (2, 19), (3, 20)),
    ('aries', (3, 21), (4, 19)),
    ('taurus', (4, 20), (5, 20)),
    ('gemini', (5, 21), (6, 20)),
    ('cancer', (6, 21), (7, 22)),
    ('leo', (7, 23), (8, 22)),
    ('virgo', (8, 23), (9, 22)),
    ('libra', (9, 23), (10, 22)),
    ('scorpio', (10, 23), (11, 21)),
    ('sagittarius', (11, 22), (12, 21)),
    ('capricorn', (12, 22), (12, 31)),
)

SIGN_ORDER = (
    'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
    'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces',
)

SIGN_METADATA = {
    'aries': {
        'element': 'fire',
        'modality': 'cardinal',
        'ruler': 'mars',
        'glyph': '♈',
        'keywords': ('initiative', 'velocity', 'courage'),
    },
    'taurus': {
        'element': 'earth',
        'modality': 'fixed',
        'ruler': 'venus',
        'glyph': '♉',
        'keywords': ('stability', 'value', 'patience'),
    },
    'gemini': {
        'element': 'air',
        'modality': 'mutable',
        'ruler': 'mercury',
        'glyph': '♊',
        'keywords': ('information', 'adaptability', 'trade'),
    },
    'cancer': {
        'element': 'water',
        'modality': 'cardinal',
        'ruler': 'moon',
        'glyph': '♋',
        'keywords': ('protection', 'home', 'sentiment'),
    },
    'leo': {
        'element': 'fire',
        'modality': 'fixed',
        'ruler': 'sun',
        'glyph': '♌',
        'keywords': ('confidence', 'visibility', 'leadership'),
    },
    'virgo': {
        'element': 'earth',
        'modality': 'mutable',
        'ruler': 'mercury',
        'glyph': '♍',
        'keywords': ('precision', 'service', 'analysis'),
    },
    'libra': {
        'element': 'air',
        'modality': 'cardinal',
        'ruler': 'venus',
        'glyph': '♎',
        'keywords': ('balance', 'contracts', 'aesthetics'),
    },
    'scorpio': {
        'element': 'water',
        'modality': 'fixed',
        'ruler': 'pluto',
        'glyph': '♏',
        'keywords': ('intensity', 'transformation', 'risk'),
    },
    'sagittarius': {
        'element': 'fire',
        'modality': 'mutable',
        'ruler': 'jupiter',
        'glyph': '♐',
        'keywords': ('expansion', 'optimism', 'exploration'),
    },
    'capricorn': {
        'element': 'earth',
        'modality': 'cardinal',
        'ruler': 'saturn',
        'glyph': '♑',
        'keywords': ('discipline', 'structure', 'longevity'),
    },
    'aquarius': {
        'element': 'air',
        'modality': 'fixed',
        'ruler': 'uranus',
        'glyph': '♒',
        'keywords': ('innovation', 'networks', 'disruption'),
    },
    'pisces': {
        'element': 'water',
        'modality': 'mutable',
        'ruler': 'neptune',
        'glyph': '♓',
        'keywords': ('intuition', 'liquidity', 'imagination'),
    },
}

PLANETARY_DAYS = (
    ('sunday', 'sun'),
    ('monday', 'moon'),
    ('tuesday', 'mars'),
    ('wednesday', 'mercury'),
    ('thursday', 'jupiter'),
    ('friday', 'venus'),
    ('saturday', 'saturn'),
)

# Approximate Mercury retrograde windows for 2025–2027 (UTC date ranges).
MERCURY_RETROGRADE_WINDOWS = (
    (date(2025, 3, 15), date(2025, 4, 7)),
    (date(2025, 7, 18), date(2025, 8, 11)),
    (date(2025, 11, 9), date(2025, 11, 29)),
    (date(2026, 2, 26), date(2026, 3, 20)),
    (date(2026, 6, 29), date(2026, 7, 23)),
    (date(2026, 10, 24), date(2026, 11, 13)),
    (date(2027, 2, 9), date(2027, 3, 3)),
    (date(2027, 6, 10), date(2027, 7, 4)),
    (date(2027, 10, 7), date(2027, 10, 28)),
)

# Known new moon near J2000 used for synodic-phase estimates.
_KNOWN_NEW_MOON = date(2000, 1, 6)
_SYNODIC_MONTH = 29.530588853

HOROSCOPE_TEMPLATES = {
    'fire': (
        'Momentum favors bold entries. Channel {keyword} into one clear decision '
        'instead of scattering attention across every ticker.'
    ),
    'earth': (
        'Build on what already holds value. {keyword_title} beats speculation — '
        'review costs, collateral, and slow-compounding positions.'
    ),
    'air': (
        'Information moves markets today. Stay light on your feet and let '
        '{keyword} guide which narratives deserve capital.'
    ),
    'water': (
        'Sentiment swings more than fundamentals. Trust {keyword}, size smaller, '
        'and protect emotional capital as carefully as cash.'
    ),
}


def parse_birth_date(birth_date):
    """Parse YYYY-MM-DD into a date object."""
    try:
        return datetime.strptime(birth_date, '%Y-%m-%d').date()
    except (TypeError, ValueError) as exc:
        raise ValueError('birth_date must use YYYY-MM-DD format') from exc


def coerce_date(value=None):
    """Accept a date, YYYY-MM-DD string, or default to today."""
    if value is None:
        return date.today()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return parse_birth_date(value)


def get_sun_sign(birth_date):
    """Return the western tropical sun sign for a birth date string or date."""
    parsed = coerce_date(birth_date)
    month, day = parsed.month, parsed.day

    for sign, (start_month, start_day), (end_month, end_day) in ZODIAC_SIGNS:
        if (month, day) >= (start_month, start_day) and (month, day) <= (end_month, end_day):
            return sign

    raise ValueError('Unable to determine sun sign for birth date')


def describe_sign(sign):
    """Return element and modality metadata for a zodiac sign."""
    normalized = sign.lower().strip()
    if normalized not in SIGN_METADATA:
        raise ValueError('Unknown zodiac sign: {0}'.format(sign))
    meta = SIGN_METADATA[normalized]
    return {
        'sign': normalized,
        'element': meta['element'],
        'modality': meta['modality'],
        'ruler': meta['ruler'],
        'glyph': meta['glyph'],
        'keywords': list(meta['keywords']),
    }


def build_chart(birth_date):
    """Build a birth chart summary from a birth date."""
    parsed = coerce_date(birth_date)
    sign = get_sun_sign(parsed)
    meta = describe_sign(sign)
    return {
        'birth_date': parsed.isoformat(),
        'sun_sign': sign,
        'element': meta['element'],
        'modality': meta['modality'],
        'ruler': meta['ruler'],
        'glyph': meta['glyph'],
        'keywords': meta['keywords'],
    }


def moon_age_days(on_date=None):
    """Approximate age of the moon in days for the given date."""
    target = coerce_date(on_date)
    days = (target - _KNOWN_NEW_MOON).days + 0.5
    return days % _SYNODIC_MONTH


def moon_phase(on_date=None):
    """Return a readable lunar phase plus illumination fraction."""
    age = moon_age_days(on_date)
    illumination = (1 - cos(2 * pi * age / _SYNODIC_MONTH)) / 2
    phase_index = int(floor((age / _SYNODIC_MONTH) * 8 + 0.5)) % 8
    names = (
        'New Moon',
        'Waxing Crescent',
        'First Quarter',
        'Waxing Gibbous',
        'Full Moon',
        'Waning Gibbous',
        'Last Quarter',
        'Waning Crescent',
    )
    return {
        'name': names[phase_index],
        'age_days': round(age, 2),
        'illumination': round(illumination, 3),
        'cycle_progress': round(age / _SYNODIC_MONTH, 3),
    }


def planetary_day(on_date=None):
    """Return classical planetary day ruler for the given date."""
    target = coerce_date(on_date)
    # date.weekday(): Monday=0 ... Sunday=6 → remap to PLANETARY_DAYS index.
    index = (target.weekday() + 1) % 7
    day_name, ruler = PLANETARY_DAYS[index]
    return {
        'date': target.isoformat(),
        'weekday': day_name,
        'ruler': ruler,
    }


def is_mercury_retrograde(on_date=None):
    """Return whether Mercury is retrograde on the given date."""
    target = coerce_date(on_date)
    for start, end in MERCURY_RETROGRADE_WINDOWS:
        if start <= target <= end:
            return True
    return False


def next_mercury_station(on_date=None):
    """Return the next Mercury retrograde start or end after on_date."""
    target = coerce_date(on_date)
    for start, end in MERCURY_RETROGRADE_WINDOWS:
        if target < start:
            return {'event': 'retrograde_begins', 'date': start.isoformat()}
        if start <= target <= end:
            return {'event': 'retrograde_ends', 'date': end.isoformat()}
    return None


def current_sun_sign(on_date=None):
    """Sun sign for a calendar date (transit sun)."""
    return get_sun_sign(coerce_date(on_date))


def daily_horoscope(sign, on_date=None):
    """Generate a short personalized financial-leaning horoscope."""
    meta = describe_sign(sign)
    phase = moon_phase(on_date)
    day = planetary_day(on_date)
    keyword = meta['keywords'][0]
    template = HOROSCOPE_TEMPLATES[meta['element']]
    body = template.format(keyword=keyword, keyword_title=keyword.title())
    mercury = is_mercury_retrograde(on_date)

    tone = 'steady'
    if phase['name'] in ('Full Moon', 'New Moon'):
        tone = 'volatile'
    elif mercury:
        tone = 'revisional'
    elif day['ruler'] in ('jupiter', 'venus'):
        tone = 'expansive'

    return {
        'sign': meta['sign'],
        'glyph': meta['glyph'],
        'date': coerce_date(on_date).isoformat(),
        'tone': tone,
        'headline': '{0} {1}: {2} day'.format(
            meta['glyph'], meta['sign'].title(), tone
        ),
        'reading': body,
        'moon_phase': phase['name'],
        'day_ruler': day['ruler'],
        'mercury_retrograde': mercury,
    }


def cosmic_weather(on_date=None, days=7):
    """Return a short multi-day cosmic forecast."""
    start = coerce_date(on_date)
    forecast = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        phase = moon_phase(day)
        ruler = planetary_day(day)
        mercury = is_mercury_retrograde(day)
        intensity = 55
        intensity += int(phase['illumination'] * 25)
        if mercury:
            intensity += 10
        if phase['name'] in ('Full Moon', 'New Moon'):
            intensity += 12
        if ruler['ruler'] in ('mars', 'uranus'):
            intensity += 8
        intensity = min(100, intensity)
        forecast.append({
            'date': day.isoformat(),
            'weekday': ruler['weekday'],
            'sun_sign': current_sun_sign(day),
            'moon_phase': phase['name'],
            'day_ruler': ruler['ruler'],
            'mercury_retrograde': mercury,
            'intensity': intensity,
            'note': _forecast_note(phase['name'], ruler['ruler'], mercury),
        })
    return forecast


def _forecast_note(phase_name, ruler, mercury):
    if mercury and phase_name in ('Full Moon', 'New Moon'):
        return 'High-noise window — double-check fills and headlines.'
    if mercury:
        return 'Mercury retrograde: favor reviews, hedges, and rebalancing.'
    if phase_name == 'Full Moon':
        return 'Full Moon pressure — expect sharper swings and profit-taking.'
    if phase_name == 'New Moon':
        return 'New Moon reset — good for framing fresh theses, not chasing.'
    if ruler == 'jupiter':
        return 'Jupiter day — bias toward expansion and international themes.'
    if ruler == 'saturn':
        return 'Saturn day — favor discipline, blue chips, and risk limits.'
    if ruler == 'venus':
        return 'Venus day — consumer, luxury, and quality factors can lead.'
    if ruler == 'mars':
        return 'Mars day — energy and high-beta names may move first.'
    return 'Quiet lunar weather — let process, not impulse, set the pace.'
