from datetime import date
from unittest import TestCase

from astroeconomics import (
    daily_market_pulse,
    market_watchlist,
    personal_briefing,
    sign_market_profile,
)


class AstroEconomicsTestCase(TestCase):

    def test_sign_market_profile(self):
        profile = sign_market_profile('aquarius')
        self.assertEqual(profile['sign'], 'aquarius')
        self.assertIn('Technology', profile['sectors'])
        self.assertTrue(profile['assets'])

    def test_watchlist_not_empty(self):
        picks = market_watchlist(date(2026, 7, 22), limit=6)
        self.assertEqual(len(picks), 6)
        self.assertIn('symbol', picks[0])
        self.assertIn('aura_score', picks[0])

    def test_daily_market_pulse(self):
        pulse = daily_market_pulse(date(2026, 7, 22))
        self.assertEqual(pulse['brand'], 'AstroEconomics')
        self.assertEqual(pulse['date'], '2026-07-22')
        self.assertTrue(20 <= pulse['market_aura'] <= 92)
        self.assertEqual(len(pulse['forecast']), 7)
        self.assertEqual(len(pulse['aura_board']), 12)
        self.assertTrue(pulse['sky']['mercury_retrograde'])

    def test_personal_briefing(self):
        briefing = personal_briefing('1990-07-13', on_date=date(2026, 7, 22), owner='alice')
        self.assertEqual(briefing['owner'], 'alice')
        self.assertEqual(briefing['chart']['sun_sign'], 'cancer')
        self.assertTrue(briefing['watchlist'])
        self.assertIn('horoscope', briefing)
