import argparse
from logjam.core.filter_config import FilterConfig
from logjam.cli.logjam_cli import LogjamCLI


def main():
    parser = argparse.ArgumentParser(description="Logjam CLI")
    parser.add_argument(
        "filter_config", nargs="?", help="Path to filter config JSON file."
    )
    parser.add_argument("input_file", nargs="?", help="Path to input file.")
    parser.add_argument("output_file", nargs="?", help="Path to output file.")
    parser.add_argument(
        "--verbose",
        "-v",
        help="Enable verbose output.",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--filter", "-f", help="The name of the filter to apply.", default=None
    )
    parser.add_argument(
        "--example-config",
        help='Generate an example filter config file "example_filter_config.json" and exit.',
        action="store_true",
    )
    args = parser.parse_args()

    if args.example_config:
        FilterConfig.create_example_config().to_file("example_filter_config.json")
        print("Example filter config written to example_filter_config.json.")
        return

    if not args.filter_config or not args.input_file or not args.output_file:
        parser.error(
            "the following arguments are required: filter_config, input_file, output_file"
        )

    logjam_cli = LogjamCLI(
        args.filter_config, args.input_file, args.output_file, args.verbose, args.filter
    )

    logjam_cli.run()


if __name__ == "__main__":
    main()
