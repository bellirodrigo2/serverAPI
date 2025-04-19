from dataclasses import dataclass, field
from typing import Any

from serveAPI.di import resolve_dependencies
from serveAPI.interfaces import (
    IDispatcher,
    IHandler,
    IMetaExtractor,
    ITaskContext,
    ITaskRunner,
)


@dataclass
class TaskRunner(ITaskRunner):
    handler: IHandler
    dispatcher: IDispatcher
    metaextractor: IMetaExtractor
    context: ITaskContext

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]:

        id, route, data = self.metaextractor.extract(input)

        handler, input_data = self.handler.handle(route, data)
        await self.context.push(id, addr)

        deps = await resolve_dependencies(handler)

        async def bound_handler():
            return await handler(input_data, **deps)

        await self.dispatcher.dispatch(bound_handler, input_data, id, addr)

        return route, id
