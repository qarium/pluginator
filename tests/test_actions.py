# pylint: disable = W0212
from unittest.mock import MagicMock

import hamcrest as h

from pluginator.actions import Action, ActionContext, ActionManager


class TestAction:
    """Tests for Action class."""

    def test_init_default_values(self):
        """Test Action initialization with default values."""
        action = Action("test_action", "test.module")

        h.assert_that(action._name, h.equal_to("test_action"))
        h.assert_that(action._module, h.equal_to("test.module"))
        h.assert_that(action._enable, h.equal_to(True))
        h.assert_that(action._config, h.equal_to({}))
        h.assert_that(action._func, h.none())

    def test_init_custom_values(self):
        """Test Action initialization with custom values."""
        action = Action("test_action", "test.module", enable=False, default_config={"key": "value"})

        h.assert_that(action._name, h.equal_to("test_action"))
        h.assert_that(action._module, h.equal_to("test.module"))
        h.assert_that(action._enable, h.equal_to(False))
        h.assert_that(action._config, h.equal_to({"key": "value"}))

    def test_name_property(self):
        """Test Action name property."""
        action = Action("my_action", "test.module")

        h.assert_that(action.name, h.equal_to("my_action"))

    def test_call_when_disabled(self, mocker):
        """Test Action call returns None when disabled."""
        action = Action("test_action", "test.module", enable=False)
        action._func = mocker.Mock(return_value="result")

        ctx = ActionContext()
        result = action(ctx)

        h.assert_that(result, h.none())
        h.assert_that(action._func.call_count, h.equal_to(0))

    def test_call_when_enabled(self, mocker):
        """Test Action call executes function when enabled."""
        mock_func = mocker.Mock(return_value="result")
        action = Action("test_action", "test.module", enable=True, default_config={"key": "value"})
        action._func = mock_func

        ctx = ActionContext()
        result = action(ctx)

        h.assert_that(result, h.equal_to("result"))
        mock_func.assert_called_once_with(config={"key": "value"}, context=ctx)

    def test_configure_success(self, mocker):
        """Test Action configure with successful module import."""
        mock_module = MagicMock()
        mock_func = mocker.Mock()
        mock_module.main = mock_func

        mock_import = mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        action = Action("test_action", "test.module", default_config={"key": "default"})
        action.configure(action_config={"enable": False, "module": "custom.module", "config": {"key": "custom"}})

        h.assert_that(action._enable, h.equal_to(False))
        h.assert_that(action._module, h.equal_to(mock_module))
        h.assert_that(action._config, h.equal_to({"key": "custom"}))
        mock_import.assert_called_once_with("custom.module")
        h.assert_that(action._func, h.equal_to(mock_func))

    def test_configure_without_action_config(self, mocker):
        """Test Action configure without action_config uses defaults."""
        mock_module = MagicMock()
        mock_func = mocker.Mock()
        mock_module.main = mock_func

        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        action = Action("test_action", "test.module", enable=True, default_config={"key": "default"})
        action.configure(action_config={})

        h.assert_that(action._enable, h.equal_to(True))
        h.assert_that(action._module, h.equal_to(mock_module))
        h.assert_that(action._config, h.equal_to({"key": "default"}))

    def test_configure_already_initialized_raises(self, mocker):
        """Test Action configure raises error if already initialized."""
        action = Action("test_action", "test.module")
        action._func = mocker.Mock()

        h.assert_that(
            h.calling(lambda: action.configure(action_config={})),
            h.raises(RuntimeError, matching=h.has_string(h.contains_string("Action already initialized"))),
        )

    def test_configure_import_error(self, mocker):
        """Test Action configure raises ImportError for missing module."""
        mocker.patch("pluginator.actions.importlib.import_module", side_effect=ImportError("No module"))

        action = Action("test_action", "nonexistent.module")

        h.assert_that(
            h.calling(lambda: action.configure(action_config={})),
            h.raises(ImportError, matching=h.has_string(h.contains_string("Failed to import module"))),
        )

    def test_configure_no_main_attribute(self, mocker):
        """Test Action configure raises AttributeError if no main function."""
        mock_module = MagicMock(spec=[])  # No 'main' attribute
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        action = Action("test_action", "test.module")

        h.assert_that(
            h.calling(lambda: action.configure(action_config={})),
            h.raises(AttributeError, matching=h.has_string(h.contains_string('does not define a "main" func'))),
        )

    def test_configure_main_not_callable(self, mocker):
        """Test Action configure raises TypeError if main is not callable."""
        mock_module = MagicMock()
        mock_module.main = "not a function"

        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        action = Action("test_action", "test.module")

        h.assert_that(
            h.calling(lambda: action.configure(action_config={})),
            h.raises(TypeError, matching=h.has_string(h.contains_string("should be a callable"))),
        )

    def test_configure_config_merge(self, mocker):
        """Test Action configure merges action config with default config."""
        mock_module = MagicMock()
        mock_module.main = mocker.Mock()
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        action = Action("test_action", "test.module", default_config={"key1": "default1", "key2": "default2"})
        action.configure(action_config={"config": {"key1": "custom1"}})

        h.assert_that(action._config, h.equal_to({"key1": "custom1", "key2": "default2"}))


class TestActionManager:
    """Tests for ActionManager class."""

    def test_init(self):
        """Test ActionManager initialization."""
        manager = ActionManager()

        h.assert_that(manager._actions, h.equal_to({}))

    def test_add_action_success(self, mocker):
        """Test ActionManager add_action adds action successfully."""
        mock_module = MagicMock()
        mock_module.main = mocker.Mock()
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        manager = ActionManager()
        action = Action("test_action", "test.module")
        plugin_config = {"actions": {"test_action": {"enable": True}}}

        manager.add_action(action, plugin_config=plugin_config)

        h.assert_that("test_action" in manager._actions, h.equal_to(True))
        h.assert_that(manager._actions["test_action"]._module, h.equal_to(mock_module))

    def test_add_action_with_default_config(self, mocker):
        """Test ActionManager add_action with default_config."""
        mock_module = MagicMock()
        mock_module.main = mocker.Mock()
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        manager = ActionManager()
        action = Action("test_action", "test.module", default_config={"key": "default"})
        plugin_config = {"actions": {"test_action": {"config": {"key": "value"}}}}

        manager.add_action(action, plugin_config=plugin_config)

        h.assert_that(manager._actions["test_action"]._config, h.equal_to({"key": "value"}))

    def test_add_action_already_exists_raises(self, mocker):
        """Test ActionManager add_action raises error if action exists."""
        mock_module = MagicMock()
        mock_module.main = mocker.Mock()
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        manager = ActionManager()
        action1 = Action("test_action", "test.module")
        action2 = Action("test_action", "another.module")
        plugin_config = {"actions": {}}

        manager.add_action(action1, plugin_config=plugin_config)

        h.assert_that(
            h.calling(lambda: manager.add_action(action2, plugin_config=plugin_config)),
            h.raises(RuntimeError, matching=h.has_string(h.contains_string("Plugin action already exist"))),
        )

    def test_call_action_success(self, mocker):
        """Test ActionManager call executes action."""
        mock_module = MagicMock()
        mock_func = mocker.Mock(return_value="action_result")
        mock_module.main = mock_func
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        manager = ActionManager()
        action = Action("test_action", "test.module")
        plugin_config = {"actions": {"test_action": {"enable": True}}}

        manager.add_action(action, plugin_config=plugin_config)

        ctx = ActionContext()
        result = manager("test_action", ctx)

        h.assert_that(result, h.equal_to("action_result"))
        mock_func.assert_called_once()

    def test_call_action_not_found_raises(self):
        """Test ActionManager call raises error for unknown action."""
        manager = ActionManager()
        ctx = ActionContext()

        h.assert_that(
            h.calling(lambda: manager("nonexistent", ctx)),
            h.raises(RuntimeError, matching=h.has_string(h.contains_string('Plugin action "nonexistent" not found'))),
        )

    def test_call_action_disabled_returns_none(self, mocker):
        """Test ActionManager call returns None for disabled action."""
        mock_module = MagicMock()
        mock_func = mocker.Mock(return_value="result")
        mock_module.main = mock_func
        mocker.patch("pluginator.actions.importlib.import_module", return_value=mock_module)

        manager = ActionManager()
        action = Action("test_action", "test.module", enable=True)
        plugin_config = {"actions": {"test_action": {"enable": False}}}

        manager.add_action(action, plugin_config=plugin_config)

        ctx = ActionContext()
        result = manager("test_action", ctx)

        h.assert_that(result, h.none())
        mock_func.assert_not_called()
