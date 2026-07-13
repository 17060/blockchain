from datetime import datetime

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

SIGN_METADATA = {
    'aries': {'element': 'fire', 'modality': 'cardinal'},
    'taurus': {'element': 'earth', 'modality': 'fixed'},
    'gemini': {'element': 'air', 'modality': 'mutable'},
    'cancer': {'element': 'water', 'modality': 'cardinal'},
    'leo': {'element': 'fire', 'modality': 'fixed'},
    'virgo': {'element': 'earth', 'modality': 'mutable'},
    'libra': {'element': 'air', 'modality': 'cardinal'},
    'scorpio': {'element': 'water', 'modality': 'fixed'},
    'sagittarius': {'element': 'fire', 'modality': 'mutable'},
    'capricorn': {'element': 'earth', 'modality': 'cardinal'},
    'aquarius': {'element': 'air', 'modality': 'fixed'},
    'pisces': {'element': 'water', 'modality': 'mutable'},
}


def parse_birth_date(birth_date):
    """Parse YYYY-MM-DD into a date object."""
    try:
        return datetime.strptime(birth_date, '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValueError('birth_date must use YYYY-MM-DD format') from exc


def get_sun_sign(birth_date):
    """Return the western tropical sun sign for a birth date string."""
    parsed = parse_birth_date(birth_date)
    month, day = parsed.month, parsed.day

    for sign, (start_month, start_day), (end_month, end_day) in ZODIAC_SIGNS:
        if (month, day) >= (start_month, start_day) and (month, day) <= (end_month, end_day):
            return sign

    raise ValueError('Unable to determine sun sign for birth date')


def describe_sign(sign):
    """Return element and modality metadata for a zodiac sign."""
    normalized = sign.lower()
    if normalized not in SIGN_METADATA:
        raise ValueError(f'Unknown zodiac sign: {sign}')
    return {'sign': normalized, **SIGN_METADATA[normalized]}


def build_chart(birth_date):
    """Build a birth chart summary from a birth date."""
    sign = get_sun_sign(birth_date)
    return {
        'birth_date': birth_date,
        'sun_sign': sign,
        **SIGN_METADATA[sign],
    }
