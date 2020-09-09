import datetime
import logging
import os
import shutil
import subprocess
import tempfile
from urllib import parse as urlparse

from . import pipeline, exceptions
from .sources import git
from .utils import copytree

logger = logging.getLogger(__name__)


def __process_pipeline(path, devel=False, remove_artifacts=False, config_dir=None):
    for root, dirs, files in os.walk(path):
        rel_path = os.path.relpath(root, path)
        if 'aletheia.yml' in files:
            file_path = os.path.join(root, 'aletheia.yml')
            logger.info(f'Processing docs source in {rel_path}.')
            pipeline_obj = pipeline.Pipeline(file_path, devel=devel, config_dir=config_dir)
            pipeline_obj.load()
            pipeline_obj.run()
            if remove_artifacts:
                os.remove(file_path)
                if os.path.exists(os.path.join(root, '.gitignore')):
                    os.remove(os.path.join(root, '.gitignore'))
            logger.info(f'Finished processing docs source in {rel_path}.')


def __local_or_github(path):
    if path.startswith('https://'):
        # This is a git repo url
        url_parts = urlparse.urlparse(path)
        hostname = url_parts.netloc
        url_path = url_parts.path.lstrip('/')
        if '@' in url_path:
            repo, branch = url_path.split('@')
        else:
            repo, branch = url_path, 'master'
        plugin = git.Source(hostname, repo, branch)
        to_return = plugin.run(), plugin.cleanup
    else:
        to_return = path or os.getcwd(), lambda: None
    return to_return


def build(target, path=None, preserve=False, remove_artifacts=False, devel=False, config_dir=None):
    path, callback = __local_or_github(path or os.getcwd())
    target = target.rstrip('/')

    if os.path.exists(target):
        if os.listdir(target) and not devel:
            raise exceptions.AletheiaException(f'Target path {target} exists and is non-empty.')
    else:
        if not os.path.exists(os.path.dirname(target)) and os.path.isdir(os.path.dirname(target)):
            raise exceptions.AletheiaException(f'No such parent directory for target path {target}.')

    temp_dir = tempfile.mkdtemp()
    cleanup = not devel

    try:
        working_dir = os.path.join(temp_dir, 'aletheia')
        copytree(path, working_dir)
        __process_pipeline(working_dir, devel, remove_artifacts=remove_artifacts, config_dir=config_dir)
        if not os.path.exists(target):
            os.mkdir(target)
        copytree(working_dir, target, nonempty_ok=devel)
    except:  # noqa: E722
        if preserve:
            logger.exception(f'Error during build. Preserving build directory in {temp_dir}.')
            cleanup = False
        else:
            logger.exception('Error during build.')
        raise
    finally:
        if cleanup:
            shutil.rmtree(temp_dir)
            callback()


def assemble(path, devel=False, config_dir=None):
    path = path or os.getcwd()
    __process_pipeline(path, devel, config_dir=config_dir)


def export(path, dest_repo, devel=False, config_dir=None):
    if not dest_repo.startswith('https://'):
        raise ValueError('The destination repo must be of the format https://hostname/account/project[@branch]')

    # build_dir is where we will assemble the current build
    build_dir = tempfile.mkdtemp()

    try:
        # export_dir is where we will clone the destination repo
        export_dir, cleanup_callback = __local_or_github(dest_repo)
        build(build_dir, path, devel=devel, remove_artifacts=True, config_dir=config_dir)
        # remove the .git from the build tree and move the destination repo's .git over
        # that way we let git do the resolution of everything
        shutil.rmtree(os.path.join(build_dir, '.git'))
        copytree(
            os.path.join(export_dir, '.git'),
            os.path.join(build_dir, '.git')
        )

        # Did anything change?
        result = subprocess.run(['git', 'diff', '--exit-code'], cwd=build_dir)
        if result.returncode == 0:
            logger.info('No changes detected.')
            return

        result = subprocess.run(['git', 'add', '.'],
                                # env=dict(GIT_TERMINAL_PROMPT='0'),
                                cwd=build_dir)
        if result.returncode:
            raise exceptions.AletheiaException('Error updating destination git repo.')
        result = subprocess.run(['git', 'commit', '-m', f'Aletheia docs build {datetime.datetime.utcnow()}'],
                                cwd=build_dir)
        if result.returncode:
            raise exceptions.AletheiaException('Error committing changes.')
        result = subprocess.run(['git', 'push'], cwd=build_dir)
        if result.returncode:
            raise exceptions.AletheiaException('Error pushing changes.')
    finally:
        try:
            shutil.rmtree(build_dir)
            cleanup_callback()
        except:  # noqa: E722
            pass


ALETHEIA_YML = '''
pipeline:
- empty: {}
- noop: {}
'''.lstrip()

GITIGNORE = '''
*
**/*
!aletheia.yml
!.gitignore
'''.lstrip()


def init(path, devel=False, config_dir=None):
    path = path or os.getcwd()

    if os.path.exists(os.path.join(path, 'aletheia.yml')):
        raise exceptions.AletheiaException(f'Path {os.path.abspath(path)} already has an aletheia.yml file.')

    with open(os.path.join(path, 'aletheia.yml'), 'w') as ofs:
        ofs.write(ALETHEIA_YML)
    
    with open(os.path.join(path, '.gitignore'), 'w') as ofs:
        ofs.write(GITIGNORE)

    logger.info(f'Initialized empty Aletheia config in {os.path.abspath(path)}.')
