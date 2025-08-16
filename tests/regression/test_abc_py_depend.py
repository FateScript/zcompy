import os
import tempfile

import pytest

from zcompy import Command, Completion, DependentCompletion, Files, Option
from zcompy.utils import python_func_source


def ls_number():
    import random

    random_letter = "abcdefghijklmnopqrstuvwxyz"
    for idx in range(10):
        letter = "".join(random.choices(random_letter, k=10))
        print(f"{idx} {letter}")


def ls_number_depend(prefix):
    import random

    random_letter = "abcdefghijklmnopqrstuvwxyz"
    for idx in range(10):
        letter = "".join(random.choices(random_letter, k=10))
        print(f"{prefix}{idx} {letter}")


@pytest.mark.parametrize("shell_embed", [True, False])
def test_complete_abc_py(shell_embed):
    cmd = Command("abc", "abc command")

    opts = [
        Option(("-a",), "Hello", complete_func=Files()),
        Option(
            ("-b", "-c"), "Another option", type="NUMBER",
            complete_func=Completion(ls_number, shell_embed=shell_embed),
        ),
        Option(
            "-d", "Denpend -b/-c", type="PREFIX_NUMBER",
            complete_func=DependentCompletion(
                func=ls_number_depend,
                depends_on=("-b", "-c"),
                shell_embed=shell_embed,
            ),
        ),
        Option("--test", "It's a test", allow_repeat=True),
    ]
    cmd.add_options(opts)

    filename = "_abc_py_depend" if shell_embed else "_abc_py_depend_no_embed"
    with open(os.path.join(os.path.dirname(__file__), filename), "r") as f:
        answer = f.read()

    with tempfile.TemporaryDirectory() as temp_dir:
        cmd.completion_entry(temp_dir)
        output_file = os.path.join(temp_dir, "_abc")
        with open(output_file, "r") as f:
            content = f.read()
        content_lines = [x for x in content.splitlines() if x.strip()]
        answer_lines = [x for x in answer.splitlines() if x.strip()]
        for x, y in zip(content_lines, answer_lines):
            assert x == y, f"Content mismatch:\nExpected: {y}\nGot: {x}"

    if not shell_embed:
        save_path = os.environ["ZCOMPY_FUNC_SAVE_PATH"]
        ls_number_file = os.path.join(save_path, "ls_number")
        assert os.path.exists(ls_number_file)
        with open(ls_number_file, "r") as f:
            ls_content = f.read()
        assert ls_content.endswith(python_func_source(ls_number))

        ls_number_depend_file = os.path.join(save_path, "ls_number_depend")
        assert os.path.exists(ls_number_depend_file)
        with open(ls_number_depend_file, "r") as f:
            ls_content = f.read()
        assert ls_content.endswith(python_func_source(ls_number_depend))
