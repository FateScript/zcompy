#!/usr/bin/env python3

import types

__all__ = ["is_lambda_func", "pattern_to_glob", "zsh_completion_function"]


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
