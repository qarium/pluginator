import os
import shutil
import tempfile
import typing as t
from dataclasses import dataclass

import pytest

from pluginator import define
from pluginator.pytest import CommandLine, PluginMeta, PluginOption
from pluginator.utils import call_context


@dataclass
class TmpFile:
    filepath: str
    content: str
    expected_value: str


def meta_decorator(meta_type):
    def wrapper(cls):
        if t.TYPE_CHECKING:
            cls.__meta__ = meta_type
        return cls

    return wrapper


@pytest.fixture(scope="session")
def default_plugin():
    @define.plugin("test-plugin")
    @meta_decorator(PluginMeta)
    class Test:
        pass

    return Test


@pytest.fixture(scope="session", name="config_file")
def create_config_file():
    tmpdir = tempfile.mkdtemp()
    value = "hello world"
    content = f"name: {value}"
    tmp_file = os.path.join(tmpdir, "config.yml")

    with open(tmp_file, "w", encoding="UTF-8") as f:
        f.write(content)

    yield TmpFile(tmp_file, content, value)

    shutil.rmtree(tmpdir)


@pytest.fixture(scope="session")
def custom_plugin(config_file):
    @define.plugin("test-config", config=config_file.filepath, deps=["test-dep1", "test-dep2"])
    @meta_decorator(PluginMeta)
    class Test:
        name = define.option(str, required=True, plugin_config_key="name")

        @pytest.fixture()
        def config_name(self):
            return self.name

    return Test


# pylint: disable = W0612
@pytest.fixture(scope="session")
def test_func():
    def _test_func():
        _local_var = 0  # noqa: F841
        return call_context()

    return _test_func


@pytest.fixture(scope="session", name="command_line")
def create_command_line():
    return CommandLine("--test-option", "test-arg", action="store", help="test command")


@pytest.fixture(scope="session")
def plugin_option(command_line):
    return PluginOption(
        int,
        required=True,
        env_var="test",
        default_from="test-default",
        plugin_config_key="test-key",
        command_line=command_line,
        strict=False,
    )
