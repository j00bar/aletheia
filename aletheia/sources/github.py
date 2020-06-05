import logging
import os
import subprocess
import shutil
import tempfile

from ..utils import ensure_dependencies, devel_dir
from ..exceptions import AletheiaExeception

logger = logging.getLogger(__name__)
ensure_dependencies(('git', '2.3.0'))


class Source:
    def __init__(self, repo, branch='master', devel=False):
        self.repo = repo
        self.branch = branch
        self.devel = devel
        self._tempdir = None
    
    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.error('Error cleaning up Github plugin.')
    
    @property
    def working_dir(self):
        if not self._tempdir:
            if self.devel:
                self._tempdir = devel_dir(f'github--{self.repo}--{self.branch}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir
    
    def run(self):
        logger.info(f'Cloning GitHub repo {self.repo}.')
        if self.devel and os.path.exists(os.path.join(self.working_dir, '.git')):
            result = subprocess.run(['git', 'reset', '--hard'],
                                    # env=dict(GIT_TERMINAL_PROMPT='0'),
                                    cwd=self.working_dir)
            result = subprocess.run(['git', 'pull', '--rebase', 'origin'],
                                    # env=dict(GIT_TERMINAL_PROMPT='0'),
                                    cwd=self.working_dir)
        else:
            result = subprocess.run(['git', 'clone', f'https://github.com/{self.repo}', '-b', self.branch, '.'],
                                    # env=dict(GIT_TERMINAL_PROMPT='0'),
                                    cwd=self.working_dir)
        if not result.returncode == 0:
            logger.error(f'Failed to clone repository - git exited with {result.returncode}')
            raise AletheiaExeception('Error retrieving source.')
        return self.working_dir
        



