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
import pdb

from PyQt5.QtWidgets import QWidget, QGridLayout
from qutebrowser.browser import browserpane


class Tab(QWidget):

    """A browser tab. Contains one or more panes."""

    def __init__(self, win_id, private, parent=None):
        super().__init__(parent)
        self._win_id = win_id
        self._private = private
        self.data = TabData()

        layout = QGridLayout()
        self.active_pane = browserpane.create(win_id, private)
        layout.addWidget(self.active_pane, 0, 0, 1, 1)
        self.setLayout(layout)

    def shutdown(self):
        self.active_pane.shutdown()

    def vsplit(self):
        active_pane_url = self.active_pane.url()
        active_pane_position = self.layout().getItemPosition(
            self.layout().indexOf(self.active_pane))
        self.active_pane = browserpane.create(self._win_id, self._private)
        self.layout().addWidget(self.active_pane, active_pane_position[0],
                                active_pane_position[1] + 1, 1, 1)
        self.active_pane.openurl(active_pane_url)

    def split(self):
        active_pane_url = self.active_pane.url()
        active_pane_position = self.layout().getItemPosition(
            self.layout().indexOf(self.active_pane))
        self.active_pane = browserpane.create(self._win_id, self._private)
        self.layout().addWidget(self.active_pane, active_pane_position[0] + 1,
                                active_pane_position[1], 1, 1)
        self.active_pane.openurl(active_pane_url)

    def _resize_panes(self):
        rows = range(self.layoyt().rowCount())
        columns = range(self.layoyt().columnCount())
        cells = ((i, j) for i in rows for j in columns)
        for cell in cells:
            pass

    def debug(self):
        pdb.set_trace()

    def _move_pane(self, horizontal, increment):
        count_ = (
            self.layout().columnCount()
            if horizontal else
            self.layout().rowCount()
        )
        curr_pos = self.layout().getItemPosition(
            self.layout().indexOf(self.active_pane))[:2]
        step = 1 if increment else -1
        new_pos = (
            (curr_pos[0], curr_pos[1] + step)
            if horizontal else
            (curr_pos[0] + step, curr_pos[1])
        )
        new_pane = self.active_pane
        while (
                0 <= (new_pos[1] if horizontal else new_pos[0]) < count_
                and new_pane is self.active_pane
        ):
            new_pane = self.layout().itemAtPosition(*new_pos).widget()
            new_pos = (
                (new_pos[0], new_pos[1] + step)
                if horizontal else
                (new_pos[0] + step, new_pos[1])
            )
        self.active_pane = new_pane

    def move_pane_up(self):
        self._move_pane(horizontal=False, increment=False)

    def move_pane_right(self):
        self._move_pane(horizontal=True, increment=True)

    def move_pane_down(self):
        self._move_pane(horizontal=False, increment=True)

    def move_pane_left(self):
        self._move_pane(horizontal=True, increment=False)



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
