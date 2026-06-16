import os

from logjam.core.filter_config import FilterConfig
from logjam.core.file_filter_processor import FileFilterProcessor

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "examples")
SAMPLE_LOG = os.path.join(EXAMPLES_DIR, "sample.log")
FILTERS = os.path.join(EXAMPLES_DIR, "filters.json")


def _run(filter_name):
    config = FilterConfig.from_file(FILTERS)
    processor = FileFilterProcessor(filter_config=config, file_path=SAMPLE_LOG)
    return processor.process_filters(filter_name)


def test_example_config_loads():
    config = FilterConfig.from_file(FILTERS)
    assert config.filter_names() == [
        "Errors",
        "Warnings and Alerts",
        "HTTP 5xx (regex)",
        "Errors excluding timeouts",
    ]


def test_example_errors_filter():
    assert len(_run("Errors")) == 5


def test_example_regex_filter():
    lines = _run("HTTP 5xx (regex)")
    assert len(lines) == 2
    assert all("500" in line.line_content or "504" in line.line_content for line in lines)


def test_example_nested_filter_excludes_timeouts():
    lines = _run("Errors excluding timeouts")
    contents = [line.line_content for line in lines]
    assert len(contents) == 3
    assert not any("timeout" in line for line in contents)
