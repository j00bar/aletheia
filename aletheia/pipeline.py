import atexit
import os

import yaml

from .builders import sphinx, plantuml
from .exceptions import ConfigError
from .converters import pandoc, hugoify, subdir, noop
from .sources import github, googledrive, local, empty
from .utils import copytree

PLUGINS = {
    'sphinx': sphinx.Plugin,
    'pandoc': pandoc.Plugin,
    'github': github.Source,
    'googledrive': googledrive.Source,
    'hugoify': hugoify.Plugin,
    'local': local.Source,
    'subdir': subdir.Plugin,
    'empty': empty.Source,
    'noop': noop.Plugin,
    'plantuml': plantuml.Plugin
}


class Pipeline:
    def __init__(self, pipeline_file, devel=False, config_dir=None):
        self.pipeline_file = pipeline_file
        self.target_dir = os.path.dirname(self.pipeline_file)
        self.pipeline = []
        self.devel = devel
        self.config_dir = config_dir
    
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
                (PLUGINS[plugin_name], stage[plugin_name])
            )
        
    def run(self, merge=True):
        args = ()
        output_dir = None
        for plugin, kwargs in self.pipeline:
            plugin_instance = plugin(*args, devel=self.devel, config_dir=self.config_dir, **kwargs)
            if not self.devel:
                atexit.register(plugin_instance.cleanup)
            output_dir = plugin_instance.run()
            args = (output_dir,)
        if merge and output_dir:
            return self.merge(output_dir)
        else:
            return output_dir
    
    def merge(self, output_dir):
        copytree(output_dir, self.target_dir, nonempty_ok=True)
                

    