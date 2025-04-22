from typing import Annotated

from serveAPI.di import Depends
from serveAPI.interfaces import Params


def get_db():
    return "db"


def params_deps(params: Params, db: str = Depends(get_db)) -> Params:
    return params


def params_annotated_deps(
    params: Annotated[Params, "annotated test"], db: str = Depends(get_db)
) -> Params:
    return params


def params_deps_annotated(
    params: Params, db: Annotated[str, Depends(get_db)]
) -> Params:
    return params


def params_annotated_deps_annotated(
    params: Annotated[Params, "annotated test"], db: Annotated[str, Depends(get_db)]
) -> Params:
    return params
