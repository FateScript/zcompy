#!/usr/bin/env python3

import pytest

from zcompy import Completion, Files, Option


def test_option_creation_with_completion():
    """Test Option creation with completion function."""
    with pytest.raises(ValueError):
        completion = Completion(lambda: ["choice1", "choice2"])
        option = Option(("--choice",), "Select choice", type="CHOICE", complete_func=completion)
        option.to_complete_argument()


@pytest.mark.parametrize("flags, description, expected", [
    (("-h",), "Show help", "'(-h)'-h'[Show help]'"),
    (("--help", "-h"), "Show help", "'(--help -h)'{--help,-h}'[Show help]'"),
    (("--help",), "Show help", "'(--help)'--help'[Show help]'"),
])
def test_option_to_complete_argument_variants(flags, description, expected):
    option = Option(flags, description)
    result = option.to_complete_argument()
    assert result == expected


@pytest.mark.parametrize("flags, description, expected", [
    (("--test",), "It's a test", "'(--test)'--test'[It'\\''s a test]'"),
    (("",), "Empty string flag", "'()''[Empty string flag]'"),
    (("--über",), "Über option", "'(--über)'--über'[Über option]'"),
])
def test_option_edge_cases(flags, description, expected):
    option = Option(flags, description)
    result = option.to_complete_argument()
    assert result == expected


@pytest.mark.parametrize("flags, description, type_, expected", [
    (("--file", "-f"), "Input file", "FILE", "'(--file -f)'{--file,-f}'[Input file]'"),
    (("--output", "-o"), "Output file", "FILE", "'(--output -o)'{--output,-o}'[Output file]'"),
])
def test_option_creation_with_type(flags, description, type_, expected):
    """Test Option creation with type specified."""
    option = Option(flags, description, type=type_)
    result = option.to_complete_argument()
    assert result == expected


@pytest.mark.parametrize("flags, description, complete_func, expected", [
    (
        ("--config",), "Config file", Completion(Files()),
        "'(--config)'--config'[Config file]:Files:_files'",
    ),
    (
        ("--config",), "Config file", Files(dir_only=True),
        "'(--config)'--config'[Config file]:Directory:_files -/'",
    ),
],
)
def test_option_to_with_no_type_info(flags, description, complete_func, expected):
    option = Option(flags, description, complete_func=complete_func)
    result = option.to_complete_argument()
    assert result == expected


def test_option_to_complete_argument_with_custom_completion():
    """Test to_complete_argument method with custom completion function."""

    def custom_func():
        return ["item1", "item2"]

    custom_completion = Completion(custom_func)
    option = Option(("--choice",), "Custom choice", type="CHOICE", complete_func=custom_completion)
    result = option.to_complete_argument()

    assert result == "'(--choice)'--choice'[Custom choice]:CHOICE:_custom_func'"


@pytest.mark.parametrize("flags, description, allow_repeat, expected", [
    (("--verbose", "-v"), "Verbose output", True, "'*'{--verbose,-v}'[Verbose output]'"),
    (("-v",), "Verbose output", True, "'*-v[Verbose output]'"),
    (("--verbose",), "Verbose output", True, "'*--verbose[Verbose output]'"),
])
def test_option_with_allow_repeat(flags, description, allow_repeat, expected):
    option = Option(flags, description, allow_repeat=allow_repeat)
    result = option.to_complete_argument()
    assert result == expected
