from __future__ import annotations

import copy
from argparse import Action as ParserAction
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Callable

from .action import Action, Completion
from .command import Command
from .option import Option


@dataclass
class ParserCommand:
    parser: ArgumentParser

    def to_command(self) -> Command:
        """Convert the ArgumentParser to a Command object."""
        # Get the program name from the parser
        name = self.parser.prog or "command"
        # If the name looks like a script path, use a generic name
        if "." in name or "/" in name:
            name = "command"
        description = self.parser.description or ""

        # Create the main command
        command = Command(name=name, description=description)

        # Process top-level options
        for action in self.parser._actions:
            if action.dest == "help":
                continue

            option = self.parser_action_to_option(action)
            if option:
                command.add_options(option)

        # Process subparsers if they exist
        subparsers = self.get_subparsers(self.parser)
        if subparsers:
            for sub_name, (sub_parser, help_text) in subparsers.items():
                sub_command = self.create_subcommand(sub_name, sub_parser, help_text)
                command.add_sub_commands(sub_command)

        return command

    def parser_action_to_option(self, action: ParserAction) -> Option | None:
        """Convert an argparse action to an Option object."""
        if not hasattr(action, "option_strings") or not action.option_strings:
            return None

        names = tuple(action.option_strings)
        description = action.help or ""

        # determine option type
        option_type = ""
        if action.choices:
            option_type = "choices"
        elif action.type is not None:
            if action.type is int:
                option_type = "int"
            elif action.type is float:
                option_type = "float"
            elif action.type is str:
                option_type = "str"
            else:
                option_type = "unknown"

        # create completion function if needed
        complete_func = None

        # check if we have a custom action for this option
        # _option_actions should be set by `add_action_for_options`
        if hasattr(self, '_option_actions'):
            for option_name in action.option_strings:
                if option_name in self._option_actions:
                    action_obj = self._option_actions[option_name]
                    # deepcopy to avoid change
                    complete_func = copy.deepcopy(action_obj)
                    option_type = option_type or action_obj.type_hint()
                    break

        # check for choices or existing completion function
        if complete_func is None and action.choices:
            complete_func = Completion(func=tuple(str(choice) for choice in action.choices))

        return Option(
            names=names,
            description=description,
            type=option_type,
            complete_func=complete_func,
            allow_repeat=getattr(action, "allow_repeat", False),
        )

    def create_subcommand(
        self, name: str, parser: ArgumentParser, help_text: str = ""
    ) -> Command:
        """Create a sub-command from a subparser."""
        description = parser.description or help_text or ""
        sub_command = Command(name=name, description=description)

        # Process options for this subcommand
        for action in parser._actions:
            if action.dest == "help":
                continue

            option = self.parser_action_to_option(action)
            if option:
                sub_command.add_options(option)

        # Recursively process nested subparsers
        nested_subparsers = self.get_subparsers(parser)
        if nested_subparsers:
            for nested_name, (nested_parser, nested_help_text) in nested_subparsers.items():
                nested_subcommand = self.create_subcommand(
                    nested_name, nested_parser, nested_help_text
                )
                sub_command.add_sub_commands(nested_subcommand)

        return sub_command

    def get_subparsers(
        self, parser: ArgumentParser
    ) -> dict[str, tuple[ArgumentParser, str]]:
        """Extract subparsers and their help text from a given parser."""
        subparsers = {}

        for action in parser._actions:
            if isinstance(action.choices, dict) and action.choices:
                help_map = {}
                if hasattr(action, "_choices_actions"):
                    help_map = {
                        choice_action.dest: getattr(choice_action, "help", "")
                        for choice_action in action._choices_actions
                    }

                for name, sub_parser in action.choices.items():
                    if isinstance(sub_parser, ArgumentParser):
                        help_text = help_map.get(name, "")
                        subparsers[name] = (sub_parser, help_text)

        return subparsers

    def add_action_for_options(self, *options, action: Action | Callable):
        """Add an action for the given options.

        Args:
            options: The option names to add the action for.
            action: The Action object to add.

        .. code-block:: python
            parser_command.add_action_for_options("--file", "--output", action)
            parser_command.to_command()
        """
        if callable(action):
            action = Completion(func=action, shell_embed=True)
        # Store the action for later use in option processing
        if not hasattr(self, '_option_actions'):
            self._option_actions = {}

        # Map option names to the action
        for option_name in options:
            self._option_actions[option_name] = action
