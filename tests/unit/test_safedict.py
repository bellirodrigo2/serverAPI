import asyncio

import pytest

from serveAPI.safedict import SafeDict


@pytest.mark.asyncio
async def test_set_and_get():
    d = SafeDict[int]()
    await d.set("a", 10)
    result = await d.get("a")
    assert result == 10


@pytest.mark.asyncio
async def test_get_missing_key_returns_none():
    d = SafeDict[str]()
    result = await d.get("missing")
    assert result is None


@pytest.mark.asyncio
async def test_pop_removes_key():
    d = SafeDict[str]()
    await d.set("key", "value")
    await d.pop("key")
    result = await d.get("key")
    assert result is None


@pytest.mark.asyncio
async def test_concurrent_access():
    d = SafeDict[int]()

    async def worker(i: int):
        await d.set(f"k{i}", i)

    n = 10000

    await asyncio.gather(*(worker(i) for i in range(n)))

    for i in range(100):
        assert await d.get(f"k{i}") == i


@pytest.mark.asyncio
async def test_pop_non_existent_key():
    d = SafeDict[int]()
    # Deve não lançar erro mesmo se a chave não existir
    await d.pop("not_there")
    assert await d.get("not_there") is None
