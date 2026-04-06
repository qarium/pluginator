import typing as t
import importlib


class ActionContext:
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(
                    f'Action context:{self.__class__.__name__} not contain attribute:"{key}"',
                )
            setattr(self, key, value)

    def validate(self):
        pass


class Action:
    def __init__(self,
                 name: str,
                 module: str, *,
                 enable: bool = True,
                 default_config: t.Optional[dict] = None):
        self._name = name
        self._module = module
        self._enable = enable
        self._config = default_config or {}
        self._func = None
        self._setup = None

    def __call__(self, context: ActionContext) -> t.Any:
        if self._enable:
            context.validate()
            return self._func(config=self._config, context=context)
        return None

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enable

    @property
    def setup(self) -> t.Optional[t.Callable]:
        return self._setup

    @property
    def config(self) -> t.Optional[dict]:
        return self._config

    def configure(self, action_config: dict):
        if self._func:
            raise RuntimeError('Action already initialized')

        self._enable = action_config.get('enable', self._enable)
        module = action_config.get('module', self._module)

        self._config = {
            k: action_config.get('config', {}).get(k, v)
            for k, v in self._config.items()
        }

        try:
            self._module = importlib.import_module(module)
        except ImportError as e:
            raise ImportError(f'Failed to import module "{module}": {e}') from e

        func = getattr(self._module, 'main', None)
        if func is None:
            raise AttributeError(f'Module "{self._module}" does not define a "main" func attribute')

        if not isinstance(func, t.Callable):
            raise TypeError(f'"{func}" should be a callable object, not {type(func)}')

        self._func = func

        self._setup = getattr(self._module, 'setup', None)


class ActionManager:
    def __init__(self):
        self._actions: dict[str, Action] = {}

    def add_action(self,
                   action: Action,
                   plugin_config: t.Optional[dict] = None) -> None:
        if action.name in self._actions:
            raise RuntimeError('Plugin action already exist')

        action.configure(plugin_config.get('actions', {}).get(action.name, {}))
        if action.enabled and action.setup:
            action.setup(action.config)

        self._actions[action.name] = action

    def __call__(self, name: str, context: ActionContext) -> t.Any:
        if action := self._actions.get(name):
            return action(context)
        raise RuntimeError(f'Plugin action "{name}" not found')
