# LogJam

LogJam is a configurable tool for filtering text files using custom filter definitions.

## Features

- Filter lines in text files using logical operators (AND, OR, NOT).
- Define filters in JSON format.
- Command-line interface for batch processing.
- Example PyQt6 GUI starter.

## Usage

### CLI

```sh
python -m logjam.cli.main <filter_config.json> <input_file.txt> <output_file.txt> [--filter <filter_name>] [--verbose]
```

### Generate Example Config

```sh
python -m logjam.cli.main --example-config
```

## Filter Config Example

See `filter1.json` for a sample filter definition.

## Requirements

- Python 3.12+
- pyqt6

## License

MIT
