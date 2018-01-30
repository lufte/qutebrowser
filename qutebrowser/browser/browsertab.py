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

from PyQt5.QtWidgets import QWidget, QGridLayout
from qutebrowser.browser import browserpane


class Tab(QWidget):

    """A browser tab. Contains one or more panes."""

    def __init__(self, win_id, private, parent=None):
        super().__init__(parent)
        self.data = TabData()

        layout = QGridLayout()
        self.active_pane = browserpane.create(win_id, private)
        layout.addWidget(self.active_pane, 0, 0, 1, 1)
        self.setLayout(layout)

    def shutdown(self):
        self.active_pane.shutdown()


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
