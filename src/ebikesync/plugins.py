import logging
import importlib

"""
Plugin Factory for input and output plugins
"""


class InputPlugin:
    total_altitude: int = 0
    total_distance: int = 0


class OutputPlugin:
    pass


input_plugins: dict[str, InputPlugin] = {}
output_plugins: dict[str, OutputPlugin] = {}


def load_plugin(plugin_name: str) -> None:
    """Loads the plugins defined in the plugins list."""
    try:
        plugin = importlib.import_module(f"ebikesync.{plugin_name}")
        plugin.register(plugin_name)
    except ModuleNotFoundError:
        logging.error(f"Error loading plugin {plugin_name}, could not load the module.")
    except AttributeError:
        logging.error(f"Error loading plugin {plugin_name}, no register function found.")


def register_input(plugin_name: str, plugin_class) -> None:
    """Register a new game character type."""
    input_plugins[plugin_name] = plugin_class
    logging.info(f"Added {plugin_name} to the input plugins.")


def register_output(plugin_name: str, plugin_class) -> None:
    """Register a new game character type."""
    output_plugins[plugin_name] = plugin_class
    logging.info(f"Added {plugin_name} to the output plugins.")
