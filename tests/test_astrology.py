from datetime import date
from unittest import TestCase

from astrology import (
    build_chart,
    cosmic_weather,
    daily_horoscope,
    get_sun_sign,
    is_mercury_retrograde,
    moon_phase,
    parse_birth_date,
    planetary_day,
)


class AstrologyTestCase(TestCase):

    def test_parse_birth_date(self):
        parsed = parse_birth_date('1990-05-15')
        self.assertEqual(parsed.year, 1990)
        self.assertEqual(parsed.month, 5)
        self.assertEqual(parsed.day, 15)

    def test_invalid_birth_date(self):
        with self.assertRaises(ValueError):
            parse_birth_date('05-15-1990')

    def test_sun_sign_for_cancer(self):
        self.assertEqual(get_sun_sign('1990-07-13'), 'cancer')

    def test_sun_sign_for_capricorn_december(self):
        self.assertEqual(get_sun_sign('1990-12-25'), 'capricorn')

    def test_sun_sign_for_capricorn_january(self):
        self.assertEqual(get_sun_sign('1990-01-10'), 'capricorn')

    def test_build_chart_includes_metadata(self):
        chart = build_chart('1990-07-13')
        self.assertEqual(chart['sun_sign'], 'cancer')
        self.assertEqual(chart['element'], 'water')
        self.assertEqual(chart['modality'], 'cardinal')
        self.assertEqual(chart['glyph'], '♋')
        self.assertIn('protection', chart['keywords'])

    def test_moon_phase_has_name(self):
        phase = moon_phase(date(2026, 7, 22))
        self.assertIn('name', phase)
        self.assertGreaterEqual(phase['illumination'], 0)
        self.assertLessEqual(phase['illumination'], 1)

    def test_planetary_day_wednesday_is_mercury(self):
        # 2026-07-22 is a Wednesday
        day = planetary_day(date(2026, 7, 22))
        self.assertEqual(day['weekday'], 'wednesday')
        self.assertEqual(day['ruler'], 'mercury')

    def test_mercury_retrograde_window(self):
        self.assertTrue(is_mercury_retrograde(date(2026, 7, 22)))
        self.assertFalse(is_mercury_retrograde(date(2026, 8, 1)))

    def test_daily_horoscope(self):
        reading = daily_horoscope('leo', date(2026, 7, 22))
        self.assertEqual(reading['sign'], 'leo')
        self.assertTrue(reading['reading'])

    def test_cosmic_weather_length(self):
        forecast = cosmic_weather(date(2026, 7, 22), days=7)
        self.assertEqual(len(forecast), 7)
        self.assertIn('intensity', forecast[0])
