from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from zcompy.utils import pattern_to_glob

__all__ = [
    "Action",
    "SimpleAction",
    "Default",
    "Files",
    "URLs",
    "OSEnv",
    "ProcessID",
    "UserNames",
    "Hosts",
]


class Action(ABC):
    """Base class for actions that can be performed by commands."""

    @abstractmethod
    def type_hint(self) -> str:
        pass

    @abstractmethod
    def action_source(self) -> str:
        pass


@dataclass
class SimpleAction(Action):

    hint: str
    cmd_source: str

    def type_hint(self):
        return self.hint

    def action_source(self) -> str:
        return self.cmd_source


@dataclass
class Files(Action):
    # pattern/ignore_pattern example: "*.txt" or ("*.txt", "*.md")
    pattern: str | tuple[str] | None = None
    ignore_pattern: str | tuple[str] | None = None
    dir_only: bool = False

    def type_hint(self) -> str:
        return "Directory" if self.dir_only else "Files"

    def action_source(self):
        source = "_files "
        if self.dir_only:
            if self.pattern or self.ignore_pattern:
                raise AssertionError("Cannot use dir_only with patterns")
            return "_files -/"

        opts = []
        if self.pattern:
            opts.append(f"-g {pattern_to_glob(self.pattern)}")
        if self.ignore_pattern:
            opts.append(f"-F {pattern_to_glob(self.ignore_pattern)}")
        if opts:
            source += " ".join(opts)
        return source.strip()


@dataclass
class Default(SimpleAction):
    """Default action for commands without specific actions."""
    hint: str = "Default"
    cmd_source: str = "_default"


@dataclass
class URLs(SimpleAction):
    """Action to represent a URL."""
    hint: str = "URLs"
    cmd_source: str = "_urls"


@dataclass
class OSEnv(SimpleAction):
    """Action to represent an OS environment variable."""

    hint: str = "Environment variable"
    cmd_source: str = "_parameters"


@dataclass
class ProcessID(SimpleAction):
    """Action to represent a process ID."""

    hint: str = "Process ID"
    cmd_source: str = "_pids"


@dataclass
class UserNames(SimpleAction):
    """Action to represent a user name."""

    hint: str = "User name"
    cmd_source: str = "_users"


@dataclass
class Hosts(SimpleAction):
    """Action to represent a host name."""
    hint: str = "Host name"
    cmd_source: str = "_hosts"
