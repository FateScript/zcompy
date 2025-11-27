#!/usr/bin/env python3

import os
import tempfile

from zcompy import Command, Completion, Files, Option


def create_mytool_command():
    """Create a mytool command that matches the _mytool file structure."""
    mytool_cmd = Command("mytool", "My tool description")

    # Add global options
    options = [
        Option(("--verbose", "-v"), "Enable verbose output"),
        Option(
            ("--config", "-c"), "Config file path", type="FILE", complete_func=Completion(Files())
        ),
    ]
    mytool_cmd.add_options(options)

    # Add sub-commands
    init_cmd = Command("init", "Initialize a new project")
    init_options = [
        Option(("--template", "-t"), "Template to use"),
        Option(("--force", "-f"), "Force overwrite existing files"),
    ]
    init_cmd.add_options(init_options)

    build_cmd = Command("build", "Build the project")
    build_cmd.add_options(
        Option(
            ("--output", "-o"),
            "Output directory",
            type="DIR",
            complete_func=Completion(Files(dir_only=True)),
        )
    )
    build_cmd.add_options(Option(("--optimize", "-O"), "Optimization level"))

    deploy_cmd = Command("deploy", "Deploy the project")
    deploy_cmd.add_options(Option(("--server", "-s"), "Server to deploy to"))
    deploy_cmd.add_options(Option(("--dry-run",), "Show what would be deployed"))

    mytool_cmd.add_sub_commands([init_cmd, build_cmd, deploy_cmd])

    return mytool_cmd


def test_completion_matches_mytool():
    """Test that generated completion matches _mytool format."""
    # Create the command
    mytool_cmd = create_mytool_command()

    # Generate completion to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, "_mytool")

        mytool_cmd.completion_entry(output_dir=temp_dir)

        with open(temp_file, "r") as f:
            generated_content = f.read()

        with open(os.path.join(os.path.dirname(__file__), "_mytool"), "r") as f:
            reference_content = f.read()

        gen_code = [x for x in generated_content.splitlines() if x.strip()]
        gen_code = [x for x in gen_code if all(not x.startswith(k) for k in ("compdef", "zstyle"))]
        ref_code = [x for x in reference_content.splitlines() if x.strip()]
        assert gen_code == ref_code, "Generated completion does not match reference _mytool format"


if __name__ == "__main__":
    test_completion_matches_mytool()
