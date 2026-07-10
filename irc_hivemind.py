"""
IRC Hive Mind — a collective IRC interface to a blockchain node.

Everyone in the channel shares one node's view of the chain. Commands are
broadcast to the hive; consensus syncs with peer nodes on the network.
"""

import argparse
import json
import re
import socket
import ssl
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

import requests


COMMAND_PREFIX = '!'
MAX_MESSAGE_LENGTH = 400


def parse_command(message: str) -> Optional[Tuple[str, List[str]]]:
    """Parse a hive command from a channel message."""
    message = message.strip()
    if not message.startswith(COMMAND_PREFIX):
        return None

    parts = message[len(COMMAND_PREFIX):].split()
    if not parts:
        return None

    return parts[0].lower(), parts[1:]


def format_chain_summary(chain: List[dict], limit: int = 3) -> str:
    """Summarize the tail of the chain for IRC."""
    if not chain:
        return 'chain is empty'

    blocks = chain[-limit:]
    lines = [f'chain length {len(chain)} (showing last {len(blocks)})']
    for block in blocks:
        tx_count = len(block.get('transactions', []))
        lines.append(
            f"#{block['index']} proof={block['proof']} txs={tx_count} "
            f"hash={block['previous_hash'][:8]}..."
        )
    return ' | '.join(lines)


class BlockchainClient:
    """HTTP client for the local blockchain node."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_chain(self) -> dict:
        response = requests.get(f'{self.base_url}/chain', timeout=10)
        response.raise_for_status()
        return response.json()

    def mine(self) -> dict:
        response = requests.get(f'{self.base_url}/mine', timeout=120)
        response.raise_for_status()
        return response.json()

    def new_transaction(self, sender: str, recipient: str, amount: float) -> dict:
        payload = {'sender': sender, 'recipient': recipient, 'amount': amount}
        response = requests.post(
            f'{self.base_url}/transactions/new',
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def register_nodes(self, nodes: List[str]) -> dict:
        response = requests.post(
            f'{self.base_url}/nodes/register',
            json={'nodes': nodes},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def resolve(self) -> dict:
        response = requests.get(f'{self.base_url}/nodes/resolve', timeout=30)
        response.raise_for_status()
        return response.json()


class HiveMindCommands:
    """Command handlers that turn IRC input into blockchain actions."""

    def __init__(self, client: BlockchainClient):
        self.client = client
        self.handlers: Dict[str, Callable[[str, List[str]], str]] = {
            'help': self.help,
            'status': self.status,
            'mine': self.mine,
            'chain': self.chain,
            'tx': self.tx,
            'peer': self.peer,
            'sync': self.sync,
        }

    def dispatch(self, nick: str, command: str, args: List[str]) -> str:
        handler = self.handlers.get(command)
        if handler is None:
            return f'unknown command `{command}` — try {COMMAND_PREFIX}help'
        try:
            return handler(nick, args)
        except requests.RequestException as exc:
            return f'node unreachable: {exc}'

    def help(self, nick: str, args: List[str]) -> str:
        return (
            'hive commands: '
            f'{COMMAND_PREFIX}status, {COMMAND_PREFIX}mine, {COMMAND_PREFIX}chain [n], '
            f'{COMMAND_PREFIX}tx <recipient> <amount>, {COMMAND_PREFIX}peer <url>, '
            f'{COMMAND_PREFIX}sync'
        )

    def status(self, nick: str, args: List[str]) -> str:
        data = self.client.get_chain()
        pending = 0
        if data['chain']:
            # Pending txs live on the node but are not exposed by the API;
            # report chain length as the hive's shared state.
            pass
        return f'hive state: {data["length"]} blocks'

    def mine(self, nick: str, args: List[str]) -> str:
        data = self.client.mine()
        block_index = data.get('index', '?')
        return f'{nick} forged block #{block_index} — the hive grows'

    def chain(self, nick: str, args: List[str]) -> str:
        limit = 3
        if args:
            try:
                limit = max(1, min(10, int(args[0])))
            except ValueError:
                return 'usage: !chain [count]'

        data = self.client.get_chain()
        return format_chain_summary(data['chain'], limit=limit)

    def tx(self, nick: str, args: List[str]) -> str:
        if len(args) < 2:
            return 'usage: !tx <recipient> <amount>'

        recipient = args[0]
        try:
            amount = float(args[1])
        except ValueError:
            return 'amount must be a number'

        if amount <= 0:
            return 'amount must be positive'

        data = self.client.new_transaction(nick, recipient, amount)
        return f'{nick} queued payment: {data.get("message", "ok")}'

    def peer(self, nick: str, args: List[str]) -> str:
        if not args:
            return 'usage: !peer <http://host:port>'

        data = self.client.register_nodes(args)
        nodes = ', '.join(data.get('total_nodes', []))
        return f'{nick} linked peer — hive nodes: {nodes or "none"}'

    def sync(self, nick: str, args: List[str]) -> str:
        data = self.client.resolve()
        message = data.get('message', 'consensus complete')
        length = len(data.get('new_chain', data.get('chain', [])))
        return f'hive consensus: {message} ({length} blocks)'


class IRCHiveMind:
    """Minimal IRC client that exposes the blockchain to a channel."""

    def __init__(
        self,
        server: str,
        port: int,
        channel: str,
        nickname: str,
        blockchain_url: str,
        use_ssl: bool = False,
        password: Optional[str] = None,
    ):
        self.server = server
        self.port = port
        self.channel = channel if channel.startswith('#') else f'#{channel}'
        self.nickname = nickname
        self.password = password
        self.use_ssl = use_ssl
        self.commands = HiveMindCommands(BlockchainClient(blockchain_url))
        self._socket: Optional[socket.socket] = None
        self._running = False

    def _send(self, message: str) -> None:
        if not self._socket:
            return
        payload = f'{message}\r\n'.encode('utf-8')
        self._socket.sendall(payload)

    def _privmsg(self, target: str, text: str) -> None:
        if len(text) <= MAX_MESSAGE_LENGTH:
            self._send(f'PRIVMSG {target} :{text}')
            return

        chunk = text[:MAX_MESSAGE_LENGTH]
        self._send(f'PRIVMSG {target} :{chunk}')
        self._privmsg(target, text[MAX_MESSAGE_LENGTH:])

    def _handle_line(self, line: str) -> None:
        if line.startswith('PING'):
            self._send(line.replace('PING', 'PONG', 1))
            return

        match = re.match(
            r':([^!]+)!.* PRIVMSG ([^ ]+) :(.*)',
            line,
        )
        if not match:
            return

        nick, target, message = match.groups()
        if target.lower() != self.channel.lower():
            return

        parsed = parse_command(message)
        if not parsed:
            return

        command, args = parsed
        reply = self.commands.dispatch(nick, command, args)
        self._privmsg(self.channel, f'{nick}: {reply}')

    def _reader_loop(self) -> None:
        buffer = ''
        while self._running and self._socket:
            try:
                data = self._socket.recv(4096)
            except OSError:
                break

            if not data:
                break

            buffer += data.decode('utf-8', errors='replace')
            while '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)
                if line:
                    self._handle_line(line)

    def connect(self) -> None:
        raw_socket = socket.create_connection((self.server, self.port), timeout=30)
        if self.use_ssl:
            context = ssl.create_default_context()
            self._socket = context.wrap_socket(raw_socket, server_hostname=self.server)
        else:
            self._socket = raw_socket

        self._send(f'NICK {self.nickname}')
        self._send(f'USER {self.nickname} 0 * :IRC Hive Mind')
        if self.password:
            self._send(f'PASS {self.password}')
        self._send(f'JOIN {self.channel}')

        self._running = True
        reader = threading.Thread(target=self._reader_loop, daemon=True)
        reader.start()

        while self._running and reader.is_alive():
            time.sleep(1)

    def stop(self) -> None:
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(description='IRC Hive Mind blockchain bridge')
    parser.add_argument('--server', default='irc.libera.chat', help='IRC server hostname')
    parser.add_argument('--port', type=int, default=6697, help='IRC server port')
    parser.add_argument('--channel', default='#hivemind', help='IRC channel to join')
    parser.add_argument('--nick', default='HiveMind', help='IRC nickname')
    parser.add_argument(
        '--blockchain',
        default='http://127.0.0.1:5000',
        help='URL of the local blockchain node',
    )
    parser.add_argument('--ssl', action='store_true', help='Use TLS (recommended)')
    parser.add_argument('--password', help='Optional IRC server password')
    args = parser.parse_args()

    bot = IRCHiveMind(
        server=args.server,
        port=args.port,
        channel=args.channel,
        nickname=args.nick,
        blockchain_url=args.blockchain,
        use_ssl=args.ssl,
        password=args.password,
    )

    print(f'connecting {args.nick} to {args.server}:{args.port}{args.channel}')
    bot.connect()


if __name__ == '__main__':
    main()
