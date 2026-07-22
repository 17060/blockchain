from unittest import TestCase

from blockchain import Blockchain, app
from ui import render_app


class BlockchainAstrologyTestCase(TestCase):

    def setUp(self):
        self.blockchain = Blockchain()

    def test_register_chart_transaction(self):
        index = self.blockchain.new_chart_transaction('alice', '1990-07-13')

        self.assertEqual(index, 2)
        transaction = self.blockchain.current_transactions[0]
        self.assertEqual(transaction['transaction_type'], 'birth_chart')
        self.assertEqual(transaction['sender'], 'alice')
        self.assertEqual(transaction['sun_sign'], 'cancer')
        self.assertEqual(transaction['glyph'], '♋')

    def test_get_charts_from_chain(self):
        self.blockchain.new_chart_transaction('alice', '1990-07-13')
        self.blockchain.new_block(proof=123, previous_hash='abc')
        self.blockchain.new_chart_transaction('bob', '1990-03-21')
        self.blockchain.new_block(proof=456, previous_hash='def')

        charts = self.blockchain.get_charts()
        self.assertEqual(len(charts), 2)
        self.assertEqual(charts[0]['sender'], 'alice')
        self.assertEqual(charts[1]['sun_sign'], 'aries')

    def test_invalid_chart_date_raises(self):
        with self.assertRaises(ValueError):
            self.blockchain.new_chart_transaction('alice', 'invalid-date')


class AppRoutesTestCase(TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_home_serves_app(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AstroEconomics', response.data)
        self.assertIn(b'app is running', response.data)
        self.assertIn(b'Market aura', response.data)
        self.assertIn(b'Your chart briefing', response.data)
        self.assertIn(b'Cosmic watchlist', response.data)
        self.assertIn(b'Seven-day sky', response.data)
        self.assertIn(b'<form method="post"', response.data)
        # No client-side boot dependency.
        self.assertNotIn(b'<script>', response.data)

    def test_html_404(self):
        response = self.client.get('/does-not-exist')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Page not found', response.data)
        self.assertIn(b'AstroEconomics', response.data)

    def test_home_form_briefing(self):
        response = self.client.post('/', data={
            'owner': 'alice',
            'birth_date': '1990-07-13',
            'register': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cancer', response.data)
        self.assertIn(b'Registered in block', response.data)
        self.assertIn(b'alice', response.data)

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['status'], 'ok')

    def test_pulse_endpoint(self):
        response = self.client.get('/astroeconomics/pulse?date=2026-07-22')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['brand'], 'AstroEconomics')
        self.assertTrue(payload['watchlist'])

    def test_briefing_and_registry(self):
        response = self.client.post(
            '/astroeconomics/briefing',
            json={
                'owner': 'alice',
                'birth_date': '1990-07-13',
                'date': '2026-07-22',
                'register': True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['chart']['sun_sign'], 'cancer')
        self.assertTrue(payload['registered'])

        charts = self.client.get('/astrology/charts').get_json()['charts']
        self.assertTrue(any(chart['sender'] == 'alice' for chart in charts))

    def test_sign_lookup_includes_market_profile(self):
        response = self.client.get('/astrology/sign?birth_date=1990-01-10')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['sun_sign'], 'capricorn')
        self.assertIn('Infrastructure', payload['sectors'])

    def test_transaction_missing_body_is_json_error(self):
        response = self.client.post('/transactions/new')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())


class UiRenderTestCase(TestCase):

    def test_render_app_includes_core_copy(self):
        html = render_app(pulse=None, charts=[], briefing=None, error='boom')
        self.assertIn('AstroEconomics', html)
        self.assertIn('boom', html)
        self.assertIn('<form method="post"', html)
