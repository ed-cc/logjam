import pytest
from logjam.core.filter_config import LogicalOperator


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("AND", LogicalOperator.AND),
        ("OR", LogicalOperator.OR),
        ("NOT", LogicalOperator.NOT),
        ("and", LogicalOperator.AND),
        ("or", LogicalOperator.OR),
        ("not", LogicalOperator.NOT),
        (LogicalOperator.AND, LogicalOperator.AND),
        (LogicalOperator.OR, LogicalOperator.OR),
        (LogicalOperator.NOT, LogicalOperator.NOT),
    ],
)
def test_logical_operator_from_any_valid(input_value, expected):
    assert LogicalOperator.from_any(input_value) == expected


@pytest.mark.parametrize(
    "input_value",
    [
        None,
        "INVALID",
        123,
    ],
)
def test_logical_operator_from_any_invalid(input_value):
    with pytest.raises(ValueError):
        LogicalOperator.from_any(input_value)
