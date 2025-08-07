import os

from zcompy import Command
from zcompy.action import Files, GitBranches
from zcompy.option import Option


def test_deep_nested_command():
    """Test that subcommand names are returned in correct order."""
    cmd = Command("test", "Test command")
    cmd.add_options(Option("--verbose", "Enable verbose output"))
    cmd.add_options(Option("--config", "Config file", complete_func=Files()))

    sub1 = Command("sub1", "Level 1 sub1 command")
    sub1.add_options(Option("--output", "Output directory", complete_func=Files(dir_only=True)))

    sub2 = Command("sub2", "Level 1 sub2 command")
    sub2.add_options(Option("--optimize", "Optimization level"))
    sub2.add_positional_args(GitBranches())

    sub1a = Command("sub1a", "Level 2 sub1a command")
    sub1a.add_options(Option("--pattern", "Test pattern"))
    sub1b = Command("sub1b", "Level 2 sub1b command")
    sub1b.add_options(Option("--coverage", "Generate coverage report"))

    sub1a1 = Command("sub1a1", "Level 3 sub1a1 command")
    sub1a1.add_options(Option("--server", "Deployment server"))
    sub1a2 = Command("sub1a2", "Level 3 sub1a2 command")
    sub1a2.add_options(Option("--port", "Server port"))

    leaf1 = Command("leaf", "Level 4 leaf command")
    leaf1.add_options(Option("--dry-run", "Show what would be deployed"))
    leaf1.add_positional_args(Files())

    cmd.add_sub_commands([sub1, sub2])
    sub1.add_sub_commands([sub1a, sub1b])
    sub1a.add_sub_commands([sub1a1, sub1a2])
    sub1a1.add_sub_commands(leaf1)

    source = cmd.complete_source(as_file=False)
    with open(os.path.join(os.path.dirname(__file__), "_test"), "r") as f:
        answer = f.read()

    content = [x for x in source.splitlines() if x.strip()]
    answer = [x for x in answer.splitlines() if x.strip()][1:-1]
    for x, y in zip(content, answer):
        assert x == y, f"Expected: {x}, but got: {y}"
