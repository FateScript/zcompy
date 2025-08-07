from argparse import ArgumentParser

from zcompy.action import Files, URLs
from zcompy.parser_command import ParserCommand


def test_simple_parser():
    """Test conversion of a simple ArgumentParser."""
    parser = ArgumentParser(prog="testcmd", description="A test command")
    parser.add_argument("-f", "--file", help="Input file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    assert command.name == "testcmd"
    assert command.description == "A test command"
    assert len(command.options) == 2
    assert len(command.sub_commands) == 0

    # Check options
    option_names = [opt.names for opt in command.options]
    assert ("-f", "--file") in option_names
    assert ("-v", "--verbose") in option_names

    # Check file option
    file_option = next(opt for opt in command.options if opt.names == ("-f", "--file"))
    assert file_option.description == "Input file"
    assert file_option.type == ""

    # Check verbose option
    verbose_option = next(opt for opt in command.options if opt.names == ("-v", "--verbose"))
    assert verbose_option.description == "Verbose output"
    command.complete_source()


def test_parser_with_choices():
    """Test parser with choices completion."""
    parser = ArgumentParser(prog="choicecmd")
    parser.add_argument("--mode", choices=["auto", "manual", "disabled"], help="Operation mode")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    assert len(command.options) == 1
    option = command.options[0]
    assert option.names == ("--mode",)
    assert option.type == "choices"
    assert option.complete_func is not None
    assert option.complete_func.func == ("auto", "manual", "disabled")
    command.complete_source()


def test_parser_with_types():
    """Test parser with different option types."""
    parser = ArgumentParser(prog="typecmd")
    parser.add_argument("--count", type=int, help="Count value")
    parser.add_argument("--ratio", type=float, help="Ratio value")
    parser.add_argument("--name", type=str, help="Name string")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    assert len(command.options) == 3

    types_found = {opt.names[0]: opt.type for opt in command.options}
    assert types_found["--count"] == "int"
    assert types_found["--ratio"] == "float"
    assert types_found["--name"] == "str"
    command.complete_source()


def test_subcommands():
    """Test parser with subcommands."""
    parser = ArgumentParser(prog="maincmd")
    parser.add_argument("--global-opt", help="Global option")

    subparsers = parser.add_subparsers(dest="command")

    # Add subcommand 1
    sub1 = subparsers.add_parser("sub1", help="First subcommand")
    sub1.add_argument("--sub1-opt", help="Sub1 option")

    # Add subcommand 2
    sub2 = subparsers.add_parser("sub2", help="Second subcommand")
    sub2.add_argument("--sub2-opt", choices=["a", "b"], help="Sub2 option with choices")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    assert command.name == "maincmd"
    assert len(command.options) == 1  # --global-opt
    assert len(command.sub_commands) == 2  # sub1, sub2

    # Check main command option
    assert command.options[0].names == ("--global-opt",)

    # Check subcommands
    sub_names = [sub.name for sub in command.sub_commands]
    assert "sub1" in sub_names
    assert "sub2" in sub_names

    # Check sub1
    sub1_cmd = next(sub for sub in command.sub_commands if sub.name == "sub1")
    assert sub1_cmd.description == "First subcommand"
    assert len(sub1_cmd.options) == 1
    assert sub1_cmd.options[0].names == ("--sub1-opt",)

    # Check sub2
    sub2_cmd = next(sub for sub in command.sub_commands if sub.name == "sub2")
    assert sub2_cmd.description == "Second subcommand"
    assert len(sub2_cmd.options) == 1
    assert sub2_cmd.options[0].names == ("--sub2-opt",)
    assert sub2_cmd.options[0].type == "choices"
    command.complete_source()


def test_nested_subcommands():
    """Test parser with nested subcommands."""
    parser = ArgumentParser(prog="nestedcmd")

    subparsers = parser.add_subparsers(dest="command")

    # Add parent subcommand
    parent = subparsers.add_parser("parent", help="Parent command")

    # Add nested subcommands to parent
    parent_subparsers = parent.add_subparsers(dest="subcommand")

    child1 = parent_subparsers.add_parser("child1", help="First child")
    child1.add_argument("--child1-opt", help="Child1 option")

    child2 = parent_subparsers.add_parser("child2", help="Second child")
    child2.add_argument("--child2-opt", help="Child2 option")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    assert len(command.sub_commands) == 1  # parent

    parent_cmd = command.sub_commands[0]
    assert parent_cmd.name == "parent"
    assert len(parent_cmd.sub_commands) == 2  # child1, child2

    child_names = [child.name for child in parent_cmd.sub_commands]
    assert "child1" in child_names
    assert "child2" in child_names


def test_empty_parser():
    """Test empty parser."""
    parser = ArgumentParser(prog="command")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    assert command.name == "command"  # default name
    assert command.description == ""
    assert len(command.options) == 0
    assert len(command.sub_commands) == 0
    answer = """
_command() {
  _arguments
}
""".strip()
    src = command.complete_source().strip()
    assert src == answer


def test_custom_completion_function():
    """Test parser with custom completion function."""

    def custom_complete():
        return ["choice1", "choice2"]

    parser = ArgumentParser(prog="customcmd")
    parser.add_argument("--custom", help="Custom completion")

    parser_command = ParserCommand(parser)
    parser_command.add_action_for_options("--custom", action=custom_complete)
    command = parser_command.to_command()

    custom_option = next(opt for opt in command.options if opt.names == ("--custom",))
    assert custom_option.complete_func is not None
    assert custom_option.complete_func.func == custom_complete
    command.complete_source()


def test_completion_code_generation():
    """Test that completion code can be generated."""
    parser = ArgumentParser(prog="testcmd")
    parser.add_argument("-f", "--file", help="Input file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command")
    sub1 = subparsers.add_parser("sub1", help="First subcommand")
    sub1.add_argument("--sub1-opt", help="Sub1 option")

    parser_command = ParserCommand(parser)
    command = parser_command.to_command()

    # This should not raise an exception
    completion_code = command.complete_source()

    assert isinstance(completion_code, str)
    assert "testcmd" in completion_code
    assert "sub1" in completion_code
    command.complete_source()


def test_add_action_for_options():
    """Test adding actions to options using add_action_for_options."""
    parser = ArgumentParser(prog="testcmd")
    parser.add_argument("-f", "--file", help="Input file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser_command = ParserCommand(parser)
    file_action = Files()
    parser_command.add_action_for_options("--file", "--output", action=file_action)
    command = parser_command.to_command()

    # Check that file and output options have the correct completion
    file_option = next(opt for opt in command.options if opt.names == ("-f", "--file"))
    output_option = next(opt for opt in command.options if opt.names == ("-o", "--output"))
    verbose_option = next(opt for opt in command.options if opt.names == ("-v", "--verbose"))

    assert file_option.complete_func == file_action
    assert output_option.complete_func == file_action
    assert verbose_option.complete_func is None
    command.complete_source()


def test_add_action_for_options_subcommands():
    """Test adding actions to options in subcommands."""
    parser = ArgumentParser(prog="maincmd")
    parser.add_argument("-f", "--file", help="Input file")

    subparsers = parser.add_subparsers(dest="command")

    # Add subcommand with options
    sub1 = subparsers.add_parser("sub1", help="First subcommand")
    sub1.add_argument("--input", help="Input file for sub1")
    sub1.add_argument("--config", help="Config file for sub1")

    parser_command = ParserCommand(parser)

    # Add file completion to --input and --config in sub1
    file_action = Files(dir_only=True)
    parser_command.add_action_for_options("--input", "--config", action=file_action)

    command = parser_command.to_command()

    # Check main command options
    main_file_option = next(opt for opt in command.options if opt.names == ("-f", "--file"))
    assert main_file_option.complete_func is None  # Should not be affected

    # Check subcommand options
    sub1_cmd = next(sub for sub in command.sub_commands if sub.name == "sub1")
    input_option = next(opt for opt in sub1_cmd.options if opt.names == ("--input",))
    config_option = next(opt for opt in sub1_cmd.options if opt.names == ("--config",))

    assert input_option.complete_func == file_action
    assert config_option.complete_func == file_action
    command.complete_source()


def test_add_action_for_options_single_option():
    """Test adding action to a single option."""
    parser = ArgumentParser(prog="testcmd")
    parser.add_argument("--url", help="URL to process")
    parser.add_argument("--name", help="Name of the resource")

    parser_command = ParserCommand(parser)

    # Add URL completion to --url only
    url_action = URLs()
    parser_command.add_action_for_options("--url", action=url_action)

    command = parser_command.to_command()

    url_option = next(opt for opt in command.options if opt.names == ("--url",))
    name_option = next(opt for opt in command.options if opt.names == ("--name",))

    assert url_option.complete_func == url_action
    assert name_option.complete_func is None
    command.complete_source()


def test_add_action_for_options_nonexistent():
    """Test adding action to non-existent options (should be handled gracefully)."""
    parser = ArgumentParser(prog="testcmd")
    parser.add_argument("--real-option", help="A real option")

    parser_command = ParserCommand(parser)

    # Try to add action to non-existent options
    file_action = Files()
    parser_command.add_action_for_options("--nonexistent", "--also-fake", action=file_action)

    command = parser_command.to_command()

    # Should still work without errors
    real_option = next(opt for opt in command.options if opt.names == ("--real-option",))
    assert real_option.complete_func is None
    command.complete_source()


def test_parser_with_complete_source():
    source = r"""
#compdef maincmd

_maincmd_subcommands() {
  local -a subcmds
  subcmds=(
    "sub1:First subcommand"
    "sub2:Second subcommand"
  )
  _describe -t subcommands 'subcommands' subcmds
}

_maincmd() {
  local state

  _arguments -C \
    '(--file -f)'{--file,-f}'[Input file]' \
    '1: :->cmds' \
    '*:: :->args'

  case $state in
    cmds)
      _maincmd_subcommands
      ;;

    args)
      case $words[1] in
        sub1)
          _arguments \
            '(--input -i)'{--input,-i}'[Input file for sub1]:Directory:_files -/' \
            '(--config)'--config'[Config file for sub1]:Directory:_files -/'
          ;;
        sub2)
          _arguments \
            '(--check)'--check'[check output]:URLs:_urls' \
            '(--format)'--format'[output format]'
          ;;

      esac
      ;;

  esac
}

_maincmd
"""
    parser = ArgumentParser(prog="maincmd")
    parser.add_argument("-f", "--file", help="Input file")

    subparsers = parser.add_subparsers(dest="command")

    # Add subcommand with options
    sub1 = subparsers.add_parser("sub1", help="First subcommand")
    sub1.add_argument("-i", "--input", help="Input file for sub1")
    sub1.add_argument("--config", help="Config file for sub1")

    sub2 = subparsers.add_parser("sub2", help="Second subcommand")
    sub2.add_argument("--check", help="check output")
    sub2.add_argument("--format", help="output format")

    parser_command = ParserCommand(parser)

    # Add file completion to --input and --config in sub1
    file_action = Files(dir_only=True)
    parser_command.add_action_for_options("--input", "--config", action=file_action)
    parser_command.add_action_for_options("--check", action=URLs())

    command = parser_command.to_command()
    gen_source = command.complete_source()
    gen_lines = [x for x in gen_source.splitlines() if x]
    source_lines = [x for x in source.splitlines() if x][1:-1]
    for x, y in zip(gen_lines, source_lines):
        assert x == y
