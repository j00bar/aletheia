import logging
import shutil
import tempfile

from ..utils import devel_dir, copytree


logger = logging.getLogger(__name__)


class Source:
    def __init__(self, path, devel=False):
        self.path = path
        self.devel = devel
        self._tempdir = None
    
    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.error('Error cleaning up local plugin.')
    
    @property
    def working_dir(self):
        if not self._tempdir:
            if self.devel:
                self._tempdir = devel_dir(f'local--{self.path}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir
 
    def run(self):
        copytree(self.path, self.working_dir, nonempty_ok=self.devel)
        return self.working_dir

