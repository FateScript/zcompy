from __future__ import annotations

from dataclasses import dataclass

from .action import Action

__all__ = ["Option"]


@dataclass
class Option:
    """Class to represent an option with its attributes."""

    names: tuple[str, ...] | str
    description: str = ""
    type: str = ""
    complete_func: Action | None = None
    allow_repeat: bool = False

    def to_complete_argument(self) -> str:
        if isinstance(self.names, str):  # ensure tuple type
            self.names = (self.names,)

        opt_name = sorted(self.names, key=len, reverse=True)  # long term first
        opt_text = opt_name[0] if len(opt_name) == 1 else "{" + ",".join(opt_name) + "}"
        if self.allow_repeat:
            opt_text = f"*{opt_text}" if len(opt_name) == 1 else f"*'{opt_text}'"
        else:
            prefix = "(" + " ".join(opt_name) + ")"
            opt_text = f"{prefix}'{opt_text}'"

        desc = self.description
        if "'" in desc:
            desc = desc.replace("'", r"'\''")

        comp_func = ""
        if self.complete_func:
            if not self.type:
                self.type = self.complete_func.type_hint()
            assert self.type, "Option type must be specified if a function is provided"
            comp_func = f":{self.type}:{self.complete_func.action_source()}"

        return f"'{opt_text}[{desc}]{comp_func}'"
