"""zcompy - Generate zsh completions with Python."""

from .action import Action, Completion, Default, DependentCompletion, ExtendAction, Files
from .command import Command
from .option import Option

__version__ = "0.0.1"

__all__ = [
    "Command",
    "Option",
    "Completion",
    "DependentCompletion",
    "Action",
    "ExtendAction",
    "Files",
    "Default",
]
