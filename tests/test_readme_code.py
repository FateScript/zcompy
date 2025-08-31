#!/usr/bin/env python3

import pathlib
import re
import subprocess
import tempfile


def test_code_in_readme():
    with open(pathlib.Path(__file__).parent.parent / "README.md", "r") as f:
        content = f.read()
    py_content = re.findall(r"```python(.*?)```", content, re.DOTALL)

    with tempfile.TemporaryDirectory() as temp_dir:
        py_file = pathlib.Path(temp_dir) / "tmp_readme.py"
        with open(py_file, "w") as f:
            f.write("\n".join(py_content))
        result = subprocess.run(
            ["python3", str(py_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"README code failed: {result.stderr}"
