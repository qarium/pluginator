# pylint: disable = W0212
from unittest.mock import call

import hamcrest as h
import pytest

from pluginator import define
from pluginator.actions import Action, ActionContext
from pluginator.pytest import (
    PLUGINATOR_OPTIONS_ATTRIBUTE,
    CommandLine,
    PluginMeta,
    PluginOption,
    install_pytest_plugins,
)
from tests.conftest import meta_decorator


@pytest.mark.parametrize(
    "expected_args, expected_kwargs, expected_opt",
    (
        (
            "test-arg",
            {"action": "store", "help": "test command"},
            "--test-option",
        ),
    ),
)
def test_command_line(command_line, expected_args, expected_kwargs, expected_opt):
    h.assert_that(command_line.args, h.has_item(expected_args))
    h.assert_that(command_line.kwargs, h.has_entries(expected_kwargs))
    h.assert_that(command_line.opt, h.equal_to(expected_opt))


def test_command_line_register_once(mocker, command_line):
    mock_parser = mocker.Mock()
    mock_setattr = mocker.patch("pluginator.pytest.setattr")

    command_line.register_once(str, mock_parser)

    h.assert_that(
        mock_parser.mock_calls,
        h.equal_to(
            [
                call.addoption(
                    command_line.opt,
                    *command_line.args,
                    action=command_line.kwargs["action"],
                    help=command_line.kwargs["help"],
                    type=str,
                )
            ]
        ),
    )

    mock_setattr.assert_called_once()
    h.assert_that(mock_setattr.call_args.args[1], h.equal_to(PLUGINATOR_OPTIONS_ATTRIBUTE))
    h.assert_that(mock_setattr.call_args.args[2], h.equal_to([command_line.opt]))


@pytest.mark.parametrize(
    "expected_default_from, expected_env_var, expected_plugin_config_key",
    (
        (
            "test-default",
            "test",
            "test-key",
        ),
    ),
)
def test_plugin_option(
    plugin_option, command_line, expected_default_from, expected_env_var, expected_plugin_config_key
):
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
    "expected_repr, expected_meta_name, expected_dependencies",
    (
        (
            "<Test: test-config>",
            "test-config",
            ["test-dep1", "test-dep2"],
        ),
    ),
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
    h.assert_that(custom_plugin.plugin_config, h.has_entry(h.equal_to("name"), h.equal_to(custom_plugin.name)))


def test_base_plugin_without_pytest_and_plugin_configs(default_plugin):
    default_plugin = default_plugin()

    h.assert_that(default_plugin.plugin_config, h.empty())
    h.assert_that(
        h.calling(lambda: default_plugin.pytest_config),
        h.raises(
            AssertionError,
            matching=h.has_string(
                h.string_contains_in_order(f'Config is not initialized yet in "{default_plugin.__class__.__name__}"')
            ),
        ),
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
    h.assert_that(
        mock_calls[0], h.starts_with(f"call.pluginmanager.register({custom_plugin}, name='{custom_plugin.meta.name}')")
    )
    h.assert_that(mock_calls[1], h.starts_with("call.add_cleanup(<function BasePlugin.install."))


def test_base_plugin_install_without_pytest_config(custom_plugin):
    custom_plugin = custom_plugin()

    h.assert_that(
        h.calling(custom_plugin.install),
        h.raises(
            AssertionError,
            matching=h.has_string(
                h.string_contains_in_order(
                    f'Plugin "{custom_plugin.__class__.__name__}" is not ready to install,'
                    f' please call to "init_options" and "init_config" before that'
                )
            ),
        ),
    )


def test_install_pytest_plugins(custom_plugin):
    context = {}

    install_pytest_plugins(custom_plugin, context=context)

    h.assert_that(context, h.has_key("pytest_addoption"))
    h.assert_that(context, h.has_key("pytest_configure"))
    h.assert_that(context, h.has_key("pytest_collection_finish"))


# ============================================================
# Additional tests for pluginator/pytest.py coverage
# ============================================================


# --- CommandLine ---


def test_command_line_register_with_group(mocker):
    """register_once should call parser.getgroup when group kwarg present."""
    mock_parser = mocker.Mock()
    mock_group = mocker.Mock()
    mock_parser.getgroup.return_value = mock_group
    mocker.patch("pluginator.pytest.setattr")

    cmd = CommandLine("--opt", group="my-group", action="store")
    cmd.register_once(str, mock_parser)

    mock_parser.getgroup.assert_called_once_with("my-group")
    mock_group.addoption.assert_called_once()


@pytest.mark.parametrize("excluded_type", [list, tuple, set, frozenset])
def test_command_line_register_excluded_type(mocker, excluded_type):
    """Excluded types should not add 'type' kwarg to addoption."""
    mock_parser = mocker.Mock()
    mocker.patch("pluginator.pytest.setattr")

    cmd = CommandLine("--opt", action="store")
    cmd.register_once(excluded_type, mock_parser)

    call_kwargs = mock_parser.addoption.call_args[1]
    h.assert_that(call_kwargs, h.is_not(h.has_entry("type", h.anything())))


# --- PluginOption value resolution ---


def test_plugin_option_get_from_env_var(mocker, monkeypatch):
    """PluginOption should resolve value from env var."""
    monkeypatch.setenv("TEST_PLUGIN_OPT_ENV", "42")

    opt = PluginOption(int, env_var="TEST_PLUGIN_OPT_ENV", strict=True)
    opt.__set_name__(None, "test_opt")

    mock_instance = mocker.Mock()
    mock_instance.plugin_config = {}

    result = opt.__get__(mock_instance, type(mock_instance))
    h.assert_that(result, h.equal_to(42))


def test_plugin_option_get_from_command_line(mocker):
    """PluginOption should resolve value from command line option."""
    mock_config = mocker.Mock()
    mock_config.getoption.return_value = "99"

    cmd = CommandLine("--my-opt", action="store")
    opt = PluginOption(int, command_line=cmd, strict=True)
    opt.__set_name__(None, "test_opt")

    mock_instance = mocker.Mock()
    mock_instance.plugin_config = {}
    mock_instance.pytest_config = mock_config

    result = opt.__get__(mock_instance, type(mock_instance))
    h.assert_that(result, h.equal_to(99))


def test_plugin_option_get_from_default_from(mocker):
    """PluginOption should resolve value from default_from attribute."""
    opt = PluginOption(str, default_from="my_default", strict=True)
    opt.__set_name__(None, "test_opt")

    mock_instance = mocker.Mock()
    mock_instance.plugin_config = {}
    mock_instance.my_default = "fallback"

    result = opt.__get__(mock_instance, type(mock_instance))
    h.assert_that(result, h.equal_to("fallback"))


def test_plugin_option_required_raises(mocker):
    """PluginOption should raise ValueError for required option with no value."""
    opt = PluginOption(str, required=True)
    opt.__set_name__(None, "missing_opt")

    mock_instance = mocker.Mock()
    mock_instance.__class__ = type("MockCls", (), {})
    mock_instance.plugin_config = {}
    mock_instance.pytest_config = mocker.Mock()
    mock_instance.pytest_config.getoption.return_value = None

    h.assert_that(
        h.calling(lambda: opt.__get__(mock_instance, type(mock_instance))),
        h.raises(ValueError, matching=h.has_string(h.contains_string("missing_opt"))),
    )


def test_plugin_option_nullable_returns_none(mocker):
    """PluginOption should return None for nullable option with no value."""
    opt = PluginOption(str, nullable=True, strict=True)
    opt.__set_name__(None, "test_opt")

    mock_instance = mocker.Mock()
    mock_instance.plugin_config = {}
    mock_instance.pytest_config = mocker.Mock()
    mock_instance.pytest_config.getoption.return_value = None

    result = opt.__get__(mock_instance, type(mock_instance))
    h.assert_that(result, h.none())


# --- PluginOption _prepare_value ---


def test_plugin_option_prepare_value_with_hook_strict(mocker):
    """_prepare_value with hook and strict should apply type cast to hook result."""
    hook = mocker.Mock(return_value="42")

    opt = PluginOption(int, hook=hook, strict=True)
    result = opt._prepare_value("input")

    hook.assert_called_once_with("input")
    h.assert_that(result, h.equal_to(42))


def test_plugin_option_prepare_value_with_hook_non_strict(mocker):
    """_prepare_value with hook and non-strict should return hook result directly."""
    hook = mocker.Mock(return_value="raw_value")

    opt = PluginOption(int, hook=hook, strict=False)
    result = opt._prepare_value("input")

    hook.assert_called_once_with("input")
    h.assert_that(result, h.equal_to("raw_value"))


def test_plugin_option_prepare_value_no_hook_strict():
    """_prepare_value without hook and strict should apply type cast."""
    opt = PluginOption(int, strict=True)
    result = opt._prepare_value("7")
    h.assert_that(result, h.equal_to(7))


def test_plugin_option_prepare_value_no_hook_non_strict():
    """_prepare_value without hook and non-strict should return value as-is."""
    opt = PluginOption(int, strict=False)
    result = opt._prepare_value("unchanged")
    h.assert_that(result, h.equal_to("unchanged"))


# --- BasePluginMeta ---


def test_base_plugin_meta_wraps_pytest_addoption():
    """BasePluginMeta should wrap pytest_addoption with called_once."""
    call_count = 0

    @define.plugin("addoption-test")
    @meta_decorator(PluginMeta)
    class TestPlugin:
        def pytest_addoption(self, parser):
            nonlocal call_count
            call_count += 1

    plugin = TestPlugin()
    plugin.pytest_addoption(None)
    plugin.pytest_addoption(None)

    h.assert_that(call_count, h.equal_to(1))


# --- BasePlugin actions ---


def test_base_plugin_with_actions(mocker):
    """BasePlugin.__init__ should configure actions from meta."""
    mock_action = mocker.Mock(spec=Action)
    mock_action.name = "test-action"

    @define.plugin("action-test", actions=[mock_action])
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    TestPlugin()
    mock_action.configure.assert_called_once()


def test_base_plugin_action_eager(mocker):
    """BasePlugin.action with lazy=False should call _actions directly."""

    @define.plugin("eager-test")
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    plugin._actions = mocker.Mock(return_value="eager_result")

    ctx = ActionContext()
    result = plugin.action("test", ctx, lazy=False)

    plugin._actions.assert_called_once_with("test", ctx)
    h.assert_that(result, h.equal_to("eager_result"))


def test_base_plugin_action_lazy(mocker):
    """BasePlugin.action with lazy=True should return wrapper."""

    @define.plugin("lazy-test")
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    plugin._actions = mocker.Mock(return_value="lazy_result")

    ctx = ActionContext()
    wrapper = plugin.action("test", ctx, lazy=True)

    assert callable(wrapper)
    result = wrapper()

    # lazy mode uses deepcopy of context, so check name and type only
    call_args = plugin._actions.call_args
    h.assert_that(call_args[0][0], h.equal_to("test"))
    h.assert_that(call_args[0][1], h.instance_of(ActionContext))
    h.assert_that(result, h.equal_to("lazy_result"))


def test_base_plugin_action_lazy_with_kwargs(mocker):
    """BasePlugin.action lazy wrapper should update context with kwargs."""

    @define.plugin("lazy-kwargs-test")
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    plugin._actions = mocker.Mock(return_value="ok")

    ctx = ActionContext()
    wrapper = plugin.action("test", ctx, lazy=True)
    wrapper()

    call_args = plugin._actions.call_args
    h.assert_that(call_args[0][0], h.equal_to("test"))


# --- BasePlugin plugin_config edge cases ---


def test_plugin_config_file_not_found():
    """plugin_config should return default_config when file does not exist."""

    @define.plugin("config-missing-test", config="/nonexistent/config.yml", default_config={"k": "v"})
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    h.assert_that(plugin.plugin_config, h.equal_to({"k": "v"}))


def test_plugin_config_invalid_yaml(tmp_path):
    """plugin_config should return default_config when yaml does not return dict."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("- item1\n- item2\n")

    @define.plugin("yaml-test", config=str(config_file), default_config={"default": True})
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    h.assert_that(plugin.plugin_config, h.equal_to({"default": True}))


# --- install_pytest_plugins callbacks ---


def test_install_pytest_plugins_addoption_callback(mocker, custom_plugin):
    """pytest_addoption callback should init plugin options."""
    mock_parser = mocker.Mock()
    plugin = custom_plugin()
    plugin.init_plugin_options = mocker.Mock()

    context = {}
    install_pytest_plugins(plugin, context=context)
    context["pytest_addoption"](mock_parser)

    plugin.init_plugin_options.assert_called_once_with(mock_parser)


def test_install_pytest_plugins_configure_callback(mocker, custom_plugin):
    """pytest_configure callback should init config and install plugin."""
    mock_config = mocker.Mock()
    plugin = custom_plugin()
    plugin.init_pytest_config = mocker.Mock()
    plugin.install = mocker.Mock()

    context = {}
    install_pytest_plugins(plugin, context=context)
    context["pytest_configure"](mock_config)

    plugin.init_pytest_config.assert_called_once_with(mock_config)
    plugin.install.assert_called_once()


def test_install_pytest_plugins_configure_with_configure_callback(mocker):
    """pytest_configure callback should call plugin.configure() if it exists."""

    @define.plugin("configure-cb-test")
    @meta_decorator(PluginMeta)
    class TestPlugin:
        configured = False

        def configure(self):
            self.configured = True

    mock_config = mocker.Mock()
    plugin = TestPlugin()
    plugin.install = mocker.Mock()

    context = {}
    install_pytest_plugins(plugin, context=context)
    context["pytest_configure"](mock_config)

    h.assert_that(plugin.configured, h.equal_to(True))


def test_install_pytest_plugins_collection_deps_ok(mocker):
    """pytest_collection_finish should pass when deps are satisfied."""

    @define.plugin("deps-ok-test", deps=["some-dep"])
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    mock_session = mocker.Mock()
    mock_session.config.pluginmanager.get_plugin.return_value = True

    context = {}
    install_pytest_plugins(plugin, context=context, check_deps=True)
    context["pytest_collection_finish"](mock_session)


def test_install_pytest_plugins_collection_deps_missing(mocker):
    """pytest_collection_finish should raise when deps are not installed."""

    @define.plugin("deps-missing-test", deps=["missing-dep"])
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    mock_session = mocker.Mock()
    mock_session.config.pluginmanager.get_plugin.return_value = None

    context = {}
    install_pytest_plugins(plugin, context=context, check_deps=True)

    h.assert_that(h.calling(lambda: context["pytest_collection_finish"](mock_session)), h.raises(AssertionError))


def test_install_pytest_plugins_no_deps_check(mocker):
    """pytest_collection_finish should skip dep check when check_deps=False."""

    @define.plugin("no-deps-test", deps=["missing-dep"])
    @meta_decorator(PluginMeta)
    class TestPlugin:
        pass

    plugin = TestPlugin()
    mock_session = mocker.Mock()

    context = {}
    install_pytest_plugins(plugin, context=context, check_deps=False)
    context["pytest_collection_finish"](mock_session)
