import atexit
import io
import logging
import os
import sys
import tempfile
import traceback

import jinja2
import yaml

from . import DEFAULTS
from .builders import sphinx, plantuml
from .exceptions import ConfigError
from .converters import pandoc, hugoify, subdir, noop
from .sources import git, googledrive, local, empty
from .utils import copytree


logger = logging.getLogger(__name__)
PLUGINS = {
    'sphinx': sphinx.Plugin,
    'pandoc': pandoc.Plugin,
    'github': git.Source,
    'git': git.Source,
    'googledrive': googledrive.Source,
    'hugoify': hugoify.Plugin,
    'local': local.Source,
    'subdir': subdir.Plugin,
    'empty': empty.Source,
    'noop': noop.Plugin,
    'plantuml': plantuml.Plugin
}


class Pipeline:
    def __init__(self, pipeline_file, config=DEFAULTS):
        self.pipeline_file = pipeline_file
        self.target_dir = os.path.dirname(self.pipeline_file)
        self.pipeline = []
        self.config = config
    
    def load(self):
        with open(self.pipeline_file) as ifs:
            pipeline_data = yaml.safe_load(stream=ifs)
        
        if not pipeline_data.get('enabled', True):
            return
        
        for i, stage in enumerate(pipeline_data['pipeline']):
            try:
                plugin_name = next(key for key in stage if key in PLUGINS)
            except StopIteration:
                raise ConfigError(f'Could not find valid plugin in pipeline stage {i}')
            self.pipeline.append(
                (plugin_name, PLUGINS[plugin_name], stage[plugin_name])
            )
        
    def run(self, merge=True):
        args = ()
        output_dir = None
        for plugin_name, plugin_cls, kwargs in self.pipeline:
            plugin_instance = plugin_cls(*args, config=self.config, **kwargs)
            if not self.config.devel:
                atexit.register(plugin_instance.cleanup)
            try:
                output_dir = plugin_instance.run()
            except Exception:
                logger.exception('Pipeline plugin error.')
                stacktrace = '\n'.join(traceback.format_exception(*sys.exc_info()))
                output_dir = self.capture_build_error(plugin_name, kwargs, stacktrace)
                break
            args = (output_dir,)
        if merge and output_dir:
            self.merge(output_dir)
            return self.target_dir
        else:
            return output_dir

    def capture_build_error(self, plugin_name, plugin_params, stacktrace):
        plugin_info = io.StringIO()
        source_info = io.StringIO()
        source_name, _, source_params = self.pipeline[0]
        yaml.safe_dump({plugin_name: plugin_params}, plugin_info)
        yaml.safe_dump({source_name: source_params}, source_info)
        context = dict(
            dirname=os.path.basename(self.target_dir),
            plugin_info=plugin_info.getvalue(),
            source_info=source_info.getvalue(),
            stacktrace=stacktrace
        )
        if os.path.isabs(self.config.error_template):
            template_path = self.config.error_template
        else:
            template_path = os.path.join(os.path.dirname(__file__), self.config.error_template)
        with open(template_path, 'r') as ifs:
            template_obj = jinja2.Template(ifs.read())
        tempdir = tempfile.mkdtemp()
        with open(os.path.join(tempdir, self.config.error_result_filename), 'w') as ofs:
            ofs.write(template_obj.render(context))
        return tempdir

    def merge(self, output_dir):
        copytree(output_dir, self.target_dir, nonempty_ok=True)
    