from logjam.core.filter_config import FilterConfig
from logjam.core.file_filter_processor import FileFilterProcessor


class LogjamCLI:
    """Command Line Interface for Logjam."""

    filter_config: FilterConfig
    file_path: str
    filter_processor: FileFilterProcessor
    output_path: str | None
    verbose: bool
    filter_name: str | None

    def __init__(
        self,
        filter_path: str,
        file_path: str,
        output_path: str | None = None,
        verbose: bool = False,
        filter_name: str | None = None,
    ):
        self.filter_config = FilterConfig.from_file(filter_path)
        self.verbose = verbose
        if self.verbose:
            print(f"Loaded filter configuration from {filter_path}")
        self.file_path = file_path
        self.filter_processor = FileFilterProcessor(self.filter_config, self.file_path)
        self.output_path = output_path
        self.filter_name = filter_name
        if not self.output_path:
            self.output_path = "filtered_output.txt"

    def run(self):
        """Run the Logjam CLI."""
        filtered_lines = self.filter_processor.process_filters(self.filter_name)
        if self.verbose:
            print(f"Found {len(filtered_lines)} matching lines.")
        if self.output_path:
            if self.verbose:
                print(f"Writing filtered lines to {self.output_path}")
            with open(self.output_path, "w") as output_file:
                for filtered_line in filtered_lines:
                    output_file.write(f"{filtered_line.line_content}\n")
