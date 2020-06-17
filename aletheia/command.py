import logging
import os
import shutil
import tempfile

from . import pipeline, exceptions
from .utils import devel_dir, copytree

logger = logging.getLogger(__name__)


def build(target, path=None, preserve=False, devel=False):
    path = path or os.getcwd()
    target = target.rstrip('/')

    if os.path.exists(target):
        if os.listdir(target) and not devel:
            raise exceptions.AletheiaExeception(f'Target path {target} exists and is non-empty.')
    else:
        if not os.path.exists(os.path.dirname(target)) and os.path.isdir(os.path.dirname(target)):
            raise exceptions.AletheiaExeception(f'No such parent directory for target path {target}.')

    temp_dir = tempfile.mkdtemp()
    cleanup = not devel

    try:
        working_dir = os.path.join(temp_dir, 'aletheia')
        copytree(path, working_dir)
        for root, dirs, files in os.walk(working_dir):
            rel_path = os.path.relpath(root, working_dir)
            if files == ['aletheia.yml']:
                file_path = os.path.join(root, files[0])
                logger.info(f'Processing docs source in {rel_path}.')
                pipeline_obj = pipeline.Pipeline(file_path, devel=devel)
                pipeline_obj.load()
                pipeline_obj.run()
                logger.info(f'Finished processing docs source in {rel_path}.')
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


def assemble(path, devel=False):
    path = path or os.getcwd()

    for root, dirs, files in os.walk(path):
        rel_path = os.path.relpath(root, path)
        if 'aletheia.yml' in files:
            file_path = os.path.join(root, 'aletheia.yml')
            logger.info(f'Processing docs source in {rel_path}.')
            pipeline_obj = pipeline.Pipeline(file_path, devel=devel)
            pipeline_obj.load()
            pipeline_obj.run()
            logger.info(f'Finished processing docs source in {rel_path}.')


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


def init(path, devel=False):
    path = path or os.getcwd()

    if os.path.exists(os.path.join(path, 'aletheia.yml')):
        raise exceptions.AletheiaExeception(f'Path {os.path.abspath(path)} already has an aletheia.yml file.')

    with open(os.path.join(path, 'aletheia.yml'), 'w') as ofs:
        ofs.write(ALETHEIA_YML)
    
    with open(os.path.join(path, '.gitignore'), 'w') as ofs:
        ofs.write(GITIGNORE)

    logger.info(f'Initialized empty Aletheia config in {os.path.abspath(path)}.')
