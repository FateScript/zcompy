#!/usr/bin/env python3

import os
import tempfile

from zcompy import Command, Completion, Option
from zcompy.action.action import Files


def ls_number():
    import random

    random_letter = "abcdefghijklmnopqrstuvwxyz"
    for idx in range(10):
        letter = "".join(random.choices(random_letter, k=10))
        print(f"{idx} {letter}")


def test_complete_abc_py():
    cmd = Command("abc", "abc command")

    opts = [
        Option(("-a",), "Hello", complete_func=Files()),
        Option(
            ("-b", "-c"), "Another option", type="NUMBER",
            complete_func=Completion(ls_number, shell_embed=True),
        ),
        Option("--test", "It's a test", allow_repeat=True),
    ]
    cmd.add_options(opts)

    with open(os.path.join(os.path.dirname(__file__), "_abc_py"), "r") as f:
        answer = f.read()

    with tempfile.TemporaryDirectory() as temp_dir:
        cmd.completion_entry(temp_dir)
        output_file = os.path.join(temp_dir, "_abc")
        with open(output_file, "r") as f:
            content = f.read()
        content = [x for x in content.splitlines() if x.strip()]
        answer = [x for x in answer.splitlines() if x.strip()]
        assert content == answer, f"Content mismatch:\nExpected:\n{answer}\nGot:\n{content}"


if __name__ == "__main__":
    test_complete_abc_py()
