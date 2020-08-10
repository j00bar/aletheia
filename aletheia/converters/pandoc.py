import datetime
import logging
import os
import shutil
import subprocess
import tempfile

import yaml

from ..utils import ensure_dependencies, devel_dir, copytree
from ..exceptions import AletheiaExeception


logger = logging.getLogger(__name__)
ensure_dependencies(('pandoc', None))
FILE_EXTENSION_MAP = {
    'html': ['.html', '.htm'],
}


class Plugin:
    def __init__(self, working_dir, format, file_extensions=None, metadata=None, devel=False):
        self.working_dir = working_dir
        self.format = format
        self.file_extensions = file_extensions or FILE_EXTENSION_MAP.get(format, ['.'+format])
        self._metadata = metadata or {}
        self._tempdir = None
        self.devel = devel

    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.exception('Error cleaning up Pandoc plugin.')

    @property
    def output_dir(self):
        if not self._tempdir:
            if self.devel:
                self._tempdir = devel_dir(f'pandoc--{self.working_dir.replace("/", "--")}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def run(self):
        logger.info(f'Converting files from {self.format} to Markdown using Pandoc.')
        for root, dirs, files in os.walk(self.working_dir):
            for filename in files:
                logger.debug('Filename: %s', filename)
                input_path = os.path.join(root, filename)
                rel_path = os.path.relpath(root, self.working_dir)
                os.makedirs(os.path.join(self.output_dir, rel_path), exist_ok=True)
                base, ext = os.path.splitext(filename)
                if ext in self.file_extensions:
                    output_path = os.path.join(self.output_dir, rel_path, f'{base}.md')
                    result = subprocess.run(
                        ['pandoc', '-s', '-f', self.format, '-t', 'commonmark', input_path, '-o', output_path]
                    )
                    if result.returncode != 0:
                        raise AletheiaExeception('Error during pandoc conversion to Markdown.')
                    modtime = os.stat(input_path).st_mtime
                    os.utime(output_path, (modtime, modtime))
                else:
                    output_path = os.path.join(self.output_dir, rel_path, filename)
                    shutil.copy2(input_path, output_path)
        return self.output_dir
