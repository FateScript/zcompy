#!/usr/bin/env python3
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .option import Option

__all__ = ["Command"]


@dataclass
class Command:
    """Class to represent a command with sub-commands and options."""

    name: str
    description: str = ""
    options: list[Option] = field(default_factory=list)
    sub_commands: list[Command] = field(default_factory=list)

    def add_options(self, options: Option | list[Option]):
        """Add an option to this command."""
        if isinstance(options, Option):
            self.options.append(options)
        else:
            self.options.extend(options)

    def add_sub_command(self, sub_command: Command):
        """Add a sub-command to this command."""
        self.sub_commands.append(sub_command)

    def get_all_sub_command_names(self) -> list[str]:
        """Get all sub-command names recursively."""
        names = []
        for sub_cmd in self.sub_commands:
            names.append(sub_cmd.name)
            # Add nested sub-commands if needed
            if sub_cmd.sub_commands:
                for nested_sub_cmd in sub_cmd.sub_commands:
                    names.append(f"{sub_cmd.name} {nested_sub_cmd.name}")
        return names

    def subcommand_completion(self, indent=2) -> str:
        """Generate completion code for sub-commands."""
        if not self.sub_commands:
            return ""

        subcmd_descs = [f'"{x.name}:{x.description}"' for x in self.sub_commands]
        subcmds = "\n".join([f"{' ' * 2 * indent}{desc}" for desc in subcmd_descs])

        completion_code = f"""
_{self.name}_subcommands() {{
  local -a subcmds
  subcmds=(
{subcmds}
  )
  _describe -t subcommands 'subcommands' subcmds
}}
"""
        return completion_code

    def complete_source(self, as_file: bool = False) -> str:
        """Generate the completion source code for this command."""
        # Generate all completion code
        completion_code = ""

        completion_code += self.subcommand_completion()
        completion_code += "\n"

        # Add main completion function
        completion_code += generate_completion_function(self)
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

    def generate_non_subcommand_completion(self, indent_length=2) -> str:
        assert len(self.sub_commands) == 0, "Not a subcommand type."
        indent = " " * indent_length
        if not self.options:
            raise ValueError("Command must have at least one option to generate completion.")

        options_source = [opt.to_complete_argument() for opt in self.options]
        opt_text = "\\\n".join([indent * 2 + opt for opt in options_source])
        shell_source = [x.complete_func.zsh_func_source() for x in self.options if x.complete_func]

        source = """
{func_name}() {{
  _arguments \\
{content}
}}
"""
        source_to_write = source.format(func_name=f"_{self.name}", content=opt_text)
        return "\n\n".join(shell_source + [source_to_write])


def generate_completion_function(command: Command, indent_length=2) -> str:
    """Generate the main completion function for the command."""
    if not command.sub_commands:
        return command.generate_non_subcommand_completion(indent_length)

    zsh_line = "\\\n"
    indent = " " * indent_length
    options_parts = [opt.to_complete_argument() for opt in command.options]

    shell_source = [x.complete_func.zsh_func_source() for x in command.options if x.complete_func]
    options_section = f" {zsh_line}{indent * 2}".join(options_parts)
    subcmd_section = f" {zsh_line}{indent * 2}'1: :->cmds' {zsh_line}{indent * 2}'*:: :->args'"  # noqa

    main_function = f"""
_{command.name}() {{
  local state

  _arguments -C {zsh_line}    {options_section}{subcmd_section}

  case $state in
    cmds)
      _{command.name}_subcommands
      ;;
"""

    case_statements = []
    for subcmd in command.sub_commands:
        if subcmd.options:
            option_parts = [opt.to_complete_argument() for opt in subcmd.options]
            shell_source.extend(
                [opt.complete_func.zsh_func_source() for opt in subcmd.options if opt.complete_func]
            )
            option_args = f" {zsh_line}{indent * 6}".join(option_parts)
            case_statements.append(
                f"{indent * 4}{subcmd.name})\n{indent * 5}_arguments {zsh_line}{indent * 6}{option_args}\n{indent * 5};;\n"
            )
        else:
            case_statements.append(f"{indent * 4}{subcmd.name})\n{indent * 5};;\n")
    case_section = "".join(case_statements)

    main_function += f"""
    args)
      case $words[1] in
{case_section}
      esac
      ;;
"""

    main_function += f"\n{indent}esac\n}}\n"

    shell_source = "\n".join([x for x in shell_source if x])
    return shell_source + "\n" + main_function
