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
]


"""
_git_branches() {
  local branches
  branches=("${(f)$(git for-each-ref --format='%(refname:short)' refs/heads)}")
  _values 'branch' $branches
}
"""

"""
"""


class ExtendAction(Action):

    @abstractmethod
    def zsh_func_source(self) -> str:
        pass


class GitBranches(Action):
    tags: bool = False
    # if tags is set, then also show tags
    remote: bool = False
    # if remote is True, only shows remote branches

    def type_hint(self) -> str:
        return "GitRemoteBranches" if self.remote else "GitBranches"

    def action_source(self) -> str:
        return f"_{self.zsh_func_name}"

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


class GitCommits(Action):

    num_commits: int = 20

    def type_hint(self) -> str:
        return "GitCommits"

    def action_source(self) -> str:
        return "_git_commits"

    def zsh_func_source(self) -> str:
        cmd = f"git log --oneline -n {self.num_commits} --format='%h %s'"
        return zsh_completion_function("_git_commits", cmd)


# TODO: make completion as router
@dataclass
class Completion(ExtendAction):
    """Class to represent a completion with its attributes."""

    func: Callable | tuple[str] | Action
    # 1. callable function means a function to call for completion
    # 2. tuple[str] like ('auto', 'always', 'never') means choices to complete
    # 3. Files means a file completion
    path: str = "~/.local/bin"

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
            self.write_python()
            return f"_{self.func.__name__}"
        elif isinstance(self.func, Action):
            return self.func.action_source()

    def write_python(self):
        if is_lambda_func(self.func):
            raise ValueError("Lambda functions are not supported.")

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

    def zsh_func_source(self) -> str:
        if not callable(self.func):
            return ""
        func_name = self.func.__name__
        return zsh_completion_function(f"_{func_name}", func_name)
