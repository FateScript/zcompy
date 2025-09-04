# zcompy

**zcompy** (**z**sh **comp**letion using **Py**thon) is a Python library that makes it easy to generate sophisticated zsh completion scripts for your command-line tools.

Instead of writing complex zsh completion scripts by hand, you can define your commands and options in Python and let zcompy generate the completion for you.

## Features

- 🐍 **Pure Python**: Define completions using familiar Python syntax
- 🎯 **Type-safe**: Built-in support for common argument types (files, directories, strings)
- 🔄 **Sub-commands**: Full support for nested sub-commands
- 🎨 **Custom completions**: Define your own completion functions with python functions
- 🔗 **Dependencies**: Completion could depend on other option values

## Installation

### From PyPI

```bash
pip install zcompy
```

### From Source

```bash
git clone https://github.com/FateScript/zcompy.git
cd zcompy
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/FateScript/zcompy.git
cd zcompy
pip install -e ".[dev]"
```

## Quick Start

Here's a simple example to get you started:

```python
from zcompy import Command, Option, Files, Completion

# Create your command
mytool = Command("mytool", "My awesome command-line tool")

# Add global options for mytool
mytool.add_options([
    Option(("--verbose", "-v"), "Enable verbose output"),
    Option(("--config", "-c"), "Config file path", complete_func=Files())
])

# Create sub-commands
build_cmd = Command("build", "Build the project")
build_cmd.add_options([
    Option(
        ("--output", "-o"), "Output directory",
        complete_func=Files(dir_only=True)
    ),
    Option(
        ("--optimize", "-O"), "Optimization level",
        complete_func=Completion(func=("o1", "o2", "o3"))
    )
])

# Add sub-command to main command
mytool.add_sub_commands(build_cmd)

# print completion source
print(mytool.complete_source())
# Also, you might generate zsh completion code in output dir
# mytool.completion_entry(output_dir="~/.zsh/completion")
```

Then add to your `~/.zshrc` or run in your terminal sesssion:
```bash
fpath=(~/.zsh/completions $fpath)
autoload -U compinit && compinit
compdef _mytool mytool
```

👉 Please type `mytool` in cli and press `<TAB>` to feel the magic 🪄

## Usage

### Basic Command Structure

```python
from zcompy import Command, Option, Completion, Files

# Create a command
cmd = Command("mycmd", "Description of your command")

# Add options
cmd.add_options([
    Option(("--flag", "-f"), "Turn on to enable something"),
    Option(("--file",), "Input file", complete_func=Files()),
    Option(("--dir",), "Output directory", complete_func=Files(dir_only=True))
])
```

### Sub-commands

```python
# Create main command
main = Command("git", "Git version control")

# Create sub-commands
status = Command("status", "Show working tree status")
commit = Command("commit", "Record changes to repository")
commit.add_options([
    Option(("--message", "-m"), "Commit message", type="STRING"),
    Option(("--amend",), "Amend previous commit")
])

# Add sub-commands to main
main.add_sub_commands([status, commit])
```

### Custom Completions

Define your own completion functions

NOTE: 
1. To make your completions work, simply print each completion string to stdout.
2. If you want to show descriptions for completions, print them after a space, like: `completion description`.

```python
def list_things():
    for item in ["thing1", "thing2", "thing3"]:
        print(f"my_{item}")

branch_option = Option(
    ("--things", "-t"), 
    "things to describe",
    type="THINGS", 
    complete_func=Completion(list_things)
)
```

### Advanced Usage

#### Automatic CLI Framework Support

zcompy provides built-in support for generating completions from popular Python CLI frameworks:

##### ArgumentParser support
```python
from argparse import ArgumentParser
from zcompy.parser_command import ParserCommand

# Create your argparse parser
parser = ArgumentParser(prog="mytool", description="My awesome CLI tool")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
parser.add_argument("--config", "-c", type=str, help="Config file path")
parser.add_argument("--mode", choices=["auto", "manual", "disabled"], help="Operation mode")

# Add sub-commands
subparsers = parser.add_subparsers(dest="command")
build_parser = subparsers.add_parser("build", help="Build the project")
build_parser.add_argument("--output", "-o", type=str, help="Output directory")

# Generate completion using zcompy
parser_command = ParserCommand(parser)
command = parser_command.to_command()
print(command.complete_source())

# Add custom completion for file paths
from zcompy.action import Files
parser_command.add_action_for_options("--config", "--output", action=Files())
```

##### Abseil ([absl-py](https://github.com/abseil/abseil-py)) Support
```python
from absl import flags
from zcompy.absl_command import AbslFlagsCommand

# Define your absl flags
FLAGS = flags.FLAGS
flags.DEFINE_string('name', 'World', 'The name to greet')
flags.DEFINE_integer('count', 1, 'The number of greetings')
flags.DEFINE_bool('verbose', False, 'Whether to display verbose output')
flags.DEFINE_enum('color', 'blue', ['red', 'blue', 'green'], 'Choose a color')

# Generate completion using zcompy
cmd = AbslFlagsCommand(name="mytool").to_command()
print(cmd.complete_source())
```

##### [Fire](https://github.com/google/python-fire) Support

Users could use FireCommand like [fire-guide](https://github.com/google/python-fire/blob/master/docs/guide.md).

###### python class
```python
import fire
from zcompy.fire_command import FireCommand

class MyCLI:
    """My awesome CLI tool."""

    def add(self, x, y):
        """Addition command"""
        return x + y

    def mul(self, a, b):
        """Multiplication command"""
        return a * b

    def build(self, output_dir="./build", optimize=True):
        """Build the project"""
        return f"Building to {output_dir}"

# Generate completion using zcompy
fire_cmd = FireCommand(name="mytool", obj=MyCLI)
command = fire_cmd.to_command()
print(command.complete_source())
```

##### python function

```python
def add_func(x, y):
    """Addition command"""
    return x + y

fire_cmd = FireCommand(name="calc", obj=add_func)
command = fire_cmd.to_command()
print(command.complete_source())
```

##### python dict

```python
func_dict = {"add": lambda x, y: x + y, "mul": lambda a, b: a * b}
fire_cmd = FireCommand(name="math", obj=func_dict)
command = fire_cmd.to_command()
print(command.complete_source())
```

#### Dependent Completions

Completions could depend on other options' value/existence:

```python
from zcompy import DependentCompletion, Option

def complete_based_on_config(config_path):
    """Complete based on config_path value."""
    if config_path and os.path.exists(config_path):
        # Read config and provide completions
        with open(config_path) as f:
            configs = f.read().splitlines()
        for line, config in enumerate(configs):
            print(f"{config} line {line + 1}")

config_dependent = Option(
    ("--target",), 
    "Target based on config",
    type="TARGET",
    complete_func=DependentCompletion(
        func=complete_based_on_config,
        depends_on="--config"
    )
)
```

#### Positional Arguments

```python
from zcompy.action import GitBranches, GitCommits

# Add positional arguments
cmd.add_positional_args([
    Files("*.py"),
    GitBranches(),
    GitCommits(),
])

# Use repeat_pos_args if you want to repeat positional arguments.
# for example, `cmd file1 file2 file3`
cmd.repeat_pos_args = Files()
```

## Development

### Setup Development Environment
```bash
git clone https://github.com/FateScript/zcompy.git
cd zcompy
python -m venv zcompy
source zcompy/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests
```

## Acknowledgments

- Thanks to [Claude code](https://github.com/anthropics/claude-code) and [Kimi K2](https://github.com/MoonshotAI/Kimi-K2) for writing code and giving inspiration, guidance.
