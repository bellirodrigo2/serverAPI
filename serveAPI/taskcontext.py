from asyncio import Lock
from dataclasses import dataclass, field
from typing import Any

from serveAPI.interfaces import ISockerServer, ITaskContext


@dataclass
class TaskContext(ITaskContext):
    server: ISockerServer
    registry: dict[str, Any] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    async def push(self, id: str, addr: Any) -> None:
        async with self._lock:
            self.registry[id] = addr

    async def respond(
        self, id: str, addr: str | tuple[str, int] | None, data: bytes
    ) -> None:
        async with self._lock:
            addr = self.registry.pop(id, None)

        if addr is not None:
            # No UDP, addr é tupla (ip, porta), no TCP addr é uma string.
            if isinstance(addr, tuple):
                addr = addr[0]  # Envia só o IP
            await self.server.write(data, addr)
