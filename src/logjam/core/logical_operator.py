from enum import Enum
from typing import Any


class LogicalOperator(Enum):
    """Enum for logical operators used in filters."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    @classmethod
    def from_any(cls, value: Any) -> "LogicalOperator":
        """Convert a value to a LogicalOperator enum member."""
        if value is None:
            raise ValueError("Logical operator cannot be None")
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            value = value.upper()
            if value not in cls._value2member_map_:
                raise ValueError(f"Invalid logical operator: {value}")
            return LogicalOperator(cls._value2member_map_[value])
        raise ValueError(f"Invalid type for logical operator: {type(value)}")
