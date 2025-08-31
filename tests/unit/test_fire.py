
import pytest

from zcompy import Command, Completion, Default, Option
from zcompy.fire_command import FireCommand, func_to_command


def add(x, y):
    """Addition command"""
    return x + y


def mul(a, b):
    return a * b


def div(val1, val2: int = 1):
    """Division command"""
    return val1 / val2


class A:

    def add(self, x, y):
        """Addition command"""
        return x + y

    def mul(self, a, b):
        return a * b

    def div(self, val1, val2: int = 1):
        """Division command"""
        return val1 / val2


Add_cmd = Command(
    name="add", description="Addition command",
    options=[
        Option("--x", complete_func=Default()),
        Option("--y", complete_func=Default()),
    ]
)

Mul_cmd = Command(
    name="mul", description="",
    options=[
        Option("--a", complete_func=Default()),
        Option("--b", complete_func=Default())
    ]
)

Div_cmd = Command(
    name="div", description="Division command",
    options=[
        Option("--val1", complete_func=Default()),
        Option("--val2", description="int", complete_func=Completion(func=("1", ))),
    ]
)


_CMD_NAME = "cmd"
_CMD_DESC = "Math operations"


Dict_cmd = Command(
    _CMD_NAME, _CMD_DESC,
    sub_commands=[Add_cmd, Mul_cmd, Div_cmd]
)


@pytest.mark.parametrize("func, expected", [
    (add, Add_cmd),
    (mul, Mul_cmd),
    (div, Div_cmd),
])
def test_fire_func_to_cmd(func, expected):
    gen_cmd = func_to_command(func)
    assert gen_cmd == expected


def sort_cmd(cmds):
    return sorted(cmds, key=lambda cmd: cmd.name)


@pytest.mark.parametrize("obj, name, description, expected", [
    (add, None, None, Add_cmd),
    ({"add": add, "mul": mul, "div": div}, _CMD_NAME, _CMD_DESC, Dict_cmd),
    (A, _CMD_NAME, _CMD_DESC, Dict_cmd),
    (A(), _CMD_NAME, _CMD_DESC, Dict_cmd),
])
def test_fire_command(obj, name, description, expected):
    fire_cmd = FireCommand(name=name, description=description, obj=obj)
    gen_cmd = fire_cmd.to_command()
    assert gen_cmd == expected
