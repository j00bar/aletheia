__version__ = '0.1.0'


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        return type(self)(self.__dict__)


DEFAULTS = AttrDict(
    devel=False,
    config_dir='/etc/aletheia'
)
