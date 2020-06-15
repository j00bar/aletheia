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
    
    subparsers = parser.add_subparsers(dest='command')
    
    build_parser = subparsers.add_parser('build')
    build_parser.add_argument(
        '--src', '-s', dest='src', help='Path to documentation source (default is current working directory)'
    )
    build_parser.add_argument(
        'target', help='Path to output assembled documentation tree'
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
        kwargs = dict(path=config.src, devel=config.devel)
        command.build(config.target, **kwargs)

if __name__ == '__main__':
    main()