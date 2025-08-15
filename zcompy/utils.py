from __future__ import annotations

import inspect
import shlex
import types
from typing import Callable

__all__ = [
    "is_lambda_func",
    "pattern_to_glob",
    "source_by_options_denpendency",
    "zsh_completion_function"
]


def is_lambda_func(obj) -> bool:
    return isinstance(obj, types.LambdaType) and obj.__name__ == "<lambda>"


def pattern_to_glob(pattern: str | tuple[str]) -> str:
    """Convert a pattern or tuple of patterns to a glob string."""
    if isinstance(pattern, str):
        return f"\"{pattern}\""
    elif isinstance(pattern, (tuple, list)):
        return "\"(" + "|".join(pattern) + ")\""
    return ""


def zsh_completion_function(func_name: str, command: str) -> str:
    """Generate a zsh completion function source."""
    shell_template = """
{func_name}() {{
  local -a choices
  local line opt msg

  while IFS= read -r line; do
    opt="${{line%% *}}"
    msg="${{line#* }}"
    choices+=("$opt:$msg")
  done < <({command})
  _describe -t choices 'choices' choices
}}
"""
    shell_source = shell_template.format(func_name=func_name, command=command)
    return shell_source


def source_by_options_denpendency(options_depend_on: str | tuple[str, ...]) -> tuple[str, str]:
    """zsh source option to get option value in cli."""
    if isinstance(options_depend_on, str):
        options_depend_on = (options_depend_on,)

    local_name = sorted([x.lstrip("-") for x in options_depend_on], key=len)[0].replace("-", "_")

    def combine_options(opt: tuple[str, ...]):
        assert not isinstance(opt, str), "Options should not be a string"
        if len(opt) == 1:
            return f"${{opt_args[{opt[0]}]}}"
        else:
            value = combine_options(opt[1:])
            return f"${{opt_args[{opt[0]}]:-{value}}}"

    full_name = f"{local_name}_value"
    source = combine_options(options_depend_on)
    full_source = f"{full_name}={source}"
    return full_source, full_name


def python_func_as_shell_source(func: Callable) -> tuple[str, str]:
    """Generate shell code that embeds a Python function.

    Args:
        func (Callable): The Python function to embed.

    Returns:
        A tuple containing the shell code and the function name.
    """
    func_name = func.__name__
    func_source = inspect.getsource(func)
    full_source = f"{func_source}\n{func_name}()"
    shell_code = f"""__{func_name}() {{
    python3 -c \\
{shlex.quote(full_source)}
}}
"""
    return shell_code, f"__{func_name}"
