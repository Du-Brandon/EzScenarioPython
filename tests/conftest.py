"""Load the plugin only when its installed entry point is unavailable."""

from importlib.metadata import entry_points


_PLUGIN = "ezspec.extension.pytest.plugin"
_INSTALLED_PLUGINS = {
    entry_point.value for entry_point in entry_points(group="pytest11")
}

pytest_plugins = [] if _PLUGIN in _INSTALLED_PLUGINS else [_PLUGIN]
