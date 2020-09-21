import logging
import os
import shutil
import subprocess
import tempfile

from .. import DEFAULTS, exceptions
from ..utils import ensure_dependencies, copytree, devel_dir

ensure_dependencies(('plantuml', None))
logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, working_dir, config=DEFAULTS, cmdline_args=[], keep_puml=False, **kwargs):
        self.working_dir = working_dir
        self.cmdline_args = cmdline_args
        self.keep_puml = keep_puml
        self.config = config
        self._tempdir = None

    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.error('Error cleaning up plantuml plugin.')

    @property
    def output_dir(self):
        if not self._tempdir:
            if self.config.devel:
                self._tempdir = devel_dir(f'plantuml--{self.working_dir.replace("/", "--")}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def run(self):
        copytree(self.working_dir, self.output_dir)
        logger.info('Searching for PlantUML files to compile.')
        for root, dirs, files in os.walk(self.output_dir):
            for filename in files:
                if filename.endswith(('.plantuml', '.puml')):
                    file_path = os.path.join(root, filename)
                    logger.info(f'Converting PlantUML diagram at {file_path}')
                    result = subprocess.run(
                        ['plantuml'] + self.cmdline_args + ['-o', os.path.abspath(root), file_path]
                    )
                    if result.returncode != 0:
                        raise exceptions.AletheiaException('Builder returned non-zero exit code.')
                    if not self.keep_puml:
                        os.remove(file_path)
        logger.info('PlantUML scan complete.')
        return self.output_dir

