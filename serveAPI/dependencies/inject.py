from functools import partial
from typing import Any, Callable, Mapping, MutableMapping

from serveAPI.dependencies.mapfunction import FuncArg, get_func_args, map_types
from serveAPI.dependencies.model import Iinjectable


def inject(
    func: Callable[..., Any],
    context: Mapping[str, Any],
    raise_on_missing: bool,
    validate_default: bool,
):

    injectables_map: MutableMapping[str, Iinjectable] = map_types(func, Iinjectable)
    print(injectables_map)
    toremove: list[str] = []
    for key, value in injectables_map.items():
        if key in context:
            value.validate(context[key])
            injectables_map[key] = context[key]
        else:
            if value.default is Ellipsis:
                if raise_on_missing:
                    raise RuntimeError(f"Missing injectable for '{key}'")
                toremove.append(key)
            else:
                if validate_default:
                    value.validate(value.default)
                injectables_map[key] = value.default
    for k in toremove:
        del injectables_map[k]
    return partial(func, **injectables_map)


def inject2(
    func: Callable[..., Any],
    context: Mapping[str | type, Any],
    raise_on_missing: bool,
    validate_default: bool,
):
    args: dict[str, FuncArg] = {arg.name: arg for arg in get_func_args(func)}
    resolved: dict[str, Any] = {}

    for key, arg in args.items():
        if key in context:
            value = context[key]
        elif arg.basetype and arg.basetype in context:
            value = context[arg.basetype]
        elif arg.default is not Ellipsis:
            value = arg.default
            if validate_default and isinstance(value, Iinjectable):
                value.validate(value)
        elif raise_on_missing:
            raise RuntimeError(f"Missing injectable for '{key}'")
        else:
            continue  # Not required and not found

        resolved[key] = value

    return partial(func, **resolved)
