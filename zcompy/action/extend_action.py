from __future__ import annotations

import os
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable

from zcompy.utils import (
    chmod_execute,
    is_lambda_func,
    python_func_as_shell_source,
    python_func_source,
    zsh_completion_function,
)

from .action import Action

__all__ = [
    "Completion",
    "ExtendAction",
    "GitBranches",
    "GitCommits",
    "DependentCompletion",
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

    func: Callable | tuple[str, ...] | Action
    # 1. callable function means a function to call for completion
    # 2. tuple[str] like ('auto', 'always', 'never') means choices to complete
    # 3. Files means a file completion
    shell_embed: bool = True
    # if True, the python function will be embedded in a shell file
    path: str | None = None
    # if shell_embed is False, the path to save the shell file
    ignore_exception: bool = False
    # if set to True, exceptions of func will be redirected to /dev/null

    def __post_init__(self):
        if is_lambda_func(self.func):
            raise ValueError("Lambda functions are not supported.")

        shell_embed = os.environ.get("ZCOMPY_SHELL_EMBED", False)
        if shell_embed:
            assert isinstance(shell_embed, str)
            self.shell_embed = shell_embed.lower() == "true" or shell_embed == "1"

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
        assert callable(self.func), "Function must be callable."
        assert isinstance(self.path, str), "Path must be specified to write."
        func_name = self.func.__name__
        real_path = os.path.expanduser(self.path)
        file_name = os.path.join(real_path, f"{func_name}")
        func_source = python_func_source(self.func)
        file_source = f"#!/usr/bin/env python3\n\n{func_source}"

        with open(file_name, "w") as f:
            f.write(file_source)
        chmod_execute(file_name)  # add executed
        print(f"Source file created at: {file_name}")

    def zsh_func_source(self) -> str:
        if not callable(self.func):
            return ""

        func_name = self.func.__name__

        shell_code, cmd_name = "", func_name
        if self.shell_embed:
            shell_code, cmd_name = python_func_as_shell_source(self.func, self.ignore_exception)

        return shell_code + zsh_completion_function(f"_{func_name}", cmd_name)


@dataclass
class DependentCompletion(Completion):
    """Action to represent a completion that depends on another action."""
    func: Callable
    depends_on: str | tuple[str, ...] | list[tuple[str, ...]] | None = None
    # Options that the completion function depends on its value.
    # for example, `--branch main` in cli and depends_on is "--branch",
    # the option value `main` will be a args in the completion function.
    exist_depends_on: str | tuple[str, ...] | list[tuple[str, ...]] | None = None
    # Options that the completion function depends on its existence.
    # for example, `--branch` in cli and exist_depends_on is "--branch",
    # the value `1`/`0` will be a args in the completion function.

    def __post_init__(self):
        super().__post_init__()
        assert callable(self.func), "Function must be callable."
        assert self.depends_on or self.exist_depends_on, "Option must depend on another option."

    def type_hint(self) -> str:
        return "Depend option Completion"

    def zsh_func_source(self) -> str:
        func_name = self.func.__name__
        shell_code, cmd_name = "", func_name
        if self.shell_embed:
            shell_code, cmd_name = python_func_as_shell_source(self.func, self.ignore_exception)

        comp_src = zsh_completion_function(
            f"_{func_name}", cmd_name,
            options_dependency=self.depends_on,
            exist_dependency=self.exist_depends_on,
        )
        return shell_code + comp_src
