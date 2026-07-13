import asyncio
import unittest

from irc_server import IRCServer, get_lan_ip


async def _read_line(reader):
    data = await reader.readuntil(b"\r\n")
    return data.decode("utf-8").strip()


async def _register(reader, nick="alice"):
    while True:
        line = await _read_line(reader)
        if " 001 " in line:
            return line


async def _drain_motd(reader):
    while True:
        line = await _read_line(reader)
        if " 376 " in line:
            return


async def _wait_for_line(reader, predicate, limit=20):
    for _ in range(limit):
        line = await asyncio.wait_for(_read_line(reader), timeout=2)
        if predicate(line):
            return line
    return None


class IRCServerTest(unittest.TestCase):
    def test_get_lan_ip_returns_string(self):
        ip = get_lan_ip()
        self.assertIsInstance(ip, str)
        self.assertTrue(ip)

    def test_client_can_register_and_join_channel(self):
        async def scenario():
            server = IRCServer(host="127.0.0.1", port=0, name="test.local")
            asyncio_server = await asyncio.start_server(server.handle_client, "127.0.0.1", 0)
            port = asyncio_server.sockets[0].getsockname()[1]
            await asyncio_server.start_serving()

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(f"NICK alice\r\nUSER alice 0 * :Test User\r\n".encode("utf-8"))
            await writer.drain()
            await _register(reader, "alice")
            await _drain_motd(reader)

            writer.write(b"JOIN #general\r\n")
            await writer.drain()

            joined = await _wait_for_line(reader, lambda line: " JOIN #general" in line)
            names = await _wait_for_line(reader, lambda line: " 353 " in line and "#general" in line)

            writer.write(b"QUIT :bye\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            asyncio_server.close()
            await asyncio_server.wait_closed()

            self.assertTrue(joined is not None)
            self.assertTrue(names is not None)

        asyncio.run(scenario())

    def test_channel_messages_are_relayed(self):
        async def scenario():
            server = IRCServer(host="127.0.0.1", port=0, name="test.local")
            asyncio_server = await asyncio.start_server(server.handle_client, "127.0.0.1", 0)
            port = asyncio_server.sockets[0].getsockname()[1]
            await asyncio_server.start_serving()

            reader_a, writer_a = await asyncio.open_connection("127.0.0.1", port)
            reader_b, writer_b = await asyncio.open_connection("127.0.0.1", port)

            for nick, reader, writer in (
                ("alice", reader_a, writer_a),
                ("bob", reader_b, writer_b),
            ):
                writer.write(f"NICK {nick}\r\nUSER {nick} 0 * :Test User\r\n".encode("utf-8"))
                await writer.drain()
                await _register(reader, nick)
                await _drain_motd(reader)

            writer_a.write(b"JOIN #general\r\n")
            await writer_a.drain()
            await _wait_for_line(reader_a, lambda line: " JOIN #general" in line and "alice" in line)

            writer_b.write(b"JOIN #general\r\n")
            await writer_b.drain()
            await _wait_for_line(reader_a, lambda line: " JOIN #general" in line and "bob" in line)

            writer_a.write(b"PRIVMSG #general :hello ios\r\n")
            await writer_a.drain()

            received = await _wait_for_line(
                reader_b,
                lambda line: "PRIVMSG #general :hello ios" in line,
            )

            for writer in (writer_a, writer_b):
                writer.write(b"QUIT :bye\r\n")
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            asyncio_server.close()
            await asyncio_server.wait_closed()

            self.assertIsNotNone(received)
            self.assertIn("alice", received)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
