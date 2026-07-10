from unittest import TestCase
from unittest.mock import MagicMock

from irc_hivemind import HiveMindCommands, format_chain_summary, parse_command


class TestParseCommand(TestCase):

    def test_parses_simple_command(self):
        assert parse_command('!mine') == ('mine', [])

    def test_parses_command_with_args(self):
        assert parse_command('!tx alice 5') == ('tx', ['alice', '5'])

    def test_ignores_non_commands(self):
        assert parse_command('hello hive') is None


class TestFormatChainSummary(TestCase):

    def test_formats_tail_blocks(self):
        chain = [
            {'index': 1, 'proof': 100, 'transactions': [], 'previous_hash': 'abc12345'},
            {'index': 2, 'proof': 352, 'transactions': [{'a': 1}], 'previous_hash': 'def67890'},
        ]
        summary = format_chain_summary(chain, limit=2)
        self.assertIn('chain length 2', summary)
        self.assertIn('#2 proof=352 txs=1', summary)


class TestHiveMindCommands(TestCase):

    def setUp(self):
        self.client = MagicMock()
        self.commands = HiveMindCommands(self.client)

    def test_help_lists_commands(self):
        reply = self.commands.help('alice', [])
        self.assertIn('!mine', reply)

    def test_mine_reports_block(self):
        self.client.mine.return_value = {'index': 4, 'message': 'New Block Forged'}
        reply = self.commands.mine('bob', [])
        self.assertIn('block #4', reply)
        self.assertIn('bob', reply)

    def test_tx_validates_amount(self):
        reply = self.commands.tx('carol', ['dave', 'nope'])
        self.assertIn('number', reply)

    def test_sync_reports_consensus(self):
        self.client.resolve.return_value = {
            'message': 'Our chain is authoritative',
            'chain': [{'index': 1}, {'index': 2}],
        }
        reply = self.commands.sync('erin', [])
        self.assertIn('authoritative', reply)
        self.assertIn('2 blocks', reply)
