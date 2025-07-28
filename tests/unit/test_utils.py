import pytest
from zcompy.utils import pattern_to_glob


@pytest.mark.parametrize("pattern,expected", [
    ("*.txt", '"*.txt"'),
    (("*.txt", "*.md"), '"(*.txt|*.md)"'),
    (["*.py", "*.js"], '"(*.py|*.js)"'),
    (None, ""),
])
def test_pattern_to_glob(pattern, expected):
    assert pattern_to_glob(pattern) == expected
