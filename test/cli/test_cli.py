import subprocess
import os
import sys
from test.common import make_filter_config_file, make_input_file


def test_main_cli_creates_output():
    input_path = make_input_file()
    filter_path = make_filter_config_file()

    output_path = input_path + ".out"

    # Run CLI
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "logjam.cli.main",
            filter_path,
            input_path,
            output_path,
            "--filter",
            "testfilter",
        ],
        capture_output=True,
        text=True,
    )

    assert os.path.exists(output_path)
    with open(output_path) as f:
        out_lines = [line.strip() for line in f.readlines()]
    assert "foo bar baz" in out_lines
    assert "foo baz" in out_lines
    assert "bar baz" in out_lines
    assert "baz qux" not in out_lines

    # Clean up
    os.remove(filter_path)
    os.remove(input_path)
    os.remove(output_path)
