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

### GUI Application

```sh
python -m logjam.ui.main
```

Alternatively, provide a file and an optional config as arguments:
```sh
python -m logjam.ui.main <input_file.txt> -f <filter_config.json>

## Requirements

- Python 3.12+
- pyqt6

## License

MIT
