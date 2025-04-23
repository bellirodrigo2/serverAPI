import json
from collections import defaultdict
from typing import MutableMapping


class ServerAPIException(Exception):
    pass


class EncoderEncodeError(ServerAPIException):
    pass


class EncoderDecodeError(ServerAPIException):
    pass


class RouterError(ServerAPIException):
    pass


class TypeCastError(ServerAPIException):
    pass


class RequestMiddlewareError(ServerAPIException):
    pass


class ResponseMiddlewareError(ServerAPIException):
    pass


class ParamsResolveError(ServerAPIException):
    pass


class DependencyResolveError(ServerAPIException):
    pass


class DispatchError(ServerAPIException):
    pass


class UnhandledError(ServerAPIException):
    pass


def internal_exception_handler(
    err: BaseException,
) -> str:
    err_msg: MutableMapping[str, MutableMapping[str, str]] = defaultdict(dict)

    err_msg["Exception"]["Type"] = type(err).__name__
    err_msg["Exception"]["Msg"] = str(err)

    original = err.__cause__ or err.__context__
    if original:
        err_msg["OriginalException"]["Type"] = type(original).__name__
        err_msg["OriginalException"]["Msg"] = str(original)

    return json.dumps(err_msg, ensure_ascii=False)


class ParseError(ServerAPIException):
    pass
