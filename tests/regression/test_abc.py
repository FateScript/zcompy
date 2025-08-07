import os
import tempfile

from zcompy import Command, Completion, Option


def ls_number():
    import random

    random_letter = "abcdefghijklmnopqrstuvwxyz"
    for idx in range(10):
        letter = "".join(random.choices(random_letter, k=10))
        print(f"{idx} {letter}")


def test_complete_abc():
    # set a temp path for function saving
    os.environ["ZCOMPY_FUNC_SAVE_PATH"] = tempfile.gettempdir()

    cmd = Command("abc", "abc command")

    opts = [
        Option(("-a",), "Hello world"),
        Option(("-b", "-c"), "Another option", type="NUMBER", complete_func=Completion(ls_number)),
    ]
    cmd.add_options(opts)

    with open(os.path.join(os.path.dirname(__file__), "_abc"), "r") as f:
        answer = f.read()

    with tempfile.TemporaryDirectory() as temp_dir:
        cmd.completion_entry(temp_dir)
        output_file = os.path.join(temp_dir, "_abc")
        with open(output_file, "r") as f:
            content = f.read()
        content = [x for x in content.splitlines() if x.strip()]
        answer = [x for x in answer.splitlines() if x.strip()]
        for x, y in zip(content, answer):
            assert x == y, f"Expected: {x}, but got: {y}"


if __name__ == "__main__":
    test_complete_abc()
