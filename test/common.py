import json
import os
import tempfile


def make_filter_config_file():
    config = {
        "filters": [
            {
                "name": "testfilter",
                "logical_operator": "OR",
                "regex": False,
                "filter_strings": ["foo", "bar"],
                "filters": [],
            }
        ]
    }
    fd, path = tempfile.mkstemp(suffix=".json", text=True)
    with os.fdopen(fd, "w") as f:
        json.dump(config, f)
    return path


def make_input_file():
    lines = ["foo bar baz", "foo baz", "bar baz", "baz qux"]
    fd, path = tempfile.mkstemp(text=True)
    with os.fdopen(fd, "w") as f:
        for line in lines:
            f.write(line + "\n")
    return path
