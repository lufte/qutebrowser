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

from PyQt5.QtWidgets import QWidget
from qutebrowser.browser import browserpane
from qutebrowser.utils import objreg
from qutebrowser.utils.tilinglayout import QTilingLayout


tab_id_gen = itertools.count(0)


class Tab(QWidget):
    """A browser tab. Contains one or more panes."""

    _INACTIVE_PANE_STYLE = '#pane { border: 1px solid transparent; }'
    _ACTIVE_PANE_STYLE = '#pane { border: 1px solid green; }'

    def __init__(self, win_id, tabbedbrowser, private, parent=None):
        super().__init__(parent)
        self.win_id = win_id
        self.private = private
        self.data = TabData()
        self.tabbedbrowser = tabbedbrowser
        self.tab_id = next(tab_id_gen)

        self.active_pane = self._create_pane()
        layout = QTilingLayout(self.active_pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.active_pane, 0, 0, 1, 1)
        self.setLayout(layout)

    def _create_pane(self):
        pane = browserpane.create(self.win_id, self, self.private, parent=self)
        self.tabbedbrowser.connect_pane_signals(self, pane)
        return pane

    def get_panes(self):
        return [self.active_pane]

    def close_pane(self, pane, crashed=False):
        if len(self.get_panes()) > 1:
            self.layout().remove_widget(pane)
        pane.shutdown()
        if not crashed:
            # WORKAROUND for a segfault when we delete the crashed tab.
            # see https://bugreports.qt.io/browse/QTBUG-58698
            pane.layout().unwrap()
            pane.deleteLater()

    def split(self, horizontal):
        old_pane = self.active_pane
        self._change_active_pane(self._create_pane())
        active_pane_url = self.active_pane.url()
        self.active_pane.openurl(active_pane_url)
        if horizontal:
            self.layout().hsplit(old_pane, self.active_pane)
        else:
            self.layout().vsplit(old_pane, self.active_pane)

    def _change_active_pane(self, new_active_pane):
        self.active_pane.setStyleSheet(self._INACTIVE_PANE_STYLE)
        new_active_pane.setStyleSheet(self._ACTIVE_PANE_STYLE)
        self.active_pane = new_active_pane



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
