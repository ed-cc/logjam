import pytest
from logjam.core.filter_config import LogicalOperator, Filter, FilterConfig


def test_filter_matches_and():
    f = Filter(
        name="test_and",
        logical_operator=LogicalOperator.AND,
        filter_strings=["foo", "bar"],
    )
    assert f.matches("foo bar baz")
    assert not f.matches("foo baz")


def test_filter_matches_or():
    f = Filter(
        name="test_or",
        logical_operator=LogicalOperator.OR,
        filter_strings=["foo", "bar"],
    )
    assert f.matches("foo baz")
    assert f.matches("bar baz")
    assert not f.matches("baz qux")


def test_filter_matches_not_or():
    f = Filter(
        name="test_not_or",
        logical_operator=LogicalOperator.NOT,
        filter_strings=["foo", "bar"],
    )
    assert f.matches("baz qux")
    assert not f.matches("foo baz")


def test_filter_config_add_and_get():
    config = FilterConfig()
    f = Filter(
        name="myfilter",
        logical_operator=LogicalOperator.OR,
        filter_strings=["hello"],
    )
    config.add_filter(f)
    assert config.get_filter_by_name("myfilter") == f
    with pytest.raises(ValueError):
        config.add_filter(f)  # duplicate name
    with pytest.raises(ValueError):
        config.get_filter_by_name("notfound")


def test_filter_config_from_dict_and_json():
    data = {
        "filter": {
            "name": "f1",
            "logical_operator": "AND",
            "regex": False,
            "filter_strings": ["x", "y"],
            "filters": [],
        }
    }
    config = FilterConfig.from_dict(data)
    f = config.get_filter_by_name("f1")
    assert f.name == "f1"
    assert f.logical_operator == LogicalOperator.AND
    assert f.filter_strings == ["x", "y"]

    json_str = config.to_json()
    config2 = FilterConfig.from_json(json_str)
    f2 = config2.get_filter_by_name("f1")
    assert f2.name == "f1"


def test_filter_config_to_from_file(tmp_path):
    config = FilterConfig()
    f = Filter(
        name="f1",
        logical_operator=LogicalOperator.AND,
        filter_strings=["x", "y"],
    )
    config.add_filter(f)

    file_path = tmp_path / "filter_config.json"
    config.to_file(file_path)

    config2 = FilterConfig.from_file(file_path)
    f2 = config2.get_filter_by_name("f1")
    assert f2.name == "f1"
    assert f2.logical_operator == LogicalOperator.AND
    assert f2.filter_strings == ["x", "y"]
