from unittest import TestCase

from astrology import build_chart, get_sun_sign, parse_birth_date


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
