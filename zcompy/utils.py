from __future__ import annotations

import inspect
import os
import shlex
import stat
import types
from typing import Callable

__all__ = [
    "chmod_execute",
    "is_lambda_func",
    "pattern_to_glob",
    "python_func_source",
    "set_shell_embed",
    "source_by_options_denpendency",
    "source_by_options_existence",
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


def source_by_options_existence(options_exist: str | tuple[str, ...]) -> tuple[str, str]:
    if isinstance(options_exist, str):
        options_exist = (options_exist,)

    local_name = sorted([x.lstrip("-") for x in options_exist], key=len)[0].replace("-", "_")
    source = " || ".join([f"${{+opt_args[{opt}]}}" for opt in options_exist])

    full_name = f"has_{local_name}"
    full_source = f"{full_name}=$(( {source} ))"
    return full_source, full_name


def _ensure_structure(
    opt: str | tuple[str, ...] | list[tuple[str, ...]]
) -> list[tuple[str, ...]]:
    if isinstance(opt, str):
        opt = (opt,)
    if not isinstance(opt[0], (tuple, list)):
        opt = [opt]
    return opt


def zsh_completion_function(
    func_name: str,
    command: str,
    options_dependency: str | tuple[str, ...] | list[tuple[str, ...]] | None = None,
    exist_dependency: str | tuple[str, ...] | list[tuple[str, ...]] | None = None,
) -> str:
    """Generate source code of zsh completion function.

    Args:
        func_name (str): The name of the shell function.
        command (str): The command executed to generate completions.
        options_dependency (str | tuple[str, ...]): The options that this completion depends on.
            Default to None, which means no dependent options are required.
        exist_dependency (str | tuple[str, ...]): The options that must exist for this completion
            to be valid. Default to None.
    """
    assignments = ""
    sources, var_names = [], []
    if options_dependency:
        options_dependency = _ensure_structure(options_dependency)
        for opt in options_dependency:
            src, name = source_by_options_denpendency(opt)
            sources.append(src)
            var_names.append(name)

    if exist_dependency:
        exist_dependency = _ensure_structure(exist_dependency)
        for opt in exist_dependency:
            src, name = source_by_options_existence(opt)
            sources.append(src)
            var_names.append(name)

    if sources:
        var_declar = f"local {' '.join(var_names)}"
        assignments = "\n".join([f"  {x}" for x in [var_declar] + sources]) + "\n"
        var_suffix = ' '.join(f'"${name}"' for name in var_names)
        command = f"{command} {var_suffix}"

    shell_template = """
{func_name}() {{
  local -a choices
  local line opt msg
{assignments}
  while IFS= read -r line; do
    opt="${{line%% *}}"
    msg="${{line#* }}"
    choices+=("$opt:$msg")
  done < <({command})
  _describe -t choices 'choices' choices
}}
"""
    shell_source = shell_template.format(
        func_name=func_name, assignments=assignments, command=command
    )
    return shell_source


def python_func_source(func: Callable) -> str:
    """Generate source code of a Python function that can be executed as script."""
    func_name = func.__name__
    func_source = inspect.getsource(func)
    num_args = func.__code__.co_argcount
    if num_args == 0:
        full_source = f"{func_source}\n{func_name}()"
    else:
        args_source = ", ".join([f"sys.argv[{i}]" for i in range(1, num_args + 1)])
        full_source = f"""
import sys

{func_source}

if len(sys.argv) > {num_args}:
    {func_name}({args_source})
"""
    return full_source


def python_func_as_shell_source(func: Callable, ignore_exception: bool = False) -> tuple[str, str]:
    """Generate shell code that embeds a Python function.

    Args:
        func (Callable): The Python function to embed.
        ignore_exception (bool): If True, exceptions will be redirected to /dev/null.

    Returns:
        A tuple containing the shell code and the function name.
    """
    indent = " " * 2  # shell indent
    func_name = func.__name__
    num_args = func.__code__.co_argcount
    full_source = python_func_source(func)
    redirect_text = " 2>/dev/null" if ignore_exception else ""

    if num_args == 0:
        shell_code = f"""__{func_name}() {{
{indent}python3 -c \\
{shlex.quote(full_source)}
}}{redirect_text}
"""
    else:  # has_args, "import sys" needed
        local_assign = [f'local arg{i}_value="${i}"' for i in range(1, num_args + 1)]
        assignment = "\n".join(indent + x for x in local_assign)
        shell_args = " ".join(f'"$arg{i}_value"' for i in range(1, num_args + 1))

        shell_code = f"""__{func_name}() {{
{assignment}
{indent}python3 -c \\
{shlex.quote(full_source)} {shell_args} 2>/dev/null
}}{redirect_text}
"""

    return shell_code, f"__{func_name}"


def chmod_execute(filename):
    """Make a file executable, which equals 'chmod +x file'."""
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def set_shell_embed(value: bool = True):
    os.environ["ZCOMPY_SHELL_EMBED"] = "1" if value else "0"
