import argparse
import logging
import logging.config
import sys

from . import command

logger = logging.getLogger(__name__)

def main(args=None):
    parser = argparse.ArgumentParser(
        description='Documentation aggregator that collects sources of truth and assimilates them into a single tree.'
    )
    parser.add_argument('--devel', action='store_true', help='Developer mode (For use during aletheia development)')
    parser.add_argument(
        '--config-dir', action='store', help='Path where config files and credentials are found.',
        default='/etc/aletheia')

    subparsers = parser.add_subparsers(dest='command')

    assemble_parser = subparsers.add_parser('assemble')
    assemble_parser.add_argument(
        'path', help='Path of the core documentation tree documentation tree', default='.', nargs='?'
    )

    build_parser = subparsers.add_parser('build')
    build_parser.add_argument(
        '--src', '-s', dest='src', help='Path to documentation source (default is current working directory)'
    )
    build_parser.add_argument(
        'target', help='Path to output assembled documentation tree'
    )

    export_parser = subparsers.add_parser('export')
    export_parser.add_argument(
        'src', help='Source path or GitHub repository.'
    )
    export_parser.add_argument(
        'target', help='Target GitHub repository.'
    )

    init_parser = subparsers.add_parser('init')
    init_parser.add_argument(
        'path', help='Path to initialize with Aletheia data', default='.', nargs='?'
    )

    config = parser.parse_args(args or sys.argv[1:])

    logging_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'simple': {
                'format': "{levelname}:{module}:{message}",
                'style': '{'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
            }
        },
        'loggers': {
            'aletheia': {
                'handlers': ['console'],
                'level': 'DEBUG' if config.devel else 'INFO',
                'propagate': False
            }
        }
    }
    logging.config.dictConfig(logging_config)

    if config.command == 'build':
        kwargs = dict(path=config.src, devel=config.devel, config_dir=config.config_dir)
        command.build(config.target, **kwargs)
    elif config.command == 'assemble':
        kwargs = dict(devel=config.devel, config_dir=config.config_dir)
        command.assemble(config.path, **kwargs)
    elif config.command == 'init':
        kwargs = dict(devel=config.devel, config_dir=config.config_dir)
        command.init(config.path, **kwargs)
    elif config.command == 'export':
        kwargs = dict(devel=config.devel, config_dir=config.config_dir)
        command.export(config.src, config.target, **kwargs)

if __name__ == '__main__':
    main()