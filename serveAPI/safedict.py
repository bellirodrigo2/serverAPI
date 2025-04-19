import asyncio
from dataclasses import dataclass, field
from typing import Generic, MutableMapping, TypeVar

T = TypeVar("T")


@dataclass
class SafeDict(Generic[T]):
    _map: MutableMapping[str, T] = field(default_factory=dict[str, T])
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def set(self, key: str, value: T) -> None:
        async with self._lock:
            self._map[key] = value

    async def get(self, key: str) -> T | None:
        async with self._lock:
            return self._map.get(key, None)

    async def pop(self, key: str) -> None:
        async with self._lock:
            self._map.pop(key, None)
