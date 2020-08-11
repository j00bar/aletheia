import datetime
import logging
import os
import re
import shutil
import tempfile

from bs4 import BeautifulSoup
import yaml

from ..utils import devel_dir

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, working_dir, weight=0, add_index=False, index_title=None, filename_as_title=False, devel=False, **kwargs):
        self.working_dir = working_dir
        self.weight = weight
        self.filename_as_title = filename_as_title
        self.add_index = add_index
        self.index_title = index_title
        self._tempdir = None
        self.devel = devel

    @property
    def output_dir(self):
        if not self._tempdir:
            if self.devel:
                self._tempdir = devel_dir(f'hugoify--{self.working_dir.replace("/", "--")}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def cleanup(self):
        if self._tempdir:
            try:
                shutil.rmtree(self._tempdir)
            except:  # noqa: E722
                logger.exception('Error cleaning up Hugoify plugin.')

    def get_mtime(self, input_path):
        input_stat = os.stat(input_path)
        return datetime.datetime.fromtimestamp(input_stat.st_mtime)
    
    ATX_H1_REGEX = re.compile(r'^ {0,3}# +(.*)$')
    SETEXT_H1_REGEX = re.compile(r'^ {0,3}(=)+ *$')

    def extract_title(self, base, md_content):
        # If we don't find a title, use the base as it
        title = base

        if self.filename_as_title and base != '_index':
            content = md_content
        else:
            # Scan the md_content line by line for an H1 to use as the title
            md_lines = md_content.splitlines()
            for idx, line in enumerate(md_lines):
                match_obj = self.ATX_H1_REGEX.match(line)
                if match_obj:
                    title = match_obj.group(1).strip() or title
                    md_lines.pop(idx)
                    break
                else:
                    if self.SETEXT_H1_REGEX.match(line):
                        title = md_lines[idx-1].strip() or title
                        md_lines.pop(idx)
                        md_lines.pop(idx-1)
                        break
            content = '\n'.join(md_lines)

        bs = BeautifulSoup(title, 'html.parser')
        title = ' '.join([node.string for node in bs.find_all(text=True)])
        return title, content

    def run(self):
        max_timestamp = 0.0
        for root, dirs, files in os.walk(self.working_dir):
            for filename in files:
                input_path = os.path.join(root, filename)
                rel_path = os.path.relpath(root, self.working_dir)
                os.makedirs(os.path.join(self.output_dir, rel_path), exist_ok=True)
                base, ext = os.path.splitext(filename)
                if ext == '.md':
                    max_timestamp = max(max_timestamp, os.stat(input_path).st_mtime)
                    output_filename = '_index.md' if base == 'index' else f'{base}.md'
                    output_path = os.path.join(self.output_dir, rel_path, output_filename)
                    with open(input_path) as ifs:
                        with open(output_path, 'w') as ofs:
                            md_content = ifs.read()
                            mtime = self.get_mtime(input_path)
                            title, html_content = self.extract_title(base, md_content)
                            metadata = dict(title=title, date=mtime)
                            if base == 'index':
                                metadata['weight'] = self.weight

                            ofs.writelines([
                                '---\n',
                                yaml.dump(metadata),
                                '---\n',
                                html_content
                            ])
                    os.utime(output_path, (os.stat(input_path).st_mtime, os.stat(input_path).st_mtime))
                else:
                    output_path = os.path.join(self.output_dir, rel_path, filename)
                    shutil.copy2(input_path, output_path)
        if self.add_index:
            index_path = os.path.join(self.output_dir, '_index.md')
            if os.path.exists(index_path):
                logger.warn('Hugoify plugin told to add index, but index already exists!')
            else:
                metadata = dict(
                    title=self.index_title, 
                    date=datetime.datetime.fromtimestamp(max_timestamp), 
                    weight=self.weight)
                with open(index_path, 'w') as ofs:
                    ofs.writelines([
                        '---\n',
                        yaml.dump(metadata),
                        '---\n'
                    ])
                os.utime(index_path, (max_timestamp, max_timestamp))
        return self.output_dir

