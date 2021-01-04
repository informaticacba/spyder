# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © Spyder Project Contributors
#
# Licensed under the terms of the MIT License
# ----------------------------------------------------------------------------

"""
Testing utilities to be used with pytest.
"""

from collections import OrderedDict
import traceback
import types

from unittest.mock import Mock, MagicMock

# Third party imports
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QMainWindow
import pytest

# Local imports
from spyder.config.manager import CONF
from spyder.plugins.preferences.api import PreferencePages
from spyder.plugins.preferences.plugin import Preferences
from spyder.plugins.shortcuts.widgets.table import load_shortcuts_data
from spyder.utils import icon_manager as ima


class MainWindowMock(QMainWindow):
    register_shortcut = Mock()

    def __init__(self):
        super().__init__(None)
        self.default_style = None
        self.widgetlist = []
        self.thirdparty_plugins = []
        self.shortcut_data = []
        self.prefs_dialog_instance = None
        self._PLUGINS = OrderedDict()
        self._EXTERNAL_PLUGINS = OrderedDict()
        self._INTERNAL_PLUGINS = OrderedDict()
        self._APPLICATION_TOOLBARS = MagicMock()

        self.console = Mock()
        self.preferences = Preferences(self, CONF)
        self.register_plugin(self.preferences)

        # Load shortcuts for tests
        for context, name, __ in CONF.iter_shortcuts():
            self.shortcut_data.append((None, context, name, None, None))

        for attr in ['mem_status', 'cpu_status']:
            mock_attr = Mock()
            setattr(mock_attr, 'toolTip', lambda: '')
            setattr(mock_attr, 'setToolTip', lambda x: '')
            setattr(mock_attr, 'is_supported', lambda: True)
            setattr(mock_attr, 'prefs_dialog_instance', lambda: '')
            setattr(self, attr, mock_attr)

    def register_plugin(self, plugin, external=False):
        plugin._register()
        plugin.register()
        self.add_plugin(plugin, external=external)

    def add_plugin(self, plugin, external=False):
        self._PLUGINS[plugin.CONF_SECTION] = plugin
        if external:
            self._EXTERNAL_PLUGINS[plugin.CONF_SECTION] = plugin
        else:
            self._INTERNAL_PLUGINS[plugin.CONF_SECTION] = plugin

    def set_prefs_size(self, size):
        pass

    def reset_spyder(self):
        pass


class ConfigDialogTester:
    def __init__(self, params):
        main_class, general_config_plugins, plugins = params
        self._main = main_class() if main_class else None
        if self._main is None:
            self._main = MainWindowMock()

        def set_prefs_size(self, size):
            pass

        def reset_spyder(self):
            pass

        def register_plugin(self, plugin, external=False):
            plugin._register()
            plugin.register()
            self.add_plugin(plugin, external=external)

        def add_plugin(self, plugin, external=False):
            self._PLUGINS[plugin.CONF_SECTION] = plugin
            if external:
                self._EXTERNAL_PLUGINS[plugin.CONF_SECTION] = plugin
            else:
                self._INTERNAL_PLUGINS[plugin.CONF_SECTION] = plugin

        setattr(self._main, '_PLUGINS', OrderedDict())
        setattr(self._main, '_EXTERNAL_PLUGINS', OrderedDict())
        setattr(self._main, '_INTERNAL_PLUGINS', OrderedDict())
        setattr(self._main, 'register_plugin',
                types.MethodType(register_plugin, self._main))
        setattr(self._main, 'add_plugin',
                types.MethodType(add_plugin, self._main))
        setattr(self._main, 'reset_spyder',
                types.MethodType(reset_spyder, self._main))
        setattr(self._main, 'set_prefs_size',
                types.MethodType(set_prefs_size, self._main))
        setattr(self._main, 'preferences', Preferences(self._main, CONF))
        self._main.register_plugin(self._main.preferences)

        if not general_config_plugins:
            self._main.preferences.config_pages.pop(PreferencePages.General)

        if plugins:
            for Plugin in plugins:
                if hasattr(Plugin, 'CONF_WIDGET_CLASS'):
                    for required in (Plugin.REQUIRES or []):
                        if required not in self._main._PLUGINS:
                            self._main._PLUGINS[required] = MagicMock()
                            self._main._INTERNAL_PLUGINS[
                                required] = MagicMock()

                    plugin = Plugin(self._main, CONF)
                    self._main.register_plugin(plugin)
                else:
                    plugin = Plugin(self._main)
                    self._main.preferences.register_plugin_preferences(plugin)


@pytest.fixture
def global_config_dialog(qtbot):
    """
    Fixture that includes the general preferences options.

    These options are the ones not tied to a specific plugin.
    """
    preferences = Preferences(MainWindowMock(), CONF)
    preferences.open_dialog(None)

    container = preferences.get_container()
    dlg = container.dialog
    qtbot.addWidget(dlg)
    dlg.show()
    return dlg


@pytest.fixture
def config_dialog(qtbot, request, mocker):
    mocker.patch.object(ima, 'icon', lambda x, icon_path=None: QIcon())
    main_ref = ConfigDialogTester(request.param)
    preferences = main_ref._main.preferences
    preferences.open_dialog(None)

    container = preferences.get_container()
    dlg = container.dialog
    qtbot.addWidget(dlg)
    dlg.show()
    return dlg
