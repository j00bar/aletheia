from . import git


class Source(git.Source):
    def __init__(self, repo, branch='master', devel=False, **kwargs):
        super().__init__('github.com', repo, branch, devel, **kwargs)