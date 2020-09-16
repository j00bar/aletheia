import logging

from .. import DEFAULTS


logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, working_dir, config=DEFAULTS, **kwargs):
        self.working_dir = working_dir
        self.config = config
        self._tempdir = None
    
    def cleanup(self):
        pass

    def run(self):
        logger.info('Noop plugin.')
        return self.working_dir

