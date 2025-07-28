import pytest

from zcompy.action import Hosts, OSEnv, ProcessID, URLs, UserNames


@pytest.mark.parametrize("cls, expected_type_hint, expected_action_source", [
    (URLs, "URLs", "_urls"),
    (OSEnv, "Environment variable", "_parameters"),
    (ProcessID, "Process ID", "_pids"),
    (UserNames, "User name", "_users"),
    (Hosts, "Host name", "_hosts"),
])
def test_simple_action_type(cls, expected_type_hint, expected_action_source):
    instance = cls()
    assert instance.type_hint() == expected_type_hint
    assert instance.action_source() == expected_action_source
