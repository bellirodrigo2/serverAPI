import asyncio
from dataclasses import dataclass, field
from typing import Callable

from serveAPI.interfaces import ISockerServer, ITaskRunner
from serveAPI.safedict import SafeDict


@dataclass
class TCPServer(ISockerServer):
    host: str
    port: int
    runner: ITaskRunner
    fire_and_forget: bool
    makeid: Callable[[], str]
    writers: SafeDict[asyncio.StreamWriter] = field(
        default_factory=SafeDict[asyncio.StreamWriter]
    )

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        addr: str | None = writer.get_extra_info("peername")

        if not addr and not self.fire_and_forget:
            print("[ERROR] Could not get client address. Closing connection.")
            writer.close()
            await writer.wait_closed()
            return

        addr_str = str(addr) if addr else self.makeid()

        await self.writers.set(addr_str, writer)

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                route, id = await self.runner.execute(data, addr_str)

                if not self.fire_and_forget and addr:
                    msg = f'Message id="{id}" received for route="{route}"'
                    writer.write(msg.encode())
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            await self.writers.pop(addr_str)

    async def write(self, data: bytes, addr: str | tuple[str, int]) -> None:
        writer = await self.writers.get(addr)
        if writer:
            try:
                writer.write(data)
                await writer.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                print(f"[WARN] Failed to send response to {addr}: {e}")
                await self.writers.pop(addr)
        else:
            if self.fire_and_forget:
                print(f"[INFO] Fire-and-forget mode: no response sent to {addr}")
            else:
                print(f"[WARN] No writer found for address: {addr}")

    async def start(self):
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        print(f"TCPServer started on {addr}")

        async with server:
            await server.serve_forever()
