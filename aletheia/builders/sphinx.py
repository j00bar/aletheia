import datetime
import logging
import os
import re
import shutil
import subprocess
import time
from urllib import parse as urlparse

from bs4 import BeautifulSoup

from ..utils import ensure_dependencies
from ..exceptions import AletheiaExeception
from ..converters import pandoc


logger = logging.getLogger(__name__)
ensure_dependencies(('sphinx-build', None),
                    ('pipenv', None),
                    ('poetry', None))


class Plugin:
    def __init__(self, working_dir, dir='docs', install_deps=False, title=None, devel=False):
        self.working_dir = working_dir
        self.dir = dir
        self.use_pipenv = install_deps and os.path.exists(os.path.join(working_dir, 'Pipfile'))
        self.use_poetry = install_deps and os.path.exists(os.path.join(working_dir, 'poetry.lock'))
        self.title = title
        self.devel = devel

    def cleanup(self):
        if self.use_pipenv:
            env = dict(os.environ)
            env.update(
                dict(
                    PIPENV_PIPFILE=os.path.join(self.working_dir, 'Pipfile'),
                    PIPENV_IGNORE_VIRTUALENVS='1'
                )
            )
            subprocess.run(['pipenv', '--rm'], cwd=self.working_dir, env=env)
        elif self.use_poetry:
            result = subprocess.run(['poetry', 'env', 'info', '--path'], cwd=self.working_dir, stdout=subprocess.PIPE)
            if result.returncode == 0:
                try:
                    shutil.rmtree(result.stdout)
                except:  # noqa: E722
                    logger.error('Error cleaning up Sphinx plugin.')

    def __modify_sphinx_theme_settings(self):
        # Modify the theme to be fully minimal
        try:
            sourcedir = re.search(
                r'SOURCEDIR\s*=\s*([^\s]+)',
                open(os.path.join(self.working_dir, self.dir, 'Makefile')).read()).group(1)
        except AttributeError:
            raise AletheiaExeception('Could not extract SOURCEDIR from Makefile.')
        sourcedir = os.path.normpath(os.path.join(self.working_dir, self.dir, sourcedir))
        conf_py = os.path.join(sourcedir, 'conf.py')
        if not os.path.exists(conf_py):
            raise AletheiaExeception(f'Could not find conf.py in {sourcedir}.')
        conf_py_src = open(conf_py).read()
        conf_py_src = re.sub(
            r'^html_theme\s*=\s*[\'"][^\'"]+[\'"]',
            'html_theme = "basic"',
            conf_py_src,
            flags=re.MULTILINE)
        templates_path = os.path.join(os.path.dirname(__file__), 'sphinx_templates')
        conf_py_src = re.sub(
            r'^templates_path\s*=\s*\[[^\]]*\]',
            f'templates_path = ["{templates_path}"]',
            conf_py_src,
            flags=re.MULTILINE
        )
        open(conf_py, 'w').write(conf_py_src)

    def __clean_html_markup(self, html_dir, mod_time):
        logger.info('Cleaning up HTML markup from Sphinx output.')
        seen = []
        for root, dirs, files in os.walk(html_dir):
            for filename in files:
                if filename.endswith('.html'):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, html_dir)
                    if rel_path in seen:
                        continue
                    doc = BeautifulSoup(open(full_path).read(), 'html.parser')

                    # Get rid of permalink anchors
                    for element in doc.find_all('a', class_='headerlink'):
                        element.extract()

                    # Munge internal links to remove .html suffix
                    for element in doc.find_all('a', href=True):
                        href = urlparse.urlparse(element['href'])
                        if not href.netloc:
                            if href.path.endswith('.html'):
                                new_path = href.path[:-5] + '/'
                                element['href'] = urlparse.urlunparse((href.scheme,
                                                                       href.netloc,
                                                                       new_path,
                                                                       href.params,
                                                                       href.query,
                                                                       href.fragment))
                    
                    # if there's a .html file with the same name as a directory,
                    # move that file to index.html of the directory
                    #
                    # This fits with Hugo's content organization scheme.
                    base, ext = os.path.splitext(filename)
                    if base in dirs:
                        filename = 'index.html'
                        os.rename(full_path,
                                  os.path.join(root, base, filename))
                        full_path = os.path.join(root, base, filename)
                        rel_path = os.path.relpath(full_path, html_dir)

                    # Because Hugo turns files into paths, if this is not an index
                    # file, we have modify link paths to point into the parent dir
                    if filename != 'index.html':
                        for element in doc.find_all('a', href=True):
                            href = urlparse.urlparse(element['href'])
                            if not href.netloc and href.path and not href.path.startswith('/'):
                                new_path = f'../{href.path}'
                                element['href'] = urlparse.urlunparse((href.scheme,
                                                                       href.netloc,
                                                                       new_path,
                                                                       href.params,
                                                                       href.query,
                                                                       href.fragment))
                    # Given that we're renaming files and os.walk is weird, track
                    # what files we've seen before
                    seen.append(rel_path)
                    open(full_path, 'w').write(doc.prettify())

                    # Set mod_time based on source's original mod_time
                    os.utime(full_path, (mod_time, mod_time))

    def __find_latest_modtime(self):
        mod_time = 0
        for root, dirs, files in os.walk(self.working_dir):
            mod_time = max(
                [stat.st_mtime for stat in [
                    os.stat(f) for f in [
                        os.path.join(root, file) for file in files if file.endswith('.rst')
                        ]
                    ]
                ], default=mod_time
            )
        return mod_time

    def run(self):
        environ = dict(os.environ)

        if self.use_pipenv or self.use_poetry:
            logger.info('Creating virtualenv to install dependencies.')
            if self.use_pipenv:
                environ.update(
                    dict(PIPENV_PIPFILE=os.path.join(self.working_dir, 'Pipfile'),
                         PIPENV_IGNORE_VIRTUALENVS='1')
                )
                result = subprocess.run(
                    ['pipenv', 'sync', '--dev'],
                    cwd=self.working_dir,
                    env=environ
                )
            else:
                result = subprocess.run(
                    ['poetry', 'install'],
                    cwd=self.working_dir,
                    env=environ
                )
            if result.returncode != 0:
                raise AletheiaExeception('Builder pre-build returned non-zero exit code.')

        mod_time = self.__find_latest_modtime()

        self.__modify_sphinx_theme_settings()

        try:
            builddir = re.search(
                r'BUILDDIR\s*=\s*([^\s]+)',
                open(os.path.join(self.working_dir, self.dir, 'Makefile')).read()).group(1)
        except AttributeError:
            raise AletheiaExeception('Could not extract BUILDDIR from Makefile.')

        if self.devel and os.path.exists(os.path.join(self.working_dir, self.dir, builddir)):
            shutil.rmtree(os.path.join(self.working_dir, self.dir, builddir))

        if self.use_pipenv:
            wrapper = ['pipenv', 'run']
        elif self.use_poetry:
            wrapper = ['poetry', 'run']
        else:
            wrapper = []
        logger.info('Running Sphinx build.')
        result = subprocess.run(
            wrapper + ['make', 'html'],
            cwd=os.path.join(self.working_dir, self.dir),
            env=environ
        )
        if result.returncode != 0:
            raise AletheiaExeception('Builder returned non-zero exit code.')
        html_dir = os.path.normpath(
            os.path.join(self.working_dir, self.dir, builddir, 'html')
        )
        self.__clean_html_markup(html_dir, mod_time)

        return html_dir
