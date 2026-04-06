# pylint: disable = W0212
from unittest.mock import call

import hamcrest as h
import pytest

from pluginator.pytest import CommandLine, PluginMeta, PLUGINATOR_OPTIONS_ATTRIBUTE, install_pytest_plugins


@pytest.mark.parametrize(
    'expected_args, expected_kwargs, expected_opt', (
            ('test-arg', {'action': 'store', 'help': 'test command'}, '--test-option',),
    )
)
def test_command_line(command_line, expected_args, expected_kwargs, expected_opt):
    h.assert_that(command_line.args, h.has_item(expected_args))
    h.assert_that(command_line.kwargs, h.has_entries(expected_kwargs))
    h.assert_that(command_line.opt, h.equal_to(expected_opt))


def test_command_line_register_once(mocker, command_line):
    mock_parser = mocker.Mock()
    mock_setattr = mocker.patch('pluginator.pytest.setattr')

    command_line.register_once(str, mock_parser)

    h.assert_that(
        mock_parser.mock_calls,
        h.equal_to([call.addoption(
            command_line.opt,
            *command_line.args,
            action=command_line.kwargs['action'],
            help=command_line.kwargs['help'],
            type=type(str())
        )])
    )

    mock_setattr.assert_called_once()
    h.assert_that(mock_setattr.call_args.args[1], h.equal_to(PLUGINATOR_OPTIONS_ATTRIBUTE))
    h.assert_that(mock_setattr.call_args.args[2], h.equal_to([command_line.opt]))


@pytest.mark.parametrize(
    'expected_default_from, expected_env_var, expected_plugin_config_key', (('test-default', 'test', 'test-key',),)
)
def test_plugin_option(plugin_option, command_line, expected_default_from, expected_env_var,
                       expected_plugin_config_key):
    h.assert_that(plugin_option.command_line, h.all_of(h.instance_of(CommandLine), h.equal_to(command_line)))
    h.assert_that(plugin_option.type, h.equal_to(int))
    h.assert_that(plugin_option._default_from, h.equal_to(expected_default_from))
    h.assert_that(plugin_option._env_var, expected_env_var)
    h.assert_that(plugin_option._name, h.none())
    h.assert_that(plugin_option._plugin_config_key, h.equal_to(expected_plugin_config_key))
    h.assert_that(plugin_option._required, h.equal_to(True))
    h.assert_that(plugin_option._strict, h.equal_to(False))


def test_plugin_option_init_command_line(mocker, plugin_option):
    mock_parser = mocker.Mock()

    plugin_option.init_command_line(mock_parser)

    mock_parser.addoption.assert_called_once()


@pytest.mark.parametrize(
    'expected_repr, expected_meta_name, expected_dependencies', (
            ('<Test: test-config>', 'test-config', ['test-dep1', 'test-dep2'],),
    )
)
def test_base_plugin(custom_plugin, config_file, expected_repr, expected_meta_name, expected_dependencies):
    custom_plugin = custom_plugin()
    meta = custom_plugin.meta

    h.assert_that(repr(custom_plugin), h.equal_to(expected_repr))
    h.assert_that(meta, h.instance_of(PluginMeta))
    h.assert_that(meta.name, h.equal_to(expected_meta_name))
    h.assert_that(meta.default_config, h.none())
    h.assert_that(meta.config_file, h.contains_string(config_file.filepath))
    h.assert_that(meta.dependencies, h.equal_to(expected_dependencies))
    h.assert_that(custom_plugin.name, h.contains_string(config_file.expected_value))
    h.assert_that(custom_plugin.plugin_config, h.has_entry(h.equal_to('name'), h.equal_to(custom_plugin.name)))


def test_base_plugin_without_pytest_and_plugin_configs(default_plugin):
    default_plugin = default_plugin()

    h.assert_that(default_plugin.plugin_config, h.empty())
    h.assert_that(
        h.calling(lambda: default_plugin.pytest_config),
        h.raises(AssertionError, matching=h.has_string(
            h.string_contains_in_order(f'Config is not initialized yet in "{default_plugin.__class__.__name__}"')
        ))
    )


def test_base_plugin_init_plugin_options(mocker, custom_plugin):
    mock_parser = mocker.Mock()
    custom_plugin = custom_plugin()

    custom_plugin.init_plugin_options(mock_parser)

    h.assert_that(mock_parser.mock_calls, h.equal_to([call.getgroup(custom_plugin.meta.name)]))


def test_base_plugin_install_with_pytest_config(mocker, custom_plugin):
    mock_config = mocker.Mock()
    custom_plugin = custom_plugin()

    custom_plugin.init_pytest_config(mock_config)
    custom_plugin.install()

    mock_calls = list(map(str, mock_config.mock_calls))
    mock_config.add_cleanup.assert_called_once()
    h.assert_that(mock_calls[0], h.starts_with(f"call.pluginmanager.register({custom_plugin},"
                                               f" name='{custom_plugin.meta.name}')"))
    h.assert_that(mock_calls[1], h.starts_with('call.add_cleanup(<function BasePlugin.install.'))


def test_base_plugin_install_without_pytest_config(custom_plugin):
    custom_plugin = custom_plugin()

    h.assert_that(
        h.calling(custom_plugin.install),
        h.raises(AssertionError, matching=h.has_string(
            h.string_contains_in_order(f'Plugin "{custom_plugin.__class__.__name__}" is not ready to install,'
                                       f' please call to "init_options" and "init_config" before that')
        ))
    )


def test_install_pytest_plugins(custom_plugin):
    context = {}

    install_pytest_plugins(custom_plugin, context=context)

    h.assert_that(context, h.has_key('pytest_addoption'))
    h.assert_that(context, h.has_key('pytest_configure'))
    h.assert_that(context, h.has_key('pytest_collection_finish'))
