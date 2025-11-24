
import click
import cloup

from zcompy.click_command import ClickCommand


@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")


def test_hello_command():
    source = r"""
#compdef hello

_hello() {
  _arguments \
    '(--count)'--count'[Number of greetings.]:Integer:(1)' \
    '(--name)'--name'[The person to greet.]:Text:_default'
}

_hello
"""
    cmd = ClickCommand(hello).to_command()
    generated = cmd.complete_source()
    source_lines = [line for line in source.splitlines() if line.strip()][1:-1]
    generated_lines = [line for line in generated.splitlines() if line.strip()]
    assert len(source_lines) == len(generated_lines)
    for s, g in zip(source_lines, generated_lines):
        assert s.strip() == g.strip()


@cloup.command()
@cloup.option("--foo", help="add1")
@cloup.option("--bar", help="add2", default=10)
@cloup.option(
    '-T',
    '--type',
    type=cloup.Choice(['a', 'b', 'c']),
    required=True,
    help='data type',
)
@cloup.option(
    '--use-foo',
    is_flag=True,
    help='append with foo in the end',
)
def mycmd(foo, bar, type, use_foo):
    """returns the sum of foo and bar as a string, followed by the type"""
    if use_foo:
        return str(foo + bar) + type + " with foo"
    return str(foo + bar) + type


def test_mycmd():
    source = r"""
#compdef mycmd

_mycmd() {
  _arguments \
    '(--foo)'--foo'[add1]:Text:_default' \
    '(--bar)'--bar'[add2]:Integer:(10)' \
    '(--type -T)'{--type,-T}'[data type]:Choices:(a b c)' \
    '(--use-foo)'--use-foo'[append with foo in the end]'
}

_mycmd
"""
    cmd = ClickCommand(mycmd).to_command()
    generated = cmd.complete_source()
    source_lines = [line for line in source.splitlines() if line.strip()][1:-1]
    generated_lines = [line for line in generated.splitlines() if line.strip()]
    assert len(source_lines) == len(generated_lines)
    for s, g in zip(source_lines, generated_lines):
        assert s.strip() == g.strip()


@cloup.command()
@cloup.option("--foo", help="add1")
@cloup.option("--bar", help="add2", default=10)
@cloup.option(
    '-T',
    '--type',
    type=cloup.Choice(['a', 'b', 'c']),
    required=True,
    help='data type',
)
@cloup.argument(
    'name',
    help='The name to use in the output',
    type=cloup.Choice(['a', 'b', 'c']),
)
@cloup.argument(
    'suffix',
    help='The suffix to use in the output',
)
def mycmd_args(foo, bar, type, name, suffix):
    """returns the sum of foo and bar as a string, followed by the type and name"""
    return str(foo + bar) + type + " with " + name + suffix


def test_mycmd_args():
    source = r"""
#compdef mycmd_args

_mycmd_args() {
  _arguments \
    '(--foo)'--foo'[add1]:Text:_default' \
    '(--bar)'--bar'[add2]:Integer:(10)' \
    '(--type -T)'{--type,-T}'[data type]:Choices:(a b c)' \
    '1:Choices:(a b c)' \
    '2:Default:_default'
}

_mycmd_args
"""
    cmd = ClickCommand(mycmd_args).to_command()
    generated = cmd.complete_source()
    source_lines = [line for line in source.splitlines() if line.strip()][1:-1]
    generated_lines = [line for line in generated.splitlines() if line.strip()]
    assert len(source_lines) == len(generated_lines)
    for s, g in zip(source_lines, generated_lines):
        assert s.strip() == g.strip()


def test_complex_cmd():
    source = r"""
#compdef click

_click_subcommands() {
  local -a subcmds
  subcmds=(
    "hello:Simple program that greets NAME for a total of COUNT times."
    "mycmd:returns the sum of foo and bar as a string, followed by the type"
  )
  _describe -t subcommands 'subcommands' subcmds
}

_click() {
  local state

  _arguments -C \
    '1: :->cmds' \
    '*:: :->args'

  case $state in
    cmds)
      _click_subcommands
      ;;

    args)
      case $words[1] in
        hello)
          _arguments \
            '(--count)'--count'[Number of greetings.]:Integer:(1)' \
            '(--name)'--name'[The person to greet.]:Text:_default'
          ;;
        mycmd)
          _arguments \
            '(--foo)'--foo'[add1]:Text:_default' \
            '(--bar)'--bar'[add2]:Integer:(10)' \
            '(--type -T)'{--type,-T}'[data type]:Choices:(a b c)' \
            '(--use-foo)'--use-foo'[append with foo in the end]'
          ;;

      esac
      ;;

  esac
}

_click
"""
    cmd = ClickCommand([hello, mycmd], name="click").to_command()
    generated = cmd.complete_source()
    source_lines = [line for line in source.splitlines() if line.strip()][1:-1]
    generated_lines = [line for line in generated.splitlines() if line.strip()]
    assert len(source_lines) == len(generated_lines)
    for s, g in zip(source_lines, generated_lines):
        assert s.strip() == g.strip()
