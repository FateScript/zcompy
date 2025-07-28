import pytest

from zcompy.action import Files


@pytest.mark.parametrize("pattern, expected", [
    ("*.txt", "_files -g \"*.txt\""),
    (("*.txt", "*.py"), "_files -g \"(*.txt|*.py)\""),
    ("", "_files"),
    ("**/*.py", "_files -g \"**/*.py\""),
    ("*.über", "_files -g \"*.über\""),
])
def test_files_pattern(pattern, expected):
    """Test Files with different pattern types and edge cases."""
    files = Files(pattern=pattern)
    result = files.action_source()
    assert result == expected


@pytest.mark.parametrize("ignore_pattern, expected", [
    ("*.txt", "_files -F \"*.txt\""),
    (("*.txt", "*.py"), "_files -F \"(*.txt|*.py)\""),
    ("**/*.pyc", "_files -F \"**/*.pyc\""),
    ("*.tmp", "_files -F \"*.tmp\""),
])
def test_files_ignore_pattern(ignore_pattern, expected):
    """Test Files with different ignore pattern types and edge cases."""
    files = Files(ignore_pattern=ignore_pattern)
    result = files.action_source()
    assert result == expected


@pytest.mark.parametrize("pattern, ignore_pattern, expected", [
    ("*.py", "*.pyc", "_files -g \"*.py\" -F \"*.pyc\""),
    (("*.txt", "*.md"), "*.bak", "_files -g \"(*.txt|*.md)\" -F \"*.bak\""),
    ("src/**/*.py", ("*.pyc", "*.pyo"), "_files -g \"src/**/*.py\" -F \"(*.pyc|*.pyo)\""),
])
def test_files_pattern_and_ignore_pattern(pattern, ignore_pattern, expected):
    """Test Files with both pattern and ignore pattern combined."""
    files = Files(pattern=pattern, ignore_pattern=ignore_pattern)
    result = files.action_source()
    assert result == expected


def test_files_default():
    """Test Files.action_source method with default parameters."""
    files = Files()
    result = files.action_source()

    assert result == "_files"


def test_files_dir_only():
    """Test Files.action_source method with dir_only=True."""
    files = Files(dir_only=True)
    result = files.action_source()

    assert result == "_files -/"


def test_files_creation_combined_params():
    """Test Files creation with combined parameters."""
    files = Files(pattern="*.py", dir_only=True)

    with pytest.raises(AssertionError):
        files.action_source()
