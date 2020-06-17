import logging


logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, working_dir, devel=False):
        self.working_dir = working_dir
        self.devel = devel
        self._tempdir = None
    
    def cleanup(self):
        pass

    def run(self):
        logger.info('Noop plugin.')
        return self.working_dir

