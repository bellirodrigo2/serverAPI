import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from serveAPI.interfaces import ISockerServer, ITaskRunner


@dataclass
class UDPServer(asyncio.DatagramProtocol, ISockerServer):
    host: str
    port: int
    runner: ITaskRunner
    fire_and_forget: bool
    makeid: Callable[[], str]
    spawn: Callable[[Coroutine[Any, Any, Any]], None]

    transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport):
        # única vez, transport é o mesmo para todas as peers
        self.transport = transport  # type: ignore
        print(f"UDP listening on {self.host}:{self.port}")

    def datagram_received(self, data: bytes, addr: tuple[str, int]):
        # aqui você dispara o processamento em background
        # usando seu spawn (ex: asyncio.create_task ou aiojobs.spawn)
        self.spawn(self._handle_datagram(data, addr))

    async def _handle_datagram(self, data: bytes, addr: tuple[str, int]):

        route, msg_id = await self.runner.execute(data, addr)

        if not self.fire_and_forget and isinstance(
            self.transport, asyncio.DatagramTransport
        ):
            confirm = f'Message id="{msg_id}" received for route="{route}"'.encode()
            self.transport.sendto(confirm, addr)

    def error_received(self, exc: Exception):
        print(f"[UDP] error_received: {exc}")

    async def write(self, data: bytes, addr: str | tuple[str, int]) -> None:
        # aqui contexto já garante o endereço
        if self.transport:
            try:
                self.transport.sendto(data, addr)
            except (ConnectionResetError, BrokenPipeError) as e:
                print(f"[WARN] UDP sendto to {addr} failed: {e}")
        else:
            print("[ERROR] transport not initialized")

    async def start(self):
        loop = asyncio.get_event_loop()
        # precisa passar um factory que retorna a instância de protocolo
        await loop.create_datagram_endpoint(
            lambda: self,
            local_addr=(self.host, self.port),
        )
