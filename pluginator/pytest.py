import os
import typing as t
from copy import deepcopy
from functools import cached_property
from dataclasses import dataclass, field

import yaml

from _pytest.main import Session
from _pytest.config import Config
from _pytest.config.argparsing import Parser, OptionGroup

from qools.funcutils import called_once

from .actions import (
    Action,
    ActionManager,
    ActionContext,
)
from .utils import call_context

PLUGINATOR_OPTIONS_ATTRIBUTE = '__pluginator_options__'
EXCLUDED_TYPES = (list, tuple, set, frozenset)


class CommandLine:
    """
    Define a command line settings for pytest.
    """

    def __init__(self, opt: str, /, *args, **kwargs):
        self.opt = opt

        self.args = args
        self.kwargs = kwargs

    def register_once(self,
                      opt_type: type,
                      parser: Parser, *,
                      group: t.Optional[OptionGroup] = None):
        """
        Register the option once in pytest option parser.

        Args:
            opt_type: The type of the option.
            parser: The option parser instance.
            group: The option group instance.
        """
        pluginator_options = getattr(parser, PLUGINATOR_OPTIONS_ATTRIBUTE, [])

        if self.opt not in pluginator_options:
            if 'group' in self.kwargs:
                group = parser.getgroup(self.kwargs.pop('group'))

            if 'type' not in self.kwargs and self.kwargs.get('action') not in ('store_true', 'store_false'):
                if opt_type not in EXCLUDED_TYPES:
                    self.kwargs['type'] = opt_type

            (group or parser).addoption(self.opt, *self.args, **self.kwargs)
            pluginator_options.append(self.opt)

        setattr(parser, PLUGINATOR_OPTIONS_ATTRIBUTE, pluginator_options)


class PluginOption:
    """
    A plugin option.
    """

    # pylint: disable=used-before-assignment
    def __init__(self, opt_type: type, /, *,
                 nullable: bool = False,
                 required: bool = False,
                 env_var: t.Optional[str] = None,
                 default_from: t.Optional[str] = None,
                 plugin_config_key: t.Optional[str] = None,
                 command_line: t.Optional[CommandLine] = None,
                 hook: t.Optional[t.Callable[[t.Any], t.Any]] = None,
                 strict: bool = True):
        self._type = opt_type

        self._env_var = env_var
        self._nullable = nullable
        self._required = required
        self._default_from = default_from
        self._command_line = command_line
        self._hook = hook
        self._plugin_config_key = plugin_config_key
        self._strict = strict

        self._name: t.Optional[str] = None

    @property
    def type(self):
        return self._type

    @property
    def command_line(self):
        return self._command_line

    def __set_name__(self, _, name: str):
        self._name = name

    def _prepare_value(self, value: t.Any) -> t.Any:
        if callable(self._hook):
            return self._type(self._hook(value)) if self._strict else self._hook(value)
        return self._type(value) if self._strict else value

    def __get__(self, instance: 'BasePlugin', _):
        if instance is None:
            return self

        if self._plugin_config_key is not None:
            plugin_config_value = instance.plugin_config.get(self._plugin_config_key, object)

            if plugin_config_value != object:
                return self._prepare_value(plugin_config_value)

        if self._env_var is not None:
            env_var_value = os.getenv(self._env_var)

            if env_var_value is not None:
                return self._prepare_value(env_var_value)

        if self._command_line is not None:
            cli_opt_value = instance.pytest_config.getoption(self._command_line.opt)

            if cli_opt_value is not None:
                return self._prepare_value(cli_opt_value)

        if self._default_from is not None:
            default_from_value = getattr(instance, self._default_from)

            if default_from_value is not None:
                return self._prepare_value(default_from_value)

        if self._required:
            raise ValueError(f'{instance.__class__}: option "{self._name}" is required')

        return None if self._nullable else self._type()

    def init_command_line(self,
                          parser: Parser, *,
                          group: t.Optional[OptionGroup] = None):
        """
        Init command line settings for the option.

        Args:
            parser: The option parser instance.
            group: The option group instance.
        """
        if self._command_line is not None:
            self._command_line.register_once(self._type, parser, group=group)


@dataclass
class PluginMeta:
    """
    Plugin meta information.
    """
    name: str
    actions: list[Action] = field(kw_only=True, default=None)
    config_file: t.Optional[str] = field(kw_only=True, default=None)
    default_config: t.Optional[dict] = field(kw_only=True, default=None)
    dependencies: t.Optional[t.Iterable[str]] = field(kw_only=True, default=None)


class BasePluginMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)

        if hasattr(cls, 'pytest_addoption'):
            cls.pytest_addoption = called_once(cls.pytest_addoption)

        return cls


class BasePlugin(metaclass=BasePluginMeta):
    """
    Base plugin class.
    """
    __meta__: PluginMeta

    def __init__(self):
        assert hasattr(self, '__meta__'), f'meta object does not defined for "{self.__class__.__name__}"'

        self.__pytest_config: t.Optional[Config] = None
        self._actions: ActionManager = ActionManager()

        if self.__meta__.actions is not None:
            for action in self.__meta__.actions:
                self._actions.add_action(action, self.plugin_config)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.meta.name}>'

    def action(self, name: str, context: ActionContext, *, lazy: bool = False):
        if lazy:
            def wrapper(**kwargs):
                ctx = deepcopy(context)
                ctx.update(**kwargs)
                return self._actions(name, ctx)

            return wrapper
        return self._actions(name, context)

    @property
    def meta(self) -> PluginMeta:
        return self.__meta__

    @property
    def pytest_config(self) -> Config:
        if not self.__pytest_config:
            raise AssertionError(
                f'Config is not initialized yet in "{self.__class__.__name__}"',
            )
        return self.__pytest_config

    @cached_property
    def plugin_config(self) -> dict:
        if self.meta.config_file is None:
            return {}

        default_config = self.meta.default_config or {}

        if not os.path.exists(self.meta.config_file):
            return default_config

        with open(self.meta.config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.full_load(f)

            if isinstance(config_data, dict):
                return default_config | config_data

            return default_config

    @property
    def plugin_options(self) -> t.Iterable[PluginOption]:
        for attr in dir(self.__class__):
            value = getattr(self.__class__, attr, None)

            if isinstance(value, PluginOption):
                yield value

    def init_plugin_options(self, parser: Parser) -> None:
        group = parser.getgroup(self.meta.name)

        for plugin_option in self.plugin_options:
            plugin_option.init_command_line(parser, group=group)

    def init_pytest_config(self, config: Config) -> None:
        self.__pytest_config = config

    def install(self):
        if not self.__pytest_config:
            raise AssertionError(
                f'Plugin "{self.__class__.__name__}" is not ready to install, '
                f'please call to "init_options" and "init_config" before that',
            )

        name = self.__pytest_config.pluginmanager.register(self, name=self.meta.name)
        self.__pytest_config.add_cleanup(lambda: self.__pytest_config.pluginmanager.unregister(name=name))


def install_pytest_plugins(*plugins,
                           check_deps: bool = True,  # TODO: remove flag for new minor version
                           context: t.Optional[dict[str, t.Any]] = None) -> None:
    """
    Install pytest plugins in context.

    Args:
        plugins: The plugins to install.
        check_deps: Check dependencies if True else no check.
        context: The context to install plugins in.
    """
    context = call_context() if context is None else context

    ctx_pytest_addoption = context.get('pytest_addoption', lambda parser: None)
    ctx_pytest_configure = context.get('pytest_configure', lambda config: None)
    ctx_pytest_collection_finish = context.get('pytest_collection_finish', lambda session: None)

    failed_deps = []
    plugin_name_to_failed_deps = {}

    def pytest_addoption(parser: Parser):
        ctx_pytest_addoption(parser)

        for plugin in plugins:
            plugin.init_plugin_options(parser)

    def pytest_configure(config: Config):
        ctx_pytest_configure(config)

        for plugin in plugins:
            plugin.init_pytest_config(config)
            plugin.install()

            configure_callback = getattr(plugin, 'configure', None)

            if configure_callback is not None:
                configure_callback()

    def pytest_collection_finish(session: Session):
        ctx_pytest_collection_finish(session)

        if check_deps:
            for plugin in plugins:
                for dep_name in plugin.__meta__.dependencies or []:
                    if not session.config.pluginmanager.get_plugin(dep_name):
                        failed_deps.append(dep_name)

                if failed_deps:
                    plugin_name_to_failed_deps[plugin.meta.name] = failed_deps

            if plugin_name_to_failed_deps:
                fails = plugin_name_to_failed_deps.items()
                message = 'Plugin "{}" needs "{}" dependencies, but does not installed'

                raise AssertionError(*map(lambda i: message.format(i[0], ', '.join(i[1])), fails))

    context['pytest_addoption'] = pytest_addoption
    context['pytest_configure'] = pytest_configure
    context['pytest_collection_finish'] = pytest_collection_finish


__all__ = [
    'BasePlugin',
    'PluginMeta',
    'CommandLine',
    'PluginOption',
    'BasePluginMeta',
    'install_pytest_plugins',
]
