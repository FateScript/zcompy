from zcompy.action import Files, ProcessID, URLs
from zcompy.command import Command
from zcompy.option import Option


def find_option_by_name(options, target_name):
    """Helper function to find an option by name, handling both string and tuple formats."""
    for opt in options:
        if isinstance(opt.names, str):
            if opt.names == target_name:
                return opt
        else:
            if target_name in opt.names:
                return opt
    raise StopIteration


def test_add_action_for_options_single_option():
    """Test adding action to a single option."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option("--file", "Input file"))
    cmd.add_options(Option("--output", "Output file"))

    file_action = Files()
    cmd.add_action_for_options("--file", action=file_action)

    file_option = find_option_by_name(cmd.options, "--file")
    output_option = find_option_by_name(cmd.options, "--output")

    assert file_option.complete_func is file_action
    assert output_option.complete_func is None


def test_add_action_for_options_multiple_options():
    """Test adding action to multiple options at once."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option("--file", "Input file"))
    cmd.add_options(Option("--output", "Output file"))
    cmd.add_options(Option("--config", "Config file"))
    cmd.add_options(Option("--verbose", "Verbose output"))

    file_action = Files()
    cmd.add_action_for_options("--file", "--output", "--config", action=file_action)

    file_option = find_option_by_name(cmd.options, "--file")
    output_option = find_option_by_name(cmd.options, "--output")
    config_option = find_option_by_name(cmd.options, "--config")
    verbose_option = find_option_by_name(cmd.options, "--verbose")

    assert file_option.complete_func is file_action
    assert output_option.complete_func is file_action
    assert config_option.complete_func is file_action
    assert verbose_option.complete_func is None


def test_add_action_for_options_with_short_names():
    """Test adding action using short option names."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option(("-f", "--file"), "Input file"))
    cmd.add_options(Option(("-o", "--output"), "Output file"))

    file_action = Files()
    cmd.add_action_for_options("-f", action=file_action)

    file_option = find_option_by_name(cmd.options, "-f")
    output_option = find_option_by_name(cmd.options, "-o")

    assert file_option.complete_func is file_action
    assert output_option.complete_func is None


def test_add_action_for_options_mixed_names():
    """Test adding action using both short and long names."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option(("-f", "--file"), "Input file"))
    cmd.add_options(Option(("-o", "--output"), "Output file"))
    cmd.add_options(Option("--config", "Config file"))

    file_action = Files()
    cmd.add_action_for_options("-f", "--output", action=file_action)

    file_option = find_option_by_name(cmd.options, "-f")
    output_option = find_option_by_name(cmd.options, "-o")
    config_option = find_option_by_name(cmd.options, "--config")

    assert file_option.complete_func is file_action
    assert output_option.complete_func is file_action
    assert config_option.complete_func is None


def test_add_action_for_options_nonexistent():
    """Test adding action to non-existent options (should be handled gracefully)."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option("--real", "Real option"))

    file_action = Files()
    cmd.add_action_for_options("--fake", "--also-fake", "--real", action=file_action)

    real_option = find_option_by_name(cmd.options, "--real")
    assert real_option.complete_func is file_action


def test_add_action_for_options_recursive():
    """Test recursive action addition to sub-commands."""
    cmd = Command("maincmd", "Main command")
    cmd.add_options(Option("--file", "Input file"))

    sub1 = Command("sub1", "Subcommand 1")
    sub1.add_options(Option("--input", "Input file for sub1"))
    sub1.add_options(Option("--config", "Config file for sub1"))

    sub2 = Command("sub2", "Subcommand 2")
    sub2.add_options(Option("--output", "Output file for sub2"))
    sub2.add_options(Option("--log", "Log file for sub2"))

    cmd.add_sub_commands([sub1, sub2])

    file_action = Files()
    cmd.add_action_for_options("--input", "--output", action=file_action, recursive=True)

    # Check main command (should not be affected)
    main_file_option = find_option_by_name(cmd.options, "--file")
    assert main_file_option.complete_func is None

    # Check sub1
    sub1_input = find_option_by_name(sub1.options, "--input")
    sub1_config = find_option_by_name(sub1.options, "--config")
    assert sub1_input.complete_func is file_action
    assert sub1_config.complete_func is None

    # Check sub2
    sub2_output = find_option_by_name(sub2.options, "--output")
    sub2_log = find_option_by_name(sub2.options, "--log")
    assert sub2_output.complete_func is file_action
    assert sub2_log.complete_func is None


def test_add_action_for_options_recursive_nested():
    """Test recursive action addition with nested sub-commands."""
    cmd = Command("maincmd", "Main command")

    level1 = Command("level1", "Level 1 subcommand")
    level1.add_options(Option("--file", "File option"))

    level2 = Command("level2", "Level 2 subcommand")
    level2.add_options(Option("--input", "Input option"))
    level2.add_options(Option("--file", "Another file option"))

    level1.add_sub_commands(level2)
    cmd.add_sub_commands(level1)

    file_action = Files()
    cmd.add_action_for_options("--file", action=file_action, recursive=True)

    # Check level1
    level1_file = find_option_by_name(level1.options, "--file")
    assert level1_file.complete_func is file_action

    # Check level2
    level2_file = find_option_by_name(level2.options, "--file")
    level2_input = find_option_by_name(level2.options, "--input")
    assert level2_file.complete_func is file_action
    assert level2_input.complete_func is None


def test_add_action_for_options_overwrite():
    """Test that adding action overwrites existing actions."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option("--file", "Input file"))

    file_action = Files()
    url_action = URLs()

    # First add file action
    cmd.add_action_for_options("--file", action=file_action)

    file_option = find_option_by_name(cmd.options, "--file")
    assert file_option.complete_func is file_action

    # Then overwrite with URL action
    cmd.add_action_for_options("--file", action=url_action)

    file_option = find_option_by_name(cmd.options, "--file")
    assert file_option.complete_func is url_action


def test_add_action_for_options_single_string_option():
    """Test adding action to a single option with string name instead of tuple."""
    cmd = Command("testcmd", "Test command")
    # Add option with string name instead of tuple
    option = Option("--file", "Input file")
    option.names = "--file"  # Ensure it's a string
    cmd.add_options(option)

    file_action = Files()
    cmd.add_action_for_options("--file", action=file_action)

    file_option = find_option_by_name(cmd.options, "--file")
    assert file_option.complete_func is file_action


def test_add_action_for_options_empty_options():
    """Test adding action with empty options list."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option("--file", "Input file"))

    file_action = Files()
    cmd.add_action_for_options(action=file_action)  # No option names provided

    file_option = find_option_by_name(cmd.options, "--file")
    assert file_option.complete_func is None


def test_add_action_for_options_multiple_actions():
    """Test adding different actions to different sets of options."""
    cmd = Command("testcmd", "Test command")
    cmd.add_options(Option("--file", "Input file"))
    cmd.add_options(Option("--url", "URL to process"))
    cmd.add_options(Option("--pid", "Process ID"))
    cmd.add_options(Option("--verbose", "Verbose output"))

    file_action = Files()
    url_action = URLs()
    pid_action = ProcessID()

    cmd.add_action_for_options("--file", action=file_action)
    cmd.add_action_for_options("--url", action=url_action)
    cmd.add_action_for_options("--pid", action=pid_action)

    file_option = find_option_by_name(cmd.options, "--file")
    url_option = find_option_by_name(cmd.options, "--url")
    pid_option = find_option_by_name(cmd.options, "--pid")
    verbose_option = find_option_by_name(cmd.options, "--verbose")

    assert file_option.complete_func is file_action
    assert url_option.complete_func is url_action
    assert pid_option.complete_func is pid_action
    assert verbose_option.complete_func is None


def test_repeat_positional_args():
    """Test adding repeat positional arguments."""
    answer = r"""
_testcmd() {
  _arguments \
    '*:Directory:_files -/'
}
"""
    cmd = Command("testcmd", "Test command", repeat_pos_args=Files(dir_only=True))
    source = cmd.complete_source()
    answer_lines = [x for x in answer.splitlines() if x.strip()]
    source_lines = [x for x in source.splitlines() if x.strip()]
    for x, y in zip(source_lines, answer_lines):
        assert x == y, f"Mismatch at line:\nExpected: {y}\nGot: {x}"


def test_nested_command_generate_func():
    """Test that subcommand names are returned in correct order."""
    sub_cmd = r"""
_sub1_subcommands() {
  local -a subcmds
  subcmds=(
    "sub1a:Create an environment based on an environment file"
    "sub1b:Export a given environment"
  )
  _describe -t subcommands 'subcommands' subcmds
}
"""

    body = r"""
_sub1() {
  local state
  _arguments -C \
    '(--output)'--output'[Output directory]:Directory:_files -/' \
    '1: :->cmds' \
    '*:: :->args'

  case $state in
    cmds)
      _sub1_subcommands
      ;;
    args)
      case $words[1] in
        sub1a)
          _arguments \
            '(--pattern)'--pattern'[Pattern for sub1a]:Files:_files'
          ;;
        sub1b)
          _arguments \
            '(--bopt)'--bopt'[Bopt for sub1b]'
          ;;
      esac
      ;;

  esac
}
"""
    answer = sub_cmd + body
    sub1 = Command("sub1", "Level 1 sub1 command")
    sub1.add_options(Option("--output", "Output directory", complete_func=Files(dir_only=True)))

    sub1a = Command("sub1a", "Create an environment based on an environment file")
    sub1a.add_options(Option("--pattern", "Pattern for sub1a", complete_func=Files()))
    sub1b = Command("sub1b", "Export a given environment")
    sub1b.add_options(Option("--bopt", "Bopt for sub1b"))

    sub1.add_sub_commands([sub1a, sub1b])

    src = sub1.generate_main_function()
    src_lines = [x for x in src.splitlines() if x.strip()]
    answer_lines = [x for x in answer.splitlines() if x.strip()]
    for x, y in zip(src_lines, answer_lines):
        assert x == y, f"Mismatch at line:\nExpected: {y}\nGot: {x}"

    src = [x for x in sub1.subcommand_completion().splitlines() if x.strip()]
    answer = [x for x in sub_cmd.splitlines() if x.strip()]
    for x, y in zip(src, answer):
        assert x == y, f"Mismatch at line:\nExpected: {y}\nGot: {x}"
