from __future__ import annotations

from dataclasses import dataclass
from click.core import Command as ClickCommandType

from .action import Completion, Default
from .command import Command
from .option import Option

__all__ = ["ClickCommand", "convert_click_param_to_option"]


def convert_click_param_to_option(param) -> Option | None:
    """Convert a Click parameter to a zcompy Option object."""

    if not hasattr(param, 'opts'):  # Not an option parameter
        return None

    # Get parameter name and description
    names = param.opts
    if hasattr(param, 'secondary_opts') and param.secondary_opts:
        names = param.opts + param.secondary_opts

    description = param.help or ""

    # flag options (is_flag=True)
    if hasattr(param, 'is_flag') and param.is_flag:
        # flag options should not have type information or completion
        option = Option(names=names, description=description, type="", complete_func=None)
        return option

    # Determine type and completion function for non-flag options
    complete_func = None
    option_type = ""

    # Handle choices
    if hasattr(param, 'type') and hasattr(param.type, 'choices') and param.type.choices:
        # Use choices for completion
        complete_func = Completion(tuple(param.type.choices))
        option_type = "Choices"
    # Handle specific parameter types (like Interger, Float, etc.)
    elif hasattr(param, 'type') and param.type is not None:
        type_name = param.type.name if hasattr(param.type, 'name') else str(param.type)
        option_type = type_name.capitalize()
        if hasattr(param, 'default') and param.default is not None:
            complete_func = Completion(func=(str(param.default),))
        else:
            complete_func = Default()   # Default action for unknown types
    # fallback to default type for unknown parameter type
    else:
        complete_func = Default()
        option_type = "Default"

    # Create the option
    if not description:
        description = f"Option for {names[0]}"

    allow_repeat = False
    if hasattr(param, "multiple") and param.multiple:
        allow_repeat = True

    option = Option(
        names=names,
        description=description,
        type=option_type,
        complete_func=complete_func,
        allow_repeat=allow_repeat
    )

    return option


@dataclass
class ClickCommand:

    funcs: list[ClickCommandType] | ClickCommandType
    name: str = None
    description: str = ""
    # example of global options: [--help, --verbose, --version] etc.
    global_options: list[Option] = None

    def __post_init__(self):
        if callable(self.funcs):
            if self.name is None:
                self.name = self.funcs.name
            if not self.description:
                self.description = self.funcs.help or ""
        else:
            assert self.name is not None, "name must be provided when funcs is a list"

    def to_command(self) -> Command:
        if callable(self.funcs):
            return self.to_sub_command()

        cmd = Command(self.name, description=self.description)

        # add global options for command
        if self.global_options:
            cmd.add_options(self.global_options)

        for func in self.funcs:
            sub_cmd = ClickCommand(func).to_command()
            cmd.add_sub_commands(sub_cmd)
        return cmd

    def to_sub_command(self) -> Command:
        """Convert a simple Click function to a Command object with options."""
        # cloup converts underscores to hyphens in command names
        command_name = self.name.replace('-', '_')  # underscores function names
        cmd = Command(command_name, description=self.description)

        # Extract options and arguments from Click command
        if hasattr(self.funcs, 'params'):
            for param in self.funcs.params:
                option = convert_click_param_to_option(param)
                if param.param_type_name == "option":
                    if option:
                        cmd.add_options(option)
                elif param.param_type_name == "argument":
                    if option:
                        cmd.add_positional_args(option.complete_func)
                else:
                    raise ValueError(f"Unknown parameter type: {param.param_type_name}")

        return cmd
