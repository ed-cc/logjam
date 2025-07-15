import os
from logjam.cli.logjam_cli import LogjamCLI
from test.common import make_filter_config_file, make_input_file


def test_logjam_cli_run_creates_output():
    filter_path = make_filter_config_file()
    input_path = make_input_file()
    output_path = input_path + ".out"
    cli = LogjamCLI(
        filter_path=filter_path,
        file_path=input_path,
        output_path=output_path,
        verbose=True,
        filter_name="testfilter",
    )
    cli.run()
    assert os.path.exists(output_path)
    with open(output_path) as f:
        lines = [line.strip() for line in f.readlines()]
    assert "foo bar baz" in lines
    assert "foo baz" in lines
    assert "bar baz" in lines
    assert "baz qux" not in lines
