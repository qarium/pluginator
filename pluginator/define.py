import typing as t

from .pytest import (
    BasePlugin,
    PluginMeta,
    CommandLine,
    PluginOption,
    BasePluginMeta,
)
from .actions import Action


def plugin(name: str, /, *,
           config: t.Optional[str] = None,
           default_config: t.Optional[dict] = None,
           deps: t.Optional[list[str]] = None,
           actions: t.Optional[list[Action]] = None):
    """
    Decorator for creating a plugin class.

    Args:
        name: plugin name.
        config: yaml config file path.
        deps: list of dependencies names.
        default_config: configuration by default.
        actions: list of actions.

    Returns:
        Decorator function that returns new plugin class.
    """
    def wrapper(cls: type) -> type[BasePlugin]:
        meta = PluginMeta(name=name,
                          actions=actions,
                          config_file=config,
                          default_config=default_config,
                          dependencies=deps)
        bases = (cls,) if BasePlugin in cls.__mro__ else (cls, BasePlugin)

        return BasePluginMeta(cls.__name__, bases, {'__meta__': meta})

    return wrapper


def option(opt_type: type, /, *,
           strict: bool = True,
           nullable: bool = False,
           required: bool = False,
           env_var: t.Optional[str] = None,
           default_from: t.Optional[str] = None,
           plugin_config_key: t.Optional[str] = None,
           command_line: t.Optional[CommandLine] = None,
           hook: t.Optional[t.Callable[[t.Any], t.Any]] = None) -> PluginOption:
    """
    Create a plugin option.

    Args:
        opt_type: option type.
        strict: strict type for type casting.
        nullable: if set True value can be None
        required: flag for required option.
        env_var: environment variable name.
        default_from: name of plugin class property for getting default value.
        plugin_config_key: name of plugin config key for getting value.
        command_line: command line object.
        hook: hook function for prepare option value.

    Returns:
        New plugin option object.
    """
    return PluginOption(opt_type,
                        hook=hook,
                        strict=strict,
                        env_var=env_var,
                        nullable=nullable,
                        required=required,
                        command_line=command_line,
                        default_from=default_from,
                        plugin_config_key=plugin_config_key)
