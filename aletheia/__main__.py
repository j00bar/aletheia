import argparse
import logging
import logging.config
import os
import sys

import toml

from . import DEFAULTS, command


logger = logging.getLogger(__name__)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Documentation aggregator that collects sources of truth and assimilates them into a single tree."
    )
    parser.add_argument(
        "--config-dir",
        action="store",
        help="Path where config files and credentials are found.",
        default="/etc/aletheia",
    )

    subparsers = parser.add_subparsers(dest="command")

    assemble_parser = subparsers.add_parser("assemble")
    assemble_parser.add_argument(
        "path", help="Path of the core documentation tree documentation tree", default=".", nargs="?"
    )

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument(
        "--src", "-s", dest="src", help="Path to documentation source (default is current working directory)"
    )
    build_parser.add_argument("target", help="Path to output assembled documentation tree")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("src", help="Source path or GitHub repository.")
    export_parser.add_argument("target", help="Target GitHub repository.")

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("path", help="Path to initialize with Aletheia data", default=".", nargs="?")

    params = parser.parse_args(args or sys.argv[1:])
    config = DEFAULTS.copy()
    try:
        config.update(toml.load(open(os.path.join(params.config_dir, "config.toml"))))
    except OSError:
        # There is no config.toml
        pass
    except (TypeError, toml.TomlDecodeError):
        raise
    config["config_dir"] = params.config_dir

    logging_config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {"simple": {"format": "{levelname}:{module}:{message}", "style": "{"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
            }
        },
        "loggers": {
            "aletheia": {"handlers": ["console"], "level": "DEBUG" if config.devel else "INFO", "propagate": False}
        },
    }
    logging.config.dictConfig(logging_config)

    if params.command == "build":
        command.build(params.target, path=params.src, config=config)
    elif params.command == "assemble":
        command.assemble(params.path, config=config)
    elif params.command == "init":
        command.init(params.path, config=config)
    elif params.command == "export":
        command.export(params.src, params.target, config=config)


if __name__ == "__main__":
    main()
