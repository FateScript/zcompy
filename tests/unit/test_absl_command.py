
from absl import flags
from enum import Enum

from zcompy import Option, Completion, Command
from zcompy.absl_command import AbslFlagsCommand


class Mode(Enum):
    O1 = 'o1'
    O2 = 'o2'
    O3 = 'o3'


flags.DEFINE_string('name', 'World', 'The name to greet')
flags.DEFINE_integer('count', 1, 'The number of greetings')
flags.DEFINE_bool('verbose', False, 'Whether to display verbose output')
flags.DEFINE_alias('v', 'verbose')
flags.DEFINE_enum('color', 'blue', ['red', 'blue', 'green'], 'Choose a color')
flags.DEFINE_enum_class('check_mode', Mode.O1, Mode, 'Select a mode')


def test_absl_generate():
    """Test that AbslFlagsCommand properly converts ABSL flags to Command."""
    cmd = AbslFlagsCommand(name="hello").to_command()
    assert isinstance(cmd, Command)

    # Check that we have the expected flags
    flag_names = {opt.names[0] for opt in cmd.options}
    expected_flags = {'--name', '--count', '--verbose', '--color', '--check_mode'}
    assert expected_flags.issubset(flag_names)

    options_by_name = {opt.names[0]: opt for opt in cmd.options}

    # Test string flag
    name_opt = options_by_name['--name']
    assert name_opt.description == 'The name to greet'
    assert isinstance(name_opt.complete_func, Completion)
    assert name_opt.complete_func.func == ("World",)
    assert name_opt.names == ('--name',)

    # Test integer flag
    count_opt = options_by_name['--count']
    assert count_opt.description == 'The number of greetings'
    assert isinstance(count_opt.complete_func, Completion)
    assert count_opt.complete_func.func == ("1",)
    assert count_opt.names == ('--count',)

    # Test boolean flag
    verbose_opt = options_by_name['--verbose']
    assert verbose_opt.description == 'Whether to display verbose output'
    assert verbose_opt.complete_func is None
    assert verbose_opt.names == ('--verbose', '-v')

    # Test enum flag
    color_opt = options_by_name['--color']
    assert color_opt.description == 'Choose a color'
    assert isinstance(color_opt.complete_func, Completion)
    assert color_opt.complete_func.func == ('red', 'blue', 'green')
    assert color_opt.names == ('--color',)

    # Test enum class flag
    mode_opt = options_by_name['--check_mode']
    assert mode_opt.description == 'Select a mode'
    assert isinstance(mode_opt.complete_func, Completion)
    assert mode_opt.complete_func.func == ('o1', 'o2', 'o3')
    assert mode_opt.names == ('--check_mode',)


def test_custom_flag_values():
    """Test with custom flag values."""
    # Create a new flags instance for testing
    test_flags = flags.FlagValues()
    flags.DEFINE_string('test_string', 'test_value', 'Test string flag', flag_values=test_flags)
    flags.DEFINE_integer('test_int', 42, 'Test int flag', flag_values=test_flags)
    flags.DEFINE_bool('test_bool', True, 'Test bool flag', flag_values=test_flags)
    flags.DEFINE_enum('test_enum', 'option1', ['option1', 'option2', 'option3'], 'Test enum flag', flag_values=test_flags)

    cmd = AbslFlagsCommand("test_flag", test_flags).to_command()
    assert isinstance(cmd, Command)

    # Verify all flags are present
    flag_names = {opt.names[0] for opt in cmd.options}
    expected = {'--test_string', '--test_int', '--test_bool', '--test_enum'}
    assert expected.issubset(flag_names)

    options_by_name = {opt.names[0]: opt for opt in cmd.options}

    string_opt = options_by_name['--test_string']
    assert 'test_value' in string_opt.complete_func.func

    int_opt = options_by_name['--test_int']
    assert '42' in int_opt.complete_func.func

    bool_opt = options_by_name['--test_bool']
    assert bool_opt.complete_func is None

    enum_opt = options_by_name['--test_enum']
    assert enum_opt.complete_func.func == ('option1', 'option2', 'option3')
