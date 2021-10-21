from distutils.spawn import find_executable
import logging
import os
import pathlib
import shutil
import subprocess
import re

import semver

from .exceptions import ConfigError

logger = logging.getLogger(__name__)
VERSION_STRING_RE = re.compile(
    r"([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?"  # noqa: E501
)


def ensure_dependencies(*deps):
    for dep, version in deps:
        executable = find_executable(dep)
        if not executable:
            raise ConfigError(f"Could not find executable for {dep}")
        if version:
            result = subprocess.run([executable, "--version"], stdout=subprocess.PIPE)
            if result.returncode == 0:
                match_obj = VERSION_STRING_RE.search(result.stdout.decode("utf8"))
                if not match_obj:
                    raise ConfigError(f"Could not confirm {dep} is at least version {version}")
                matched_version = match_obj.group(0)
                if semver.compare(matched_version, version) == -1:
                    raise ConfigError(
                        f"Installed {dep} is version {matched_version}, but at least {version} required."
                    )
            else:
                raise ConfigError(f"Error confirming {dep} version: {result.stderr}")


def devel_dir(path_component):
    to_return = os.path.join(pathlib.Path.home(), ".local", "cache", "aletheia", path_component)
    if os.path.exists(to_return):
        shutil.rmtree(to_return)
    os.makedirs(to_return, exist_ok=True)
    return to_return


def copytree(src, dest, nonempty_ok=False):
    # It's annoying that shutil.copytree doesn't work on an empty, already-existing directory. Let's fix that.
    if os.path.exists(dest):
        if os.path.isdir(dest):
            if os.listdir(dest) and not nonempty_ok:
                raise OSError(f"Copying into a non-entry directory {dest}.")
        else:
            raise OSError(f"Destination {dest} is not a directory.")
    else:
        os.makedirs(dest)
    for filename in os.listdir(src):
        file_path = os.path.join(src, filename)
        dest_file_path = os.path.join(dest, filename)
        if os.path.isdir(file_path):
            copytree(file_path, dest_file_path, nonempty_ok=nonempty_ok)
        else:
            shutil.copy2(file_path, dest_file_path)
