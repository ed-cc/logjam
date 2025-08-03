import pytest
from logjam.core.filter_config import FilterConfig, Filter, LogicalOperator
from logjam.core.file_filter_processor import FileFilterProcessor, FilteredLine
from test.common import make_input_file


def test_filtered_line_repr():
    fl = FilteredLine(1, "hello")
    assert repr(fl) == "FilteredLine(line_number=1, line_content=hello)"


def test_file_filter_processor_and():
    file_path = make_input_file()
    filter_obj = Filter(
        name="andfilter",
        logical_operator=LogicalOperator.AND,
        filter_strings=["foo", "bar"],
    )
    config = FilterConfig()
    config.add_filter(filter_obj)
    processor = FileFilterProcessor(filter_config=config, file_path=file_path)
    result = processor.process_filters("andfilter")
    assert len(result) == 1
    assert result[0].line_content == "foo bar baz"


def test_file_filter_processor_or():
    file_path = make_input_file()
    filter_obj = Filter(
        name="orfilter",
        logical_operator=LogicalOperator.OR,
        filter_strings=["foo", "bar"],
    )
    config = FilterConfig()
    config.add_filter(filter_obj)
    processor = FileFilterProcessor(filter_config=config, file_path=file_path)
    result = processor.process_filters("orfilter")
    assert len(result) == 3
    assert result[0].line_content == "foo bar baz"
    assert result[1].line_content == "foo baz"
    assert result[2].line_content == "bar baz"


def test_file_filter_processor_not():
    file_path = make_input_file()
    filter_obj = Filter(
        name="notfilter",
        logical_operator=LogicalOperator.NOT,
        filter_strings=["foo", "bar"],
    )
    config = FilterConfig()
    config.add_filter(filter_obj)
    processor = FileFilterProcessor(filter_config=config, file_path=file_path)
    result = processor.process_filters("notfilter")
    assert len(result) == 1
    assert result[0].line_content == "baz qux"


def test_file_filter_processor_missing_config_or_path():
    processor = FileFilterProcessor()
    with pytest.raises(ValueError):
        processor.process_filters("any")
