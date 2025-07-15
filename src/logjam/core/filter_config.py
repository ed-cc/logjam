import json
from logjam.core.logical_operator import LogicalOperator


class Filter:
    """Class representing a filter with logical operators and conditions."""

    name: str
    logical_operator: LogicalOperator
    regex: bool
    filter_strings: list[str]
    sub_filters: list["Filter"]

    def __init__(
        self,
        name: str,
        logical_operator: LogicalOperator,
        regex: bool = False,
        filter_strings: list[str] | None = None,
        sub_filters: list["Filter"] | None = None,
    ):
        if not isinstance(logical_operator, LogicalOperator):
            raise ValueError("logical_operator must be an instance of LogicalOperator.")
        if not isinstance(name, str):
            raise ValueError("Filter name must be a string.")
        if filter_strings is not None and not isinstance(filter_strings, list):
            raise ValueError("filter_str must be a list of strings.")
        if filter_strings is not None and any(
            not isinstance(s, str) for s in filter_strings
        ):
            raise ValueError("All items in filter_str must be strings.")
        if sub_filters is not None and not isinstance(sub_filters, list):
            raise ValueError("filters must be a list of Filter instances.")
        if sub_filters is not None and any(
            not isinstance(f, Filter) for f in sub_filters
        ):
            raise ValueError("All items in filters must be instances of Filter.")
        if regex:
            raise NotImplementedError("Regex filtering is not yet implemented.")
        self.name = name
        self.logical_operator = logical_operator
        self.regex = regex
        self.filter_strings = filter_strings if filter_strings is not None else []
        self.sub_filters = sub_filters if sub_filters is not None else []

    def to_dict(self):
        """Convert the filter to a dictionary representation."""
        return {
            "name": self.name,
            "logical_operator": self.logical_operator.value,
            "regex": self.regex,
            "filter_strings": self.filter_strings,
            "filters": [filter.to_dict() for filter in self.sub_filters],
        }

    def matches(self, line: str) -> bool:
        """Check if the line matches the filter conditions."""
        match self.logical_operator:
            case LogicalOperator.AND:
                return self._matches_and(line)
            case LogicalOperator.OR:
                return self._matches_or(line)
            case LogicalOperator.NOT:
                return self._matches_not(line)
            case _:
                raise ValueError(f"Unknown logical operator: {self.logical_operator}")

    def _matches_and(self, line: str) -> bool:
        return all(sub_filter.matches(line) for sub_filter in self.sub_filters) and all(
            sub_str in line for sub_str in self.filter_strings
        )

    def _matches_or(self, line: str) -> bool:
        return any(sub_filter.matches(line) for sub_filter in self.sub_filters) or any(
            sub_str in line for sub_str in self.filter_strings
        )

    def _matches_not(self, line: str) -> bool:
        return not any(
            sub_filter.matches(line) for sub_filter in self.sub_filters
        ) and not any(sub_str in line for sub_str in self.filter_strings)

    @classmethod
    def from_dict(cls, data: dict):
        """Create a Filter instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary.")
        return cls(
            data.get("name", ""),
            LogicalOperator.from_any(data.get("logical_operator")),
            data.get("regex", False),
            data.get("filter_strings", []),
            [Filter.from_dict(sf) for sf in data.get("filters", [])],
        )


class FilterConfig:
    """Class representing a configuration for multiple filters."""

    filters: dict[str, Filter]

    def __init__(self):
        self.filters = {}

    @classmethod
    def from_dict(cls, data: dict):
        config = cls()
        for key, data in data.items():
            match key:
                case "filter":
                    filter = Filter.from_dict(data)
                    config.add_filter(filter)
                case _:
                    raise ValueError(f"Unknown key in configuration: {key}")
        return config

    @classmethod
    def from_json(cls, json_str: str):
        """
        Create a FilterConfig instance from a JSON string.

        Args:
            json_str (str): The JSON string representing the filter configuration.

        Returns:
            FilterConfig: An instance of FilterConfig.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, file_path: str):
        """
        Create a FilterConfig instance from a JSON file.

        Args:
            file_path (str): The path to the JSON file containing the filter configuration.

        Returns:
            FilterConfig: An instance of FilterConfig.
        """
        with open(file_path, "r") as file:
            json_str = file.read()
        return cls.from_json(json_str)

    @classmethod
    def create_example_config(cls) -> "FilterConfig":
        """
        Create an example FilterConfig with predefined filters.

        Returns:
            FilterConfig: An instance of FilterConfig with example filters.
        """
        config = cls()
        config.add_filter(
            Filter(
                name="ExampleFilter1",
                logical_operator=LogicalOperator.AND,
                filter_strings=["error", "critical"],
            )
        )
        config.add_filter(
            Filter(
                name="ExampleFilter2",
                logical_operator=LogicalOperator.OR,
                filter_strings=["warning", "alert"],
            )
        )
        return config

    def to_dict(self) -> dict:
        """
        Convert the FilterConfig to a dictionary representation.

        Returns:
            dict: A dictionary representation of the FilterConfig.
        """
        return {
            "filter": filter_obj.to_dict() for _, filter_obj in self.filters.items()
        }

    def to_json(self) -> str:
        """
        Convert the FilterConfig to a JSON string.

        Returns:
            str: A JSON string representation of the FilterConfig.
        """
        return json.dumps(self.to_dict(), indent=4)

    def to_file(self, file_path: str):
        """
        Write the FilterConfig to a JSON file.

        Args:
            file_path (str): The path to the file where the configuration will be written.
        """
        with open(file_path, "w") as file:
            json_str = self.to_json()
            file.write(json_str)

    def add_filter(self, filter_obj: Filter):
        """
        Add a filter to the configuration.

        Args:
            filter_obj (Filter): The Filter object to add.

        Raises:
            ValueError: If the name is not a string, if filter_obj is not a Filter,
                or if a filter with the same name already exists.

        Returns:
            FilterConfig: The FilterConfig instance for method chaining.
        """
        if not isinstance(filter_obj, Filter):
            raise ValueError("filter_obj must be an instance of Filter")
        name = filter_obj.name
        if name in self.filters:
            raise ValueError(f"Filter with name '{name}' already exists")
        self.filters[name] = filter_obj
        return self

    def get_filter_by_name(self, name: str) -> Filter:
        """
        Get a filter by its name.

        Args:
            name (str): The name of the filter to retrieve.

        Returns:
            Filter: The Filter object with the specified name.

        Raises:
            ValueError: If no filter with the specified name exists.
        """
        if name not in self.filters:
            raise ValueError(f"Filter with name '{name}' does not exist")
        return self.filters[name]

    def get_first_filter(self) -> Filter:
        """
        Get the first filter in the configuration.

        Returns:
            Filter: The first Filter object in the configuration.

        Raises:
            ValueError: If no filters are defined in the configuration.
        """
        if not self.filters:
            raise ValueError("No filters defined in the configuration")
        return next(iter(self.filters.values()))

    def matches(self, filter: str, line: str) -> bool:
        """
        Check if the line matches the filter.

        Args:
            filter (str): The name of the filter to check.
            line (str): The line to check against the filters.

        Returns:
            str: The name of the first filter that matches the line, or None if no filters match.
        """
        if filter not in self.filters:
            raise ValueError(f"Filter '{filter}' does not exist")
        filter_obj = self.filters[filter]
        if filter_obj.matches(line):
            return True
        return False


__all__ = ["LogicalOperator", "Filter", "FilterConfig"]
