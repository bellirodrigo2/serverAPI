import pytest

from serveAPI.exceptions import UnhandledError


# === Exceções fictícias para teste ===
class MyError(Exception):
    pass


class MySubError(MyError):
    pass


class OtherError(Exception):
    pass


@pytest.mark.asyncio
async def test_set_handler_and_resolve(registry, sample_handler, handler_called_flag):
    registry.set_handler(MyError, sample_handler)

    assert MyError in registry
    assert UnhandledError not in registry

    result = await registry.resolve(MyError("something went wrong"))
    assert result == "Handled: something went wrong"
    assert handler_called_flag["called"]
    assert handler_called_flag["value"] == "something went wrong"


@pytest.mark.asyncio
async def test_register_handler_with_decorator(registry, handler_called_flag):
    @registry.decorator(MyError)
    async def my_handler(exc: BaseException) -> str:
        handler_called_flag["called"] = True
        return f"decorated: {exc}"

    assert UnhandledError not in registry
    assert MyError in registry
    result = await registry.resolve(MyError("deco"))
    assert result == "decorated: deco"
    assert handler_called_flag["called"]


@pytest.mark.asyncio
async def test_resolve_with_subclass(registry, sample_handler, handler_called_flag):
    registry.set_handler(MyError, sample_handler)

    # MySubError é uma subclasse de MyError
    result = await registry.resolve(MySubError("sub error"))
    assert result == "Handled: sub error"
    assert handler_called_flag["called"]

    assert UnhandledError not in registry
    assert MyError in registry


@pytest.mark.asyncio
async def test_resolve_raises_if_no_handler(registry):
    with pytest.raises(UnhandledError):
        registry.resolve(OtherError("not handled"))

    assert UnhandledError not in registry


@pytest.mark.asyncio
async def test_multiple_handlers_match_first_correct_type(registry):
    calls = []

    async def handler_base(exc: BaseException) -> str:
        calls.append("base")
        return "base handler"

    async def handler_specific(exc: BaseException) -> str:
        calls.append("specific")
        return "specific handler"

    registry.set_handler(MyError, handler_base)
    registry.set_handler(MySubError, handler_specific)

    result = await registry.resolve(MySubError("hello"))

    assert UnhandledError not in registry
    assert MyError in registry
    assert MySubError in registry

    assert result == "specific handler"
    assert calls == ["specific"]  # deve chamar apenas o mais específico
