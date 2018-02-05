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

from PyQt5.QtWidgets import QWidget, QGridLayout, QFrame
from qutebrowser.browser import browserpane


class Tab(QWidget):

    """A browser tab. Contains one or more panes."""

    _INACTIVE_PANE_STYLE = '#pane { border: 1px solid transparent; }'
    _ACTIVE_PANE_STYLE = '#pane { border: 1px solid green; }'

    def __init__(self, win_id, private, parent=None):
        super().__init__(parent)
        self._win_id = win_id
        self._private = private
        self.data = TabData()

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.active_pane = self._create_pane(win_id, private)
        self.active_pane.setFrameStyle(QFrame.Panel | QFrame.Plain)
        layout.addWidget(self.active_pane, 0, 0, 1, 1)
        self.setLayout(layout)

    @classmethod
    def _create_pane(cls, win_id, private):
        pane = browserpane.create(win_id, private)
        pane.setObjectName('pane')
        pane.setStyleSheet(cls._INACTIVE_PANE_STYLE)
        return pane

    def shutdown(self):
        self.active_pane.shutdown()

    def vsplit(self):
        self._split(False)

    def hsplit(self):
        self._split(True)

    def _split(self, horizontal):
        active_pane_url = self.active_pane.url()
        l = self.layout()  # just to make it shorter :)
        curr_pos = l.getItemPosition(l.indexOf(self.active_pane))
        offset = (curr_pos[0] if horizontal else curr_pos[1]) + 1
        end = l.rowCount() if horizontal else l.columnCount()
        panes_to_displace = []

        for index in range(offset, end):
            item = l.itemAtPosition(*(
                (index, curr_pos[1])
                if horizontal else
                (curr_pos[0], index)
            ))

            if not item:
                # should not be needed once I figure rowspans and colspans
                continue
            item_pos = (item.widget(),
                        l.getItemPosition(l.indexOf(item.widget())))
            if item_pos not in panes_to_displace:
                panes_to_displace.append(item_pos)

        for pane, old_pos in reversed(panes_to_displace):
            l.removeWidget(pane)
            l.addWidget(pane,
                        old_pos[0] + (1 if horizontal else 0),
                        old_pos[1] + (1 if not horizontal else 0),
                        old_pos[2], old_pos[3])

        self._change_active_pane(
            self._create_pane(self._win_id, self._private))
        self.layout().addWidget(self.active_pane,
                                curr_pos[0] + (1 if horizontal else 0),
                                curr_pos[1] + (1 if not horizontal else 0),
                                1, 1)
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
        self._change_active_pane(new_pane)

    def move_pane_up(self):
        self._move_pane(horizontal=False, increment=False)

    def move_pane_right(self):
        self._move_pane(horizontal=True, increment=True)

    def move_pane_down(self):
        self._move_pane(horizontal=False, increment=True)

    def move_pane_left(self):
        self._move_pane(horizontal=True, increment=False)

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
