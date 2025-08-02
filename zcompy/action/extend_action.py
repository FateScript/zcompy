from __future__ import annotations

import inspect
import os
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable

from zcompy.utils import is_lambda_func, zsh_completion_function

from .action import Action

__all__ = [
    "Completion",
    "ExtendAction",
    "GitBranches",
    "GitCommits",
]


class ExtendAction(Action):

    @abstractmethod
    def zsh_func_source(self) -> str:
        pass


class GitBranches(ExtendAction):
    tags: bool = False
    # if tags is set, then also show tags
    remote: bool = False
    # if remote is True, only shows remote branches

    def type_hint(self) -> str:
        return "GitRemoteBranches" if self.remote else "GitBranches"

    def action_source(self) -> str:
        return f"_{self.zsh_func_name()}"

    def zsh_func_name(self) -> str:
        if self.remote:
            return "git_remote_branches"
        elif self.tags:
            return "git_branches_and_tags"
        else:
            return "git_branches"

    def zsh_func_source(self) -> str:
        if self.remote:
            return self._remote_branches_source()
        elif self.tags:
            return self._branches_and_tags_source()
        else:
            return self._local_branches_source()

    def _local_branches_source(self) -> str:
        return f"""
_{self.zsh_func_name()}() {{
  local branches
  branches=("${{(f)$(git for-each-ref --format='%(refname:short)' refs/heads)}}")
  _values 'branch' $branches
}}
"""

    def _remote_branches_source(self) -> str:
        return f"""
_{self.zsh_func_name()}() {{
  local branches
  branches=("${{(f)$(git for-each-ref --format='%(refname:short)' refs/remotes)}}")
  _values 'remote branch' $branches
}}
"""

    def _branches_and_tags_source(self) -> str:
        return f"""
_{self.zsh_func_name()}() {{
  local branches tags
  branches=("${{(f)$(git for-each-ref --format='%(refname:short)' refs/heads)}}")
  tags=("${{(f)$(git for-each-ref --format='%(refname:short)' refs/tags)}}")
  _values 'branch' $branches 'tag' $tags
}}
"""


class GitCommits(ExtendAction):

    num_commits: int = 20

    def type_hint(self) -> str:
        return "GitCommits"

    def action_source(self) -> str:
        return "_git_commits"

    def zsh_func_source(self) -> str:
        cmd = f"git log --oneline -n {self.num_commits} --format='%h %s'"
        return zsh_completion_function("_git_commits", cmd)


@dataclass
class Completion(ExtendAction):
    """Class to represent a completion with its attributes."""

    func: Callable | tuple[str] | Action
    # 1. callable function means a function to call for completion
    # 2. tuple[str] like ('auto', 'always', 'never') means choices to complete
    # 3. Files means a file completion
    shell_embed: bool = False
    # if True, the python function will be embedded in a shell file
    path: str | None = None
    # if shell_embed is False, the path to save the shell file

    def __post_init__(self):
        if is_lambda_func(self.func):
            raise ValueError("Lambda functions are not supported.")

        if callable(self.func) and not self.shell_embed:
            # specify the path to save the function
            if not self.path:
                self.path = os.environ.get("ZCOMPY_FUNC_SAVE_PATH", None)
            assert self.path is not None, (
                "Path to save the command must be specified. "
                "Set it explicitly or use the ZCOMPY_FUNC_SAVE_PATH environment variable."
            )

    def type_hint(self) -> str:
        if isinstance(self.func, Action):
            return self.func.type_hint()
        elif isinstance(self.func, (tuple, list)):
            return "Choices"
        return "Python Completion"

    def action_source(self):
        if isinstance(self.func, (tuple, list)):  # _values
            return "(" + " ".join(self.func) + ")"
        elif callable(self.func):
            if not self.shell_embed:
                self.write_python()
            return f"_{self.func.__name__}"
        elif isinstance(self.func, Action):
            return self.func.action_source()

    def write_python(self):
        func_name = self.func.__name__
        real_path = os.path.expanduser(self.path)
        file_name = os.path.join(real_path, f"{func_name}")
        func_source = inspect.getsource(self.func)

        py_source = f"""
#!/usr/bin/env python3

{func_source}

if __name__ == "__main__":
    {func_name}()
"""

        with open(file_name, "w") as f:
            f.write(py_source.lstrip())
        # TODO: add change mode
        print(f"Source file created at: {file_name}")

    def py_code_in_shell(self) -> tuple[str, str]:
        """Generate shell code that embeds the Python function."""
        func_name = self.func.__name__
        func_source = inspect.getsource(self.func)
        has_double_quotes = '"' in func_source
        has_single_quotes = "'" in func_source

        quote_symbol = '"'  # default to double quotes
        if has_double_quotes:
            if has_single_quotes:
                # convert double quotes to single quotes in the source
                func_source = func_source.replace('"', "'")
            else:
                quote_symbol = "'"

        # create shell function that runs the Python code inline
        shell_code = f"""__{func_name}() {{
    python3 -c {quote_symbol}
{func_source}
{func_name}()
{quote_symbol}
}}
"""

        return shell_code, f"__{func_name}"

    def zsh_func_source(self) -> str:
        if not callable(self.func):
            return ""

        func_name = self.func.__name__

        shell_code, cmd_name = "", func_name
        if self.shell_embed:
            shell_code, cmd_name = self.py_code_in_shell()

        return shell_code + zsh_completion_function(f"_{func_name}", cmd_name)
