import os

from zcompy import Command, Completion, Files, Option
from zcompy.action import Default, GitBranches, GitCommits


def create_mytool_complex_command():
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
    init_cmd.add_positional_args(GitCommits())

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
    build_cmd.add_positional_args([GitBranches(), GitCommits()])

    deploy_cmd = Command("deploy", "Deploy the project")
    deploy_cmd.add_options(Option(("--server", "-s"), "Server to deploy to"))
    deploy_cmd.add_options(Option(("--dry-run",), "Show what would be deployed"))
    deploy_cmd.add_positional_args(Default())

    mytool_cmd.add_sub_command(init_cmd)
    mytool_cmd.add_sub_command(build_cmd)
    mytool_cmd.add_sub_command(deploy_cmd)

    return mytool_cmd


def test_completion_matches_mytool_complex():
    """Test that generated completion matches _mytool format."""
    mytool_cmd = create_mytool_complex_command()

    generated_source = mytool_cmd.complete_source()

    with open(os.path.join(os.path.dirname(__file__), "_mytool_complex"), "r") as f:
        reference_content = f.read()

    gen_code = [x for x in generated_source.splitlines() if x.strip()]
    ref_code = [x for x in reference_content.splitlines() if x.strip()][1:-1]
    assert gen_code == ref_code, "Generated completion does not match reference _mytool format"


if __name__ == "__main__":
    test_completion_matches_mytool_complex()
