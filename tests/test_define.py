# pylint: disable = W0212
import hamcrest as h
import pytest

from pluginator.pytest import PluginMeta, PluginOption
from pluginator.define import option


@pytest.mark.parametrize('expected_name', ('test-plugin', ))
def test_plugin_decorator_with_default_values(default_plugin, expected_name):
    default_plugin = default_plugin()

    h.assert_that(default_plugin.meta, h.instance_of(PluginMeta))
    h.assert_that(default_plugin.meta.name, h.equal_to(expected_name))
    h.assert_that(default_plugin.meta.config_file, h.none())
    h.assert_that(default_plugin.meta.default_config, h.none())
    h.assert_that(default_plugin.meta.dependencies, h.none())
    h.assert_that(default_plugin.plugin_config, h.empty())


def test_option_with_default_values():
    result = option(str)

    h.assert_that(result, h.instance_of(PluginOption))
    h.assert_that(result.command_line, h.none())
    h.assert_that(result.type, h.equal_to(str))
    h.assert_that(result._default_from, h.none())
    h.assert_that(result._env_var, h.none())
    h.assert_that(result._hook, h.none())
    h.assert_that(result._name, h.none())
    h.assert_that(result._plugin_config_key, h.none())
    h.assert_that(result._required, h.equal_to(False))
    h.assert_that(result._strict, h.equal_to(True))
