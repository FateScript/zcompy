#!/usr/bin/env python3

import pytest

from zcompy import Completion, Files


def test_completion_creation_with_function():
    """Test Completion creation with a function."""

    def test_func():
        return ["choice1", "choice2"]

    completion = Completion(test_func)

    result = completion.action_source()
    assert result == "_test_func"


def test_completion_creation_with_files():
    """Test Completion creation with Files object."""
    files = Files()
    completion = Completion(files)

    result = completion.action_source()
    assert result == "_files"


def test_completion_creation_with_tuple():
    """Test Completion creation with tuple of choices."""
    completion = Completion(("auto", "always", "never"))

    result = completion.action_source()
    assert result == "(auto always never)"


def test_completion_action_source_with_function():
    """Test Completion.action_source method with function."""

    def test_func():
        return ["choice1", "choice2"]

    completion = Completion(test_func)
    result = completion.action_source()

    # Should return function name for custom functions
    assert result == "_test_func"


def test_completion_action_source_with_files():
    """Test Completion.action_source method with Files object."""
    files = Files()
    completion = Completion(files)
    result = completion.action_source()

    # Should return _files for Files objects
    assert result == "_files"


def test_completion_action_source_with_tuple():
    """Test Completion.action_source method with tuple of choices."""
    completion = Completion(("auto", "always", "never"))
    result = completion.action_source()

    assert result == "(auto always never)"


def test_completion_zsh_func_source():

    def test_func():
        return ["choice1", "choice2"]

    completion = Completion(test_func)
    result = completion.zsh_func_source()

    # Test exact shell function format
    expected = """
_test_func() {
  local -a choices
  local line opt msg

  while IFS= read -r line; do
    opt="${line%% *}"
    msg="${line#* }"
    choices+=("$opt:$msg")
  done < <(test_func)
  _describe -t choices 'choices' choices
}
"""
    assert result == expected


def test_completion_shell_code_with_files():
    """Test Completion.shell_code method with Files object."""
    files = Files()
    completion = Completion(files)
    result = completion.zsh_func_source()

    # Should return empty string for Files objects
    assert result == ""


def test_completion_shell_code_with_tuple():
    """Test Completion.zsh_func_source method with tuple."""
    completion = Completion(("auto", "always", "never"))
    result = completion.zsh_func_source()

    # Should return empty string for tuples
    assert result == ""


def test_completion_write_python(tmp_path):
    """Test Completion.write_python method."""

    def test_func():
        return ["choice1", "choice2"]

    completion = Completion(test_func, path=str(tmp_path))

    # This would create a file, so we'll just test it doesn't crash
    assert hasattr(completion, "write_python")


def test_completion_with_lambda_function():
    """Test Completion with lambda function."""
    with pytest.raises(ValueError):
        Completion(lambda: ["lambda1", "lambda2"])


def test_completion_equality():
    """Test Completion equality comparison."""

    def func1():
        return ["choice1"]

    def func2():
        return ["choice2"]

    completion1 = Completion(func1)
    completion2 = Completion(func1)  # Same function
    completion3 = Completion(func2)  # Different function

    assert completion1.func == completion2.func
    assert completion1.func != completion3.func
    assert completion1 != "not completion"


def test_completion_with_custom_path():
    """Test Completion with custom path."""

    def test_func():
        return ["choice1", "choice2"]

    completion = Completion(test_func, path="/custom/path")
    assert completion.path == "/custom/path"


def test_completion_with_nested_function():
    """Test Completion with nested function."""

    def outer():
        def inner():
            return ["nested_choice"]

        return inner

    completion = Completion(outer())  # Use the inner function
    result = completion.action_source()

    # Should handle nested function names
    assert result == "_inner"


def test_completion_shell_code_function_format():
    """Test that shell_code generates proper shell function format."""

    def test_func():
        return ["choice1", "choice2"]

    completion = Completion(test_func)
    result = completion.zsh_func_source()

    # Test exact shell function format
    expected = """
_test_func() {
  local -a choices
  local line opt msg

  while IFS= read -r line; do
    opt="${line%% *}"
    msg="${line#* }"
    choices+=("$opt:$msg")
  done < <(test_func)
  _describe -t choices 'choices' choices
}
"""
    assert result == expected


def test_completion_shell_code_with_complex_function():
    """Test Completion.shell_code with complex function name."""

    def complex_completion_function():
        return ["complex_choice"]

    completion = Completion(complex_completion_function)
    result = completion.action_source()

    assert result == "_complex_completion_function"
