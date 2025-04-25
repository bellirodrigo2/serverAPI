from typing import Annotated, Any, Callable, Mapping, Sequence

from serveAPI.dependencies.mapfunction import NO_DEFAULT, FuncArg, get_func_args


def test_funcarg_mt(funcsmap: Mapping[str, Callable[..., Any]]):

    mt = get_func_args(funcsmap["mt"])
    assert mt == []


def test_funcarg_simple(funcsmap: Mapping[str, Callable[..., Any]]):

    simple = get_func_args(funcsmap["simple"])
    assert len(simple) == 2
    assert simple[0].name == "arg1"
    assert simple[0].argtype == str
    assert simple[0].basetype == str
    assert simple[0].default == NO_DEFAULT
    assert simple[0].extras == None
    assert simple[0].istype(str) == True
    assert simple[0].istype(int) == False

    assert simple[1].name == "arg2"
    assert simple[1].argtype == int
    assert simple[1].basetype == int
    assert simple[1].default == NO_DEFAULT
    assert simple[1].extras == None
    assert simple[1].istype(int) == True
    assert simple[1].istype(str) == False


def test_funcarg_def(funcsmap: Mapping[str, Callable[..., Any]]):

    def_: Sequence[FuncArg] = get_func_args(funcsmap["def"])
    assert len(def_) == 4
    assert def_[0].name == "arg1"
    assert def_[0].argtype == str
    assert def_[0].basetype == str
    assert def_[0].default == "foobar"
    assert def_[0].extras == None
    assert def_[0].istype(str) == True
    assert def_[0].istype(int) == False

    assert def_[1].name == "arg2"
    assert def_[1].argtype == int
    assert def_[1].basetype == int
    assert def_[1].default == 12
    assert def_[1].extras == None
    assert def_[1].istype(int) == True
    assert def_[1].istype(str) == False

    assert def_[2].name == "arg3"
    assert def_[2].argtype == bool
    assert def_[2].basetype == bool
    assert def_[2].default == True
    assert def_[2].extras == None
    assert def_[2].istype(bool) == True
    assert def_[2].istype(str) == False

    assert def_[3].name == "arg4"
    assert def_[3].argtype == None
    assert def_[3].basetype == None
    assert def_[3].default == None
    assert def_[3].extras == None
    assert def_[3].istype(str) == False


def test_funcarg_ann(funcsmap: Mapping[str, Callable[..., Any]]):

    ann: Sequence[FuncArg] = get_func_args(funcsmap["ann"])
    assert len(ann) == 4

    assert ann[0].name == "arg1"
    assert ann[0].argtype == Annotated[str, "meta1"]
    assert ann[0].basetype == str
    assert ann[0].default == NO_DEFAULT
    assert ann[0].extras == ["meta1"]
    assert ann[0].istype(str) == True
    assert ann[0].istype(int) == False
    assert ann[0].hasinstance(str) == True
    assert ann[0].getinstance(str) == "meta1"

    assert ann[1].name == "arg2"
    assert ann[1].argtype == Annotated[int, "meta1", 2]
    assert ann[1].basetype == int
    assert ann[1].default == NO_DEFAULT
    assert ann[1].extras == ["meta1", 2]
    assert ann[1].istype(int) == True
    assert ann[1].istype(str) == False
    assert ann[1].hasinstance(tgttype=str) == True
    assert ann[1].hasinstance(tgttype=int) == True
    assert ann[1].getinstance(str) == "meta1"
    assert ann[1].getinstance(int) == 2

    assert ann[2].name == "arg3"
    assert ann[2].argtype == Annotated[list[str], "meta1", 2, True]
    assert ann[2].basetype == list[str]
    assert ann[2].default == NO_DEFAULT
    assert ann[2].extras == ["meta1", 2, True]
    assert ann[2].istype(list[str]) == True
    assert ann[2].istype(str) == False
    assert ann[2].hasinstance(str) == True
    assert ann[2].hasinstance(int) == True
    assert ann[2].hasinstance(bool) == True
    assert ann[2].getinstance(str) == "meta1"
    assert ann[2].getinstance(int) == 2
    assert ann[2].getinstance(bool) == True

    assert ann[3].name == "arg4"
    assert ann[3].argtype == Annotated[dict[str, Any], "meta1", 2, True]
    assert ann[3].basetype == dict[str, Any]
    assert ann[3].default == {"foo": "bar"}
    assert ann[3].extras == ["meta1", 2, True]
    assert ann[3].istype(dict[str, Any]) == True
    assert ann[3].istype(str) == False
    assert ann[3].hasinstance(str) == True
    assert ann[3].hasinstance(int) == True
    assert ann[3].hasinstance(bool) == True
    assert ann[3].getinstance(str) == "meta1"
    assert ann[3].getinstance(int) == 2
    assert ann[3].getinstance(bool) == True


def test_funcarg_mix(funcsmap: Mapping[str, Callable[..., Any]]):

    mix: Sequence[FuncArg] = get_func_args(funcsmap["mix"])
    assert len(mix) == 4

    assert mix[0].name == "arg1"
    assert mix[0].argtype == None
    assert mix[0].basetype == None
    assert mix[0].default == NO_DEFAULT
    assert mix[0].extras == None
    assert mix[0].istype(str) == False
    assert mix[0].istype(int) == False
    assert mix[0].hasinstance(str) == False
    assert mix[0].getinstance(str) == None

    assert mix[1].name == "arg2"
    assert mix[1].argtype == Annotated[str, "meta1"]
    assert mix[1].basetype == str
    assert mix[1].default == NO_DEFAULT
    assert mix[1].extras == ["meta1"]
    assert mix[1].istype(str) == True
    assert mix[1].istype(int) == False
    assert mix[1].hasinstance(str) == True
    assert mix[1].hasinstance(int) == False
    assert mix[1].getinstance(str) == "meta1"
    assert mix[1].getinstance(int) == None

    assert mix[2].name == "arg3"
    assert mix[2].argtype == str
    assert mix[2].basetype == str
    assert mix[2].default == NO_DEFAULT
    assert mix[2].extras == None
    assert mix[2].istype(str) == True
    assert mix[2].istype(int) == False
    assert mix[2].hasinstance(str) == False
    assert mix[2].hasinstance(int) == False
    assert mix[2].getinstance(str) == None
    assert mix[2].getinstance(int) == None

    assert mix[3].name == "arg4"
    assert mix[3].argtype == str
    assert mix[3].basetype == str
    assert mix[3].default == "foobar"
    assert mix[3].extras == None
    assert mix[3].istype(str) == True
    assert mix[3].istype(int) == False
    assert mix[3].hasinstance(str) == True
    assert mix[3].hasinstance(int) == False
    assert mix[3].getinstance(str) == "foobar"
    assert mix[3].getinstance(int) == None
