# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2016-2017 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

import attr
import itertools

from PyQt5.QtWidgets import QWidget, QGridLayout
from qutebrowser.browser import browserpane
from qutebrowser.utils import objreg


tab_id_gen = itertools.count(0)


class Tab(QWidget):
    """A browser tab. Contains one or more panes."""

    def __init__(self, win_id, tabbedbrowser, private, parent=None):
        super().__init__(parent)
        self.win_id = win_id
        self.private = private
        self.data = TabData()
        self.tabbedbrowser = tabbedbrowser
        self.tab_id = next(tab_id_gen)

        self.registry = objreg.ObjectRegistry()
        tab_registry = objreg.get('tab-registry', scope='window',
                                  window=win_id)
        tab_registry[self.tab_id] = self
        objreg.register('tab', self, registry=self.registry)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.active_pane = self._create_pane()
        layout.addWidget(self.active_pane, 0, 0, 1, 1)
        self.setLayout(layout)

    def _create_pane(self):
        pane = browserpane.create(self.win_id, self, self.private, parent=self)
        self.tabbedbrowser.connect_pane_signals(self, pane)
        return pane

    def get_panes(self):
        return [self.active_pane]

    def close_pane(self, pane, crashed=False):
        self.layout().removeWidget(pane)
        pane.shutdown()
        if not crashed:
            # WORKAROUND for a segfault when we delete the crashed tab.
            # see https://bugreports.qt.io/browse/QTBUG-58698
            pane.layout().unwrap()
            pane.deleteLater()


@attr.s
class TabData:
    """A simple namespace with a fixed set of attributes.

    Attributes:
        keep_icon: Whether the (e.g. cloned) icon should not be cleared on page
                   load.
        pinned: Flag to pin the tab.
    """

    keep_icon = attr.ib(False)
    pinned = attr.ib(False)
