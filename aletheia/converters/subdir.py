import logging
import os
import shutil
import tempfile

from ..utils import devel_dir, copytree


logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, working_dir, path, devel=False, **kwargs):
        self.working_dir = working_dir
        self.path = path
        self.devel = devel
        self._tempdir = None
    
    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.error('Error cleaning up subdir plugin.')
    
    @property
    def output_dir(self):
        if not self._tempdir:
            if self.devel:
                self._tempdir = devel_dir(f'subdir--{self.path}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir
 
    def run(self):
        copytree(os.path.join(self.working_dir, self.path), self.output_dir, nonempty_ok=self.devel)
        return self.output_dir

