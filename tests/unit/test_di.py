import asyncio
from dataclasses import dataclass
from typing import Annotated

import pytest

from serveAPI.di import Depends


@dataclass
class Service:
    name: str = "Service"


def make_service() -> Service:
    return Service(name="FactoryService")


async def make_async_service() -> Service:
    await asyncio.sleep(0.01)
    return Service(name="AsyncService")


def service_with_dep(dep: Service = Depends(Service)) -> str:
    return f"Hello from {dep.name}"


# ---------- IoCContainer Tests ----------


def test_register_and_resolve_type(base_container):
    base_container.register(Service, lambda c: Service("MyService"))
    instance = base_container.resolve(Service)
    assert isinstance(instance, Service)
    assert instance.name == "MyService"


def test_register_and_resolve_callable(base_container):
    base_container.register(make_service, lambda _: make_service())
    instance = base_container.resolve(make_service)
    assert isinstance(instance, Service)
    assert instance.name == "FactoryService"


def test_missing_provider_raises(base_container):
    with pytest.raises(ValueError):
        base_container.resolve(Service)


# ---------- Singleton Tests ----------


def test_singleton_resolves_once(singleton_container):
    counter = {"count": 0}

    def make():
        counter["count"] += 1
        return Service("Singleton")

    singleton_container.register(Service, lambda c: make())
    one = singleton_container.resolve(Service)
    two = singleton_container.resolve(Service)

    assert one is two
    assert counter["count"] == 1


# ---------- Dependency Injector Tests ----------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dep_provider, expected_name",
    [
        (Depends(Service), "ResolvedService"),
        (Depends(make_service), "FactoryService"),
        (Depends(make_async_service), "AsyncService"),
    ],
)
async def test_dependency_resolver_variants(injector, dep_provider, expected_name):
    injector.container.register(Service, lambda _: Service("ResolvedService"))

    async def my_func(dep: Service = dep_provider):
        return dep.name

    kwargs = await injector.resolve(my_func)
    assert kwargs["dep"].name == expected_name


@pytest.mark.asyncio
async def test_dependency_chain(injector):
    injector.container.register(Service, lambda c: Service("Chained"))

    async def outer(dep: str = Depends(service_with_dep)):
        return dep

    kwargs = await injector.resolve(outer)
    assert kwargs["dep"] == "Hello from Chained"


# ---------- Annotated Tests ----------


@pytest.mark.asyncio
async def test_dependency_resolver_with_annotated_type(annotated_injector):
    annotated_injector.container.register(
        Service, lambda c: Service("AnnotatedService")
    )

    async def my_func(dep: Annotated[Service, Depends(Service)]):
        return dep.name

    kwargs = await annotated_injector.resolve(my_func)
    assert kwargs["dep"].name == "AnnotatedService"


@pytest.mark.asyncio
async def test_dependency_resolver_with_annotated_callable(annotated_injector):
    async def my_func(dep: Annotated[Service, Depends(make_async_service)]):
        return dep.name

    kwargs = await annotated_injector.resolve(my_func)
    assert kwargs["dep"].name == "AsyncService"


@pytest.mark.asyncio
async def test_dependency_chain_with_annotated(annotated_injector):
    annotated_injector.container.register(
        Service, lambda c: Service("ChainedAnnotated")
    )

    def inner(dep: Annotated[Service, Depends(Service)]) -> str:
        return f"Hello from {dep.name}"

    async def outer(dep: Annotated[str, Depends(inner)]):
        return dep

    kwargs = await annotated_injector.resolve(outer)
    assert kwargs["dep"] == "Hello from ChainedAnnotated"
