from __future__ import annotations

from dataclasses import dataclass

from absl.flags import FLAGS, FlagValues

from zcompy import Command, Completion, Option

# code to refer for absl
# https://github.com/abseil/abseil-py/blob/1952c49b72a4a3cd88e8d1ddc6fb0230e37e5390/absl/flags/__init__.py#L123
# https://github.com/abseil/abseil-py/blob/1952c49b72a4a3cd88e8d1ddc6fb0230e37e5390/absl/app.py#L48-L77


def is_alias_flag(flag) -> bool:
    """Check if a flag is an alias flag."""
    if hasattr(flag, "help"):
        return flag.help.startswith("Alias for --")
    return False


def alias_of(flag) -> str:
    assert is_alias_flag(flag)
    alias = flag.help[len("Alias for --"):].strip().rstrip(".")
    return alias


@dataclass
class AbslFlagsCommand:
    name: str
    flags: FlagValues = None

    def __post_init__(self):
        self.name = "_".join(self.name.split())  # ensure no space in name
        if self.flags is None:
            self.flags = FLAGS

    def to_command(self) -> Command:
        """Convert ABSL flags to a Command object with completion support."""
        command = Command(name=self.name, description="Command with flag-based completion")

        alias_mapping = {}
        for flag_name in self.flags:
            flag = self.flags[flag_name]
            if is_alias_flag(flag):
                alias_mapping[f"-{flag_name}"] = f"--{alias_of(flag)}"
                continue
            option = self.create_option_from_flag(flag)
            command.add_options(option)

        # add alias in option
        for alias, original in alias_mapping.items():
            for opt in command.options:
                if original in tuple(opt.names):
                    opt.names = tuple(opt.names) + (alias,)

        return command

    def create_option_from_flag(self, flag) -> Option:
        """Create an Option from an ABSL flag."""
        flag_name = flag.name
        option_names = [f"--{flag_name}"]
        flag_help = flag.help or f"Flag {flag_name}"
        if all(x in flag_help for x in ["<", ">", "|", ":"]):  # for enum option
            flag_help = flag_help.split(":", maxsplit=1)[1].strip()
        completion = self._get_completion_for_flag(flag)

        return Option(
            names=tuple(option_names),
            description=flag_help,
            complete_func=completion
        )

    def _get_completion_for_flag(self, flag) -> Completion | None:
        """Determine appropriate completion for a flag based on its type."""
        default_value = str(flag.default) if flag.default is not None else ""
        flag_type = type(flag).__name__

        # enum class flags
        if hasattr(flag, 'parser') and hasattr(flag.parser, 'enum_class'):
            enum_class = flag.parser.enum_class
            if hasattr(enum_class, '__members__'):
                choices = tuple(str(e.value) for e in enum_class.__members__.values())
                return Completion(func=choices)

        # enum flags - check parser for choices
        if hasattr(flag, 'parser') and hasattr(flag.parser, 'enum_values'):
            choices = tuple(str(val) for val in flag.parser.enum_values)
            return Completion(func=choices)
        elif hasattr(flag, 'parser') and hasattr(flag.parser, 'choices'):
            choices = tuple(str(val) for val in flag.parser.choices)
            return Completion(func=choices)
        elif 'Enum' in flag_type:
            # Try to extract choices from help text for enum flags
            if flag.help and '|' in flag.help:
                choices_part = flag.help.split(':')[0] if ':' in flag.help else flag.help
                choices_part = choices_part.strip('<>')
                choices = tuple(choice.strip() for choice in choices_part.split('|'))
                return Completion(func=choices)

        # boolean flags
        if flag_type in ('BooleanFlag', 'bool') or flag.flag_type == 'bool':
            return None

        # integer flags
        if flag_type in ('IntegerFlag', 'int') or flag.flag_type == 'int':
            return Completion(func=(default_value,))

        # float flags
        if flag_type in ('FloatFlag', 'float') or flag.flag_type == 'float':
            return Completion(func=(default_value,))

        # string flags with suggestions from default
        if flag_type in ('StringFlag', 'str') or flag.flag_type == 'string':
            # For string flags, provide the default as a suggestion
            default_value = default_value or ""
            return Completion(func=(default_value,))

        # unknown types
        return Completion(func=(default_value,))
