from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable

from .action import Completion, Default
from .command import Command
from .option import Option

__all__ = [
    "FireCommand",
    "dict_to_command",
    "func_to_command",
    "obj_to_func_dict",
]


def obj_to_func_dict(obj) -> dict[str, Callable]:
    "Get function of class/object that not startwith _"
    func_dict = {}
    for attr_name in dir(obj):
        attr = getattr(obj, attr_name)
        if callable(attr) and not attr_name.startswith("_"):  # skip dunder methods
            func_dict[attr_name] = attr
    return func_dict


def func_to_command(func: Callable, class_type: bool = False) -> Command:
    # f(val1, val2) -> cmd add --val1 <value> --val2 <value>
    name = func.__name__
    description = func.__doc__ or ""

    sig = inspect.signature(func)
    options = []
    for param_name, param in sig.parameters.items():
        if class_type and param_name == "self":
            continue

        option_kwargs: dict[str, Any] = {"names": f"--{param_name}"}

        # type annotation
        if param.annotation != inspect.Parameter.empty:
            if hasattr(param.annotation, '__name__'):
                type_str = param.annotation.__name__
            else:
                type_str = str(param.annotation).split('.')[-1].replace("'", "").replace(">", "")
            option_kwargs["description"] = type_str

        # set default values as Completion
        option_kwargs["complete_func"] = Default()
        if param.default != inspect.Parameter.empty:
            option_kwargs["complete_func"] = Completion(func=(str(param.default),))

        options.append(Option(**option_kwargs))

    return Command(name=name, description=description, options=options)


def dict_to_command(
    obj_dict: dict, name: str, description: str = "", class_type: bool = False
) -> Command:
    """
    Convert a dictionary of functions to a Command.
    Keyis of dict are the subcommand names, options are arguments in function.
    For example, {"add": f} and f(x, y) represents `cmd add -x <value> -y <value>`

    Args:
        obj_dict: A dictionary mapping subcommand names to their corresponding functions.
        name: The name of the command.
        description: A brief description of the command. Default is an empty string.
        class_type: Whether to treat the function as a class method (default is False).
    """
    cmd = Command(name=name, description=description)
    for subcmd_name, func in obj_dict.items():
        assert callable(func), f"Value {func} for key {subcmd_name} is not callable"
        sub_cmd = func_to_command(func=func, class_type=class_type)
        cmd.add_sub_commands(sub_cmd)
    return cmd


@dataclass
class FireCommand:

    name: str
    description: str = ""
    obj: dict[str, Callable] | Callable | Any | type = None

    def to_command(self) -> Command:
        if isinstance(self.obj, dict):
            return dict_to_command(self.obj, name=self.name, description=self.description)
        elif isinstance(self.obj, type):  # class
            func_dict = obj_to_func_dict(self.obj)
            return dict_to_command(
                func_dict, name=self.name,
                description=self.description, class_type=True
            )
        elif callable(self.obj):  # function
            return func_to_command(func=self.obj)
        else:  # object
            func_dict = obj_to_func_dict(self.obj)
            return dict_to_command(func_dict, name=self.name, description=self.description)
