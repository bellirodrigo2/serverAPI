from typing import Annotated, Any

from serveAPI.dependencies.inject import inject, inject2
from serveAPI.dependencies.mapfunction import get_func_args, map_types
from serveAPI.dependencies.model import Injectable


class NoValidation(Injectable):

    def validate(self, instance: Any) -> None:
        return


def injfunc(
    arg: str,
    arg_ann: Annotated[str, NoValidation(...)],
    arg_dep: str = NoValidation(...),
):
    pass


def test_inject():

    deps = get_func_args(injfunc)
    # for dep in deps:
    # print(dep)

    print("------------ PARTIAL--------------")
    ctx = {"arg": "NoChange", "arg_ann": "helloworld", NoValidation: "foobar"}
    resolfunc = inject2(injfunc, ctx, False, False)
    args = get_func_args(resolfunc)
    # for arg in args:
    # print(arg)
    assert args != deps
