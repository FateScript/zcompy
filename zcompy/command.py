from __future__ import annotations

import os
from dataclasses import dataclass, field

from .action import Action, ExtendAction
from .option import Option

__all__ = ["Command"]


@dataclass
class Command:
    """Class to represent a command with sub-commands and options."""

    # cmd example: cmd diff -f <files>
    # cmd -> name
    # diff -> sub-command
    # -f -> option
    # <files> -> positional argument
    name: str
    description: str = ""
    options: list[Option] = field(default_factory=list)
    sub_commands: list[Command] = field(default_factory=list)
    positional_args: list[Action] = field(default_factory=list)
    repeat_pos_args: Action | None = None

    def add_options(self, options: Option | list[Option]):
        """Add an option to this command."""
        if isinstance(options, Option):
            self.options.append(options)
        else:
            self.options.extend(options)

    def add_positional_args(self, action: Action | list[Action]):
        """Add a positional argument to this command."""
        if isinstance(action, Action):
            self.positional_args.append(action)
        else:
            self.positional_args.extend(action)

    def add_sub_commands(self, sub_command: Command | list[Command]):
        """Add a sub-command to this command."""
        if isinstance(sub_command, Command):
            self.sub_commands.append(sub_command)
        else:
            self.sub_commands.extend(sub_command)

    def add_action_for_options(self, *options, action: Action, recursive: bool = False):
        """Add an action for the given options.

        Args:
            options: The option names to add the action for.
            action: The Action object to add.
            recursive: If True, also add the action to matching options in sub-commands.

        .. code-block:: python
            command.add_action_for_options("--file", "--output", action)
        """
        target_options = set(options)

        for option in self.options:
            names = {option.names} if isinstance(option.names, str) else set(option.names)
            if names & target_options:
                option.complete_func = action

        if recursive:  # add to sub-commands if recursive
            for sub_command in self.sub_commands:
                sub_command.add_action_for_options(*options, action=action, recursive=True)

    def command_depth(self) -> int:
        """Calculate the depth of the command based on sub-commands."""
        if not self.sub_commands:
            return 0
        return 1 + max(sub_cmd.command_depth() for sub_cmd in self.sub_commands)

    def subcommand_completion(self, func_name: str | None = None) -> str:
        """Generate completion code for sub-commands."""
        if not self.sub_commands:
            return ""

        if func_name is None:
            func_name = self.name
        indent = "  "

        subcmd_descs = [f'"{x.name}:{x.description}"' for x in self.sub_commands]
        subcmds = "\n".join([f"{indent * 2}{desc}" for desc in subcmd_descs])

        completion_code = f"""
_{func_name}_subcommands() {{
  local -a subcmds
  subcmds=(
{subcmds}
  )
  _describe -t subcommands 'subcommands' subcmds
}}
"""
        return completion_code

    def shell_source_used_by_options(self, recursive: bool = False) -> list[str]:
        """
        Generate shell source used by option.
        For example, options might use python/git command to generate completion.
        """
        shell_source = [
            x.complete_func.zsh_func_source()
            for x in self.options if isinstance(x.complete_func, ExtendAction)
        ]
        shell_source.extend([
            x.zsh_func_source() for x in [*self.positional_args, self.repeat_pos_args]
            if isinstance(x, ExtendAction)
        ])

        if recursive:
            for subcmd in self.sub_commands:
                sub_cmd_source = subcmd.shell_source_used_by_options(recursive=True)
                shell_source.extend(sub_cmd_source)

        # deduplicate, since set is unordered, we sort it to have a consistent order
        deduped_source = sorted(x for x in (set(shell_source)) if x)
        return deduped_source

    def arguments_with_options(self, indent_length=0, context_flag: bool = False) -> str:
        """Generate the argument source with options for command."""
        assert len(self.sub_commands) == 0, "Only used when there are no sub-commands."
        zsh_line = "\\\n"
        indent = "  "

        options_source = [opt.to_complete_argument() for opt in self.options]
        for idx, x in enumerate(self.positional_args, 1):
            pos_text = f"'{idx}:{x.type_hint()}:{x.action_source()}'"
            options_source.append(pos_text)

        if self.repeat_pos_args:
            hint = self.repeat_pos_args.type_hint()
            source = self.repeat_pos_args.action_source()
            pos_text = f"'*:{hint}:{source}'"
            options_source.append(pos_text)

        argument_source = "_arguments -C" if context_flag else "_arguments"
        source_lines = [argument_source] + [indent + opt for opt in options_source]
        return f" {zsh_line}".join([indent * indent_length + x for x in source_lines])

    def arguments_with_subcommands(self, indent_length=0) -> str:
        """Generate the argument source with sub-commands for command."""
        zsh_line = "\\\n"
        indent = "  "

        source_lines = [opt.to_complete_argument() for opt in self.options]
        source_lines.extend(["'1: :->cmds'", "'*:: :->args'"])

        source_lines = ["_arguments -C"] + [indent + x for x in source_lines]
        return f" {zsh_line}".join([indent * indent_length + x for x in source_lines])

    def generate_main_function(self, func_name: str | None = None) -> str:
        assert len(self.sub_commands) > 0, "Main function generation requires sub-commands."
        if func_name is None:
            func_name = self.name

        subcmd_comp_code = self.subcommand_completion(func_name=func_name)
        arg_subcommand = self.arguments_with_subcommands(indent_length=1)
        indent = "  "
        main_function = f"""
_{func_name}() {{
  local state

{arg_subcommand}

  case $state in
    cmds)
      _{func_name}_subcommands
      ;;
"""
        case_statements = []
        for subcmd in self.sub_commands:
            case_statements.append(f"{indent * 4}{subcmd.name})\n")
            if subcmd.options:
                subcmd_depth = subcmd.command_depth()
                if subcmd_depth == 0:
                    argument_src = subcmd.arguments_with_options(indent_length=5, context_flag=False)  # noqa
                    case_statements.append(argument_src)
                else:
                    subcmd_func_name = f"{func_name}_{subcmd.name}"
                    main_function = subcmd.generate_main_function(subcmd_func_name) + "\n" + main_function  # noqa
                    case_statements.append(f"{indent * 5}_{subcmd_func_name}")
            case_statements.append(f"\n{indent * 5};;\n")
        case_section = "".join(case_statements)

        main_function += f"""
    args)
      case $words[1] in
{case_section}
      esac
      ;;
  esac
}}
"""
        return subcmd_comp_code + "\n" + main_function

    def generate_non_subcommand_completion(self) -> str:
        shell_source = self.shell_source_used_by_options()
        content = self.arguments_with_options(indent_length=1)
        source_to_write = f"_{self.name}() {{\n{content}\n}}"
        return "\n\n".join(shell_source + [source_to_write])

    def generate_completion_function(self) -> str:
        """Generate the main completion function for current command."""
        depth = self.command_depth()
        if depth == 0:  # no sub-commands, simplest case
            return self.generate_non_subcommand_completion()
        else:
            shell_source = self.shell_source_used_by_options(recursive=True)
            shell_source = "\n".join(shell_source)
            main_function = self.generate_main_function()
            return f"{shell_source}\n{main_function}"

    def complete_source(self, as_file: bool = False) -> str:
        """Generate the completion source code for current command."""
        completion_code = self.generate_completion_function()
        if as_file:
            completion_code = f"#compdef {self.name}\n\n{completion_code}\n_{self.name}"
        return completion_code

    def completion_entry(self, output_dir: str = "~/.zsh/Completion"):
        """Generate completion script for a Command with sub-commands."""
        output_dir = os.path.expanduser(output_dir)

        completion_code = self.complete_source(as_file=True)

        # write to file
        comp_file = os.path.join(output_dir, f"_{self.name}")
        with open(comp_file, "w") as f:
            f.write(completion_code)

        print(f"Completion file created at: {comp_file}")
        print(f"Please add `compdef _{self.name} {self.name}` to your zsh config.")

    def __eq__(self, other) -> bool:
        def sort_cmd(cmds: list[Command]) -> list[Command]:
            return sorted(cmds, key=lambda cmd: cmd.name)

        if not isinstance(other, Command):
            return False
        for attr in vars(self):
            self_val = getattr(self, attr)
            other_val = getattr(other, attr)
            if attr == "sub_commands":
                if sort_cmd(self_val) != sort_cmd(other_val):
                    return False
            elif self_val != other_val:
                return False
        return True
