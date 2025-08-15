import pytest

from zcompy.utils import pattern_to_glob, source_by_options_denpendency, zsh_completion_function


@pytest.mark.parametrize("pattern,expected", [
    ("*.txt", '"*.txt"'),
    (("*.txt", "*.md"), '"(*.txt|*.md)"'),
    (["*.py", "*.js"], '"(*.py|*.js)"'),
    (None, ""),
])
def test_pattern_to_glob(pattern, expected):
    assert pattern_to_glob(pattern) == expected


@pytest.mark.parametrize("options, expected_source, expected_local_name", [
    ("-a", r'a_value=${opt_args[-a]}', "a_value"),
    (("-a", ), r'a_value=${opt_args[-a]}', "a_value"),
    (("-a", "--full-a"), r'a_value=${opt_args[-a]:-${opt_args[--full-a]}}', "a_value"),
    (("--full-a", "-a"), r'a_value=${opt_args[--full-a]:-${opt_args[-a]}}', "a_value"),
    (["-a", "--full-a"], r'a_value=${opt_args[-a]:-${opt_args[--full-a]}}', "a_value"),
    (
        ("-a", "--full-a", "--fa"),
        r"a_value=${opt_args[-a]:-${opt_args[--full-a]:-${opt_args[--fa]}}}",
        "a_value"
    ),
])
def test_source_by_options_dependency(options, expected_source, expected_local_name):
    src, name = source_by_options_denpendency(options)
    assert src == expected_source, f"Expected: {expected_source}, got: {src}"
    assert name == expected_local_name, f"Expected: {expected_local_name}, got: {name}"


_F_SHELL = r"""
f() {
  local -a choices
  local line opt msg

  while IFS= read -r line; do
    opt="${line%% *}"
    msg="${line#* }"
    choices+=("$opt:$msg")
  done < <(__f)
  _describe -t choices 'choices' choices
}
"""

_F_SHELL_OPT = r"""
f() {
  local -a choices
  local line opt msg
  local a_value
  a_value=${opt_args[-a]:-${opt_args[--full]}}

  while IFS= read -r line; do
    opt="${line%% *}"
    msg="${line#* }"
    choices+=("$opt:$msg")
  done < <(__f "$a_value")
  _describe -t choices 'choices' choices
}
"""


@pytest.mark.parametrize("shell_name, command, dependencies, answer", [
    ("f", "__f", None, _F_SHELL),
    ("f", "__f", ("-a", "--full"), _F_SHELL_OPT),
])
def test_zsh_com_func(shell_name, command, dependencies, answer):
    src = zsh_completion_function(shell_name, command, dependencies)
    assert src.strip() == answer.strip()
