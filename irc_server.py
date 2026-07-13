"""
Minimal IRC server for local and LAN use.

Designed for testing and small chat rooms. Connect from iOS clients such as
LimeChat, Palaver, or Colloquy over your local network.
"""

import argparse
import asyncio
import logging
import socket
from collections import defaultdict

logger = logging.getLogger(__name__)


def _prefix(nick, user="user", host="localhost"):
    return f"{nick}!{user}@{host}"


def _format_message(prefix, command, params):
    if prefix:
        line = f":{prefix} {command}"
    else:
        line = command

    if not params:
        return line

    if " " in params[-1] or params[-1].startswith(":"):
        trailing = params[-1]
        middle = params[:-1]
        if middle:
            return f"{line} {' '.join(middle)} {trailing}"
        return f"{line} {trailing}"

    return f"{line} {' '.join(params)}"


class IRCClient:
    def __init__(self, reader, writer, server):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.nick = None
        self.user = None
        self.realname = ""
        self.host = writer.get_extra_info("peername")[0]
        self.registered = False
        self.channels = set()

    async def send(self, command, params=None, prefix=None):
        line = _format_message(prefix, command, params or [])
        self.writer.write(f"{line}\r\n".encode("utf-8"))
        try:
            await self.writer.drain()
        except (ConnectionResetError, BrokenPipeError, ConnectionError):
            pass

    async def close(self, message=None):
        if message:
            await self.send("ERROR", [f":{message}"])
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except ConnectionError:
            pass

    async def handle_line(self, line):
        if not line:
            return

        if line[0] == ":":
            _, _, line = line.partition(" ")

        parts = line.split(" ")
        command = parts[0].upper()
        params = parts[1:]

        if command == "NICK":
            await self._handle_nick(params)
        elif command == "USER":
            await self._handle_user(params)
        elif command == "JOIN":
            await self._handle_join(params)
        elif command == "PART":
            await self._handle_part(params)
        elif command == "PRIVMSG":
            await self._handle_privmsg(params)
        elif command == "PING":
            await self._handle_ping(params)
        elif command == "QUIT":
            await self._handle_quit(params)
        elif command == "MODE":
            await self._handle_mode(params)
        elif command == "CAP":
            await self.send("CAP", ["*", "NAK", ":"])
        elif command == "WHOIS":
            await self._handle_whois(params)
        else:
            await self.send(
                "421",
                [self.nick or "*", command, ":Unknown command"],
                prefix=self.server.name,
            )

    async def _maybe_register(self):
        if self.registered or not self.nick or not self.user:
            return

        self.registered = True
        await self.send(
            "001",
            [self.nick, f":Welcome to {self.server.name}"],
            prefix=self.server.name,
        )
        await self.send(
            "002",
            [self.nick, f":Your host is {self.server.name}"],
            prefix=self.server.name,
        )
        await self.send(
            "003",
            [self.nick, ":This server was created for local testing"],
            prefix=self.server.name,
        )
        await self.send(
            "004",
            [self.nick, self.server.name, "1.0", "o", "o"],
            prefix=self.server.name,
        )
        await self.send(
            "375",
            [self.nick, f":- {self.server.name} Message of the day -"],
            prefix=self.server.name,
        )
        await self.send(
            "372",
            [self.nick, ":Connect from iOS using your computer's LAN IP."],
            prefix=self.server.name,
        )
        await self.send(
            "376",
            [self.nick, ":End of /MOTD command."],
            prefix=self.server.name,
        )

    async def _handle_nick(self, params):
        if not params:
            await self.send("431", [":No nickname given"], prefix=self.server.name)
            return

        nick = params[0]
        if any(client.nick == nick for client in self.server.clients if client is not self):
            await self.send("433", ["*", nick, ":Nickname is already in use"], prefix=self.server.name)
            return

        old_nick = self.nick
        self.nick = nick
        if old_nick and old_nick != nick:
            await self.server.broadcast(
                "NICK",
                [nick],
                prefix=_prefix(old_nick, self.user or "user", self.host),
            )
        await self._maybe_register()

    async def _handle_user(self, params):
        if len(params) < 4:
            return

        self.user = params[0]
        self.realname = params[3][1:] if params[3].startswith(":") else params[3]
        await self._maybe_register()

    async def _handle_join(self, params):
        if not self.registered:
            await self.send("451", [":You have not registered"], prefix=self.server.name)
            return
        if not params:
            return

        channel = params[0]
        if not channel.startswith("#"):
            await self.send("403", [channel, ":No such channel"], prefix=self.server.name)
            return

        self.channels.add(channel)
        self.server.channels[channel].add(self)
        await self.send(
            "JOIN",
            [channel],
            prefix=_prefix(self.nick, self.user, self.host),
        )
        members = sorted(client.nick for client in self.server.channels[channel] if client.nick)
        await self.send(
            "353",
            [self.nick, "=", channel, f":{' '.join(members)}"],
            prefix=self.server.name,
        )
        await self.send(
            "366",
            [self.nick, channel, ":End of /NAMES list."],
            prefix=self.server.name,
        )
        await self.server.broadcast_to_channel(
            channel,
            "JOIN",
            [channel],
            prefix=_prefix(self.nick, self.user, self.host),
            skip=self,
        )

    async def _handle_part(self, params):
        if not params:
            return

        channel = params[0]
        if channel not in self.channels:
            return

        self.channels.discard(channel)
        self.server.channels[channel].discard(self)
        await self.send(
            "PART",
            [channel],
            prefix=_prefix(self.nick, self.user, self.host),
        )
        await self.server.broadcast_to_channel(
            channel,
            "PART",
            [channel],
            prefix=_prefix(self.nick, self.user, self.host),
            skip=self,
        )

    async def _handle_privmsg(self, params):
        if not self.registered or len(params) < 2:
            return

        target = params[0]
        message = " ".join(params[1:])
        if message.startswith(":"):
            message = message[1:]

        if target.startswith("#"):
            if target not in self.channels:
                await self.send("404", [target, ":Cannot send to channel"], prefix=self.server.name)
                return
            await self.server.broadcast_to_channel(
                target,
                "PRIVMSG",
                [target, f":{message}"],
                prefix=_prefix(self.nick, self.user, self.host),
            )
        else:
            recipient = self.server.find_client(target)
            if recipient:
                await recipient.send(
                    "PRIVMSG",
                    [self.nick, f":{message}"],
                    prefix=_prefix(self.nick, self.user, self.host),
                )

    async def _handle_ping(self, params):
        token = params[0] if params else self.server.name
        await self.send("PONG", [token], prefix=self.server.name)

    async def _handle_quit(self, params):
        reason = " ".join(params)[1:] if params and params[0].startswith(":") else "Client quit"
        await self.server.remove_client(self, reason=reason)
        await self.close()

    async def _handle_mode(self, params):
        if not params:
            return
        if len(params) == 1 and params[0].startswith("#"):
            await self.send("324", [self.nick, params[0], "+"], prefix=self.server.name)
            return
        if len(params) >= 2 and params[0].startswith("#"):
            await self.send("MODE", params, prefix=self.server.name)

    async def _handle_whois(self, params):
        if not params:
            return

        target = self.server.find_client(params[0])
        if not target:
            await self.send("401", [params[0], ":No such nick/channel"], prefix=self.server.name)
            return

        await self.send(
            "311",
            [self.nick, target.nick, target.user or "user", target.host, "*", f":{target.realname}"],
            prefix=self.server.name,
        )
        channels = ",".join(sorted(target.channels)) or "*"
        await self.send(
            "319",
            [self.nick, target.nick, f":{channels}"],
            prefix=self.server.name,
        )
        await self.send("318", [self.nick, target.nick, ":End of /WHOIS list."], prefix=self.server.name)

    async def read_loop(self):
        buffer = ""
        try:
            while True:
                data = await self.reader.read(4096)
                if not data:
                    break

                buffer += data.decode("utf-8", errors="replace")
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    await self.handle_line(line)
        except (ConnectionResetError, asyncio.IncompleteReadError):
            pass
        finally:
            await self.server.remove_client(self)


class IRCServer:
    def __init__(self, host="0.0.0.0", port=6667, name=None):
        self.host = host
        self.port = port
        self.name = name or socket.gethostname()
        self.clients = set()
        self.channels = defaultdict(set)

    def find_client(self, nick):
        for client in self.clients:
            if client.nick and client.nick.lower() == nick.lower():
                return client
        return None

    async def broadcast(self, command, params, prefix=None, skip=None):
        for client in list(self.clients):
            if client is skip or not client.registered:
                continue
            await client.send(command, params, prefix=prefix)

    async def broadcast_to_channel(self, channel, command, params, prefix=None, skip=None):
        for client in list(self.channels[channel]):
            if client is skip or not client.registered:
                continue
            await client.send(command, params, prefix=prefix)

    async def remove_client(self, client, reason="Client quit"):
        if client not in self.clients:
            return

        self.clients.discard(client)
        for channel in list(client.channels):
            client.channels.discard(channel)
            self.channels[channel].discard(client)
            if client.nick:
                await self.broadcast_to_channel(
                    channel,
                    "QUIT",
                    [f":{reason}"],
                    prefix=_prefix(client.nick, client.user or "user", client.host),
                    skip=client,
                )

    async def handle_client(self, reader, writer):
        client = IRCClient(reader, writer, self)
        self.clients.add(client)
        logger.info("Client connected from %s", client.host)
        await client.read_loop()
        logger.info("Client disconnected from %s", client.host)

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        logger.info("IRC server listening on %s", addresses)
        async with server:
            await server.serve_forever()


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="Run a minimal IRC server for iOS clients.")
    parser.add_argument("--host", default="0.0.0.0", help="Address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6667, help="Port to listen on (default: 6667)")
    parser.add_argument("--name", default=None, help="Server name shown to clients")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    lan_ip = get_lan_ip()
    print(f"IRC server starting on port {args.port}")
    print(f"Connect from iOS using server: {lan_ip}  port: {args.port}")
    print("Recommended iOS apps: LimeChat, Palaver, Colloquy")

    irc_server = IRCServer(host=args.host, port=args.port, name=args.name)
    try:
        asyncio.run(irc_server.start())
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
