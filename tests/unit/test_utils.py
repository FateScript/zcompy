import pytest

from zcompy.utils import pattern_to_glob, source_by_options_denpendency


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
