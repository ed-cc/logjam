# LogJam

LogJam is a configurable tool for filtering text and log files using custom,
reusable filter definitions. It ships with both a command-line interface for
batch processing and a PyQt6 desktop GUI for interactive exploration.

## Features

- Filter lines using logical operators: **AND**, **OR**, **NOT**.
- **Nested sub-filters** for composing complex logic (e.g. "is an error AND NOT
  a timeout").
- **Substring or regular-expression** matching, with optional case sensitivity.
- Define multiple named filters in a single JSON config and switch between them.
- **CLI** for scripted/batch filtering.
- **GUI** with a filter-management panel, original line numbers, find &
  highlight, recent files, and persisted window layout.

## Installation

LogJam uses [uv](https://docs.astral.sh/uv/) for dependency management.

```sh
uv sync
```

The GUI depends on PyQt6, which needs a few system libraries on Linux
(`libEGL`, `libGL`, `libxkbcommon`, `libdbus`). On Debian/Ubuntu:

```sh
sudo apt-get install -y libegl1 libgl1 libxkbcommon0 libdbus-1-3
```

## Usage

### CLI

```sh
uv run python -m logjam.cli.main <filter_config.json> <input_file.txt> <output_file.txt> [--filter <filter_name>] [--verbose]
```

If `--filter` is omitted, the first filter in the config is used. Example with
the bundled sample data:

```sh
uv run python -m logjam.cli.main examples/filters.json examples/sample.log out.txt --filter Errors
```

#### Generate an example config

```sh
uv run python -m logjam.cli.main --example-config
```

### GUI

```sh
uv run python -m logjam.ui.main
```

You can also open a file (and optionally a filter config) directly:

```sh
uv run python -m logjam.ui.main examples/sample.log -f examples/filters.json
```

In the GUI:

- **Filters panel** (left dock): create, edit, duplicate, remove, and select
  filters. The selected filter is applied live to the open file.
- **Edit Filter dialog**: set the operator, criteria (one per line), regex and
  case-sensitivity options, and manage nested sub-filters.
- **Find** (`Ctrl+F`): highlight and step through matches in the results.
- **View menu**: toggle the Filters panel and open Find.
- Recently opened files are available under **File → Open Recent**, and the
  window layout is restored between sessions.

## Configuration format

A config is a JSON object with a `filters` list. Each filter has a name, a
logical operator, optional `regex`/`case_sensitive` flags, a list of
`filter_strings`, and an optional list of nested `filters` (sub-filters):

```json
{
    "filters": [
        {
            "name": "Errors",
            "logical_operator": "OR",
            "regex": false,
            "case_sensitive": false,
            "filter_strings": ["error", "critical", "fatal"],
            "filters": []
        }
    ]
}
```

A line matches a filter when its `filter_strings` and `sub_filters`, combined
under the chosen operator, are satisfied:

- **OR** — matches if *any* criterion or sub-filter matches.
- **AND** — matches if *all* criteria and sub-filters match.
- **NOT** — matches if *none* of the criteria or sub-filters match.

When `regex` is true, each entry in `filter_strings` is treated as a regular
expression (matched with `re.search`); otherwise it is a plain substring.

See [`examples/filters.json`](examples/filters.json) and
[`examples/sample.log`](examples/sample.log) for a complete, working example,
including a nested filter.

## Development

Run the test suite (core, CLI, and GUI tests):

```sh
uv run pytest
```

GUI tests run headless via Qt's `offscreen` platform (configured in
`test/ui/conftest.py`) and require the system libraries listed under
[Installation](#installation).

## Requirements

- Python 3.12+
- PyQt6

## License

MIT
