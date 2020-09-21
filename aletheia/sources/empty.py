import logging
import shutil
import tempfile

from .. import DEFAULTS
from ..utils import devel_dir


logger = logging.getLogger(__name__)


class Source:
    def __init__(self, config=DEFAULTS, **kwargs):
        self.config = config
        self._tempdir = None

    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.error('Error cleaning up empty plugin.')

    @property
    def working_dir(self):
        if not self._tempdir:
            if self.config.devel:
                self._tempdir = devel_dir('empty--')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def run(self):
        logger.info('Empty source.')
        return self.working_dir

