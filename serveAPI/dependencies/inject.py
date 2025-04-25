from functools import partial
from typing import Any, Callable, Mapping

from serveAPI.dependencies.mapfunction import FuncArg, get_func_args
from serveAPI.dependencies.model import Iinjectable


def inject(
    func: Callable[..., Any],
    context: Mapping[str | type, Any],
    raise_on_missing: bool,
    validate_default: bool,
):
    args: dict[str, FuncArg] = {
        arg.name: arg for arg in get_func_args(func) if arg.hasinstance(Iinjectable)
    }
    resolved: dict[str, Any] = {}

    for key, arg in args.items():
        value = None
        instance = arg.getinstance(Iinjectable)
        if key in context:
            value = context[key]
        elif type(instance) in context:
            value = context[type(instance)]
        elif instance.default is not Ellipsis:
            if validate_default:
                instance.validate(instance.default)
            value = instance.default
        elif raise_on_missing:
            raise RuntimeError(f"Missing injectable for '{key}'")
        else:
            continue  # Not required and not found

        if value is not None:
            resolved[key] = value
    # print(resolved)

    return partial(func, **resolved)
