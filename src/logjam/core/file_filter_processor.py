from logjam.core.filter_config import FilterConfig, Filter, LogicalOperator


class FilteredLine:
    """Class representing a line that has been filtered."""

    def __init__(self, line_number: int, line_content: str):
        self.line_number = line_number
        self.line_content = line_content

    def __repr__(self):
        return f"FilteredLine(line_number={self.line_number}, line_content={self.line_content})"


class FileFilterProcessor:
    """Class to process file filters based on logical operators and filter strings."""

    filter_config: FilterConfig | None
    file_path: str | None
    filtered_lines: list[FilteredLine] = []

    def __init__(
        self, filter_config: FilterConfig | None = None, file_path: str | None = None
    ):
        self.filter_config = filter_config
        self.file_path = file_path

    def process_filters(self, filter_name: str | None) -> list[FilteredLine]:
        """Process the filters and return filtered lines."""
        if not self.filter_config or not self.file_path:
            raise ValueError("Filter configuration and file path must be provided.")
        if not filter_name:
            filter = self.filter_config.get_first_filter()
        else:
            filter = self.filter_config.get_filter_by_name(filter_name)
        self.filtered_lines = []
        with open(self.file_path, "r") as file:
            for line_number, line in enumerate(file, start=1):
                if filter.matches(line):
                    filtered_line = FilteredLine(line_number, line.strip())
                    self.filtered_lines.append(filtered_line)
        return self.filtered_lines


__all__ = ["FileFilterProcessor", "FilteredLine"]
