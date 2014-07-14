# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
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

"""The tab widget used for TabbedBrowser from browser.py."""

import functools

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QSize
from PyQt5.QtWidgets import (QTabWidget, QTabBar, QSizePolicy, QCommonStyle,
                             QStyle, QStylePainter, QStyleOptionTab)
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QColor

import qutebrowser.config.config as config
from qutebrowser.config.style import set_register_stylesheet
from qutebrowser.utils.qt import qt_ensure_valid


class EmptyTabIcon(QIcon):

    """An empty icon for a tab.

    Qt somehow cuts text off when padding is used for the tabbar, see
    https://bugreports.qt-project.org/browse/QTBUG-15203

    Until we find a better solution we use this hack of using a simple
    transparent icon to get some padding, because when a real favicon is set,
    the padding seems to be fine...
    """

    def __init__(self):
        pix = QPixmap(2, 16)
        pix.fill(Qt.transparent)
        super().__init__(pix)


class TabWidget(QTabWidget):

    """The tabwidget used for TabbedBrowser.

    Class attributes:
        STYLESHEET: The stylesheet template to be used.
    """

    STYLESHEET = """
        QTabWidget::pane {{
            position: absolute;
            top: 0px;
        }}

        QTabBar {{
            {font[tabbar]}
            {color[tab.bg.bar]}
        }}
    """

    def __init__(self, parent):
        super().__init__(parent)
        bar = TabBar()
        self.setTabBar(bar)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        set_register_stylesheet(self)
        self.setDocumentMode(True)
        self.setElideMode(Qt.ElideRight)
        bar.setDrawBase(False)
        self._init_config()

    def _init_config(self):
        """Initialize attributes based on the config."""
        position_conv = {
            'north': QTabWidget.North,
            'south': QTabWidget.South,
            'west': QTabWidget.West,
            'east': QTabWidget.East,
        }
        select_conv = {
            'left': QTabBar.SelectLeftTab,
            'right': QTabBar.SelectRightTab,
            'previous': QTabBar.SelectPreviousTab,
        }
        self.setMovable(config.get('tabbar', 'movable'))
        self.setTabsClosable(config.get('tabbar', 'close-buttons'))
        posstr = config.get('tabbar', 'position')
        selstr = config.get('tabbar', 'select-on-remove')
        self.setTabPosition(position_conv[posstr])
        self.tabBar().setSelectionBehaviorOnRemove(select_conv[selstr])

    @pyqtSlot(str, str)
    def on_config_changed(self, section, _option):
        """Update attributes when config changed."""
        if section == 'tabbar':
            self._init_config()


class TabBar(QTabBar):

    """Custom tabbar to close tabs on right click.

    Signals:
        tab_rightclicked: Emitted when a tab was right-clicked and should be
                          closed. We use this rather than tabCloseRequested
                          because tabCloseRequested is sometimes connected by
                          Qt to the tabwidget and sometimes not, depending on
                          if close buttons are enabled.
                          arg: The tab index to be closed.
    """

    tab_rightclicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyle(TabBarStyle(self.style()))

    def __repr__(self):
        return '<{} with {} tabs>'.format(self.__class__.__name__,
                                          self.count())

    def mousePressEvent(self, e):
        """Override mousePressEvent to emit tabCloseRequested on rightclick."""
        if e.button() != Qt.RightButton:
            super().mousePressEvent(e)
            return
        idx = self.tabAt(e.pos())
        if idx == -1:
            super().mousePressEvent(e)
            return
        e.accept()
        if config.get('tabbar', 'close-on-right-click'):
            self.tab_rightclicked.emit(idx)

    def minimumTabSizeHint(self, index):
        """Override minimumTabSizeHint because we want no hard minimum.

        There are two problems with having a hard minimum tab size:
        - When expanding is True, the window will expand without stopping
          on some window managers.
        - We don't want the main window to get bigger with many tabs. If
          nothing else helps, we *do* want the tabs to get smaller instead
          of enforcing a minimum window size.

        Args:
            index: The index of the tab to get a sizehint for.

        Return:
            A QSize.
        """
        height = super().tabSizeHint(index).height()
        return QSize(1, height)

    def tabSizeHint(self, index):
        """Override tabSizeHint so all tabs are the same size.

        https://wiki.python.org/moin/PyQt/Customising%20tab%20bars
        """
        height = self.fontMetrics().height()
        size = QSize(self.width() / self.count(), height)
        qt_ensure_valid(size)
        return size

    def paintEvent(self, e):
        """Override paintEvent to draw the tabs like we want to."""
        p = QStylePainter(self)
        tab = QStyleOptionTab()
        selected = self.currentIndex()
        for idx in range(self.count()):
            self.initStyleOption(tab, idx)
            if idx == selected:
                color = config.get('colors', 'tab.bg.selected')
            elif idx % 2:
                color = config.get('colors', 'tab.bg.odd')
            else:
                color = config.get('colors', 'tab.bg.even')
            tab.palette.setColor(QPalette.Window, QColor(color))
            tab.palette.setColor(QPalette.WindowText,
                                 QColor(config.get('colors', 'tab.fg')))
            if tab.rect.right() < 0 or tab.rect.left() > self.width():
                # Don't bother drawing a tab if the entire tab is outside of
                # the visible tab bar.
                continue
            p.drawControl(QStyle.CE_TabBarTab, tab)


class TabBarStyle(QCommonStyle):

    """Qt style used by TabBar to fix some issues with the default one.

    This fixes the following things:
        - Remove the focus rectangle Ubuntu draws on tabs.
        - Force text to be left-aligned even though Qt has "centered"
          hardcoded.

    Unfortunately PyQt doesn't support QProxyStyle, so we need to do this the
    hard way...

    Based on:

    http://stackoverflow.com/a/17294081
    https://code.google.com/p/makehuman/source/browse/trunk/makehuman/lib/qtgui.py

    Attributes:
        _style: The base/"parent" style.
    """

    def __init__(self, style):
        """Initialize all functions we're not overriding.

        This simply calls the corresponding function in self._style.

        Args:
            style: The base/"parent" style.
        """
        self._style = style
        for method in ('drawComplexControl', 'drawItemPixmap',
                       'generatedIconPixmap', 'hitTestComplexControl',
                       'itemPixmapRect', 'itemTextRect', 'pixelMetric',
                       'polish', 'styleHint', 'subControlRect',
                       'subElementRect', 'unpolish', 'sizeFromContents'):
            target = getattr(self._style, method)
            setattr(self, method, functools.partial(target))
        super().__init__()

    def drawPrimitive(self, element, option, painter, widget=None):
        """Override QCommonStyle.drawPrimitive.

        Call the genuine drawPrimitive of self._style, except when a focus
        rectangle should be drawn.

        Args:
            element: PrimitiveElement pe
            option: const QStyleOption * opt
            painter: QPainter * p
            widget: const QWidget * widget
        """
        if element == QStyle.PE_FrameFocusRect:
            return
        return self._style.drawPrimitive(element, option, painter, widget)

    def drawItemText(self, painter, rectangle, alignment, palette, enabled,
                     text, textRole=QPalette.NoRole):
        """Extend QCommonStyle::drawItemText to not center-align text.

        Since Qt hardcodes the text alignment for tabbar tabs in QCommonStyle,
        we need to undo this here by deleting the flag again, and align left
        instead.


        Draws the given text in the specified rectangle using the provided
        painter and palette.

        The text is drawn using the painter's pen, and aligned and wrapped
        according to the specified alignment. If an explicit textRole is
        specified, the text is drawn using the palette's color for the given
        role. The enabled parameter indicates whether or not the item is
        enabled; when reimplementing this function, the enabled parameter
        should influence how the item is drawn.

        Args:
            painter: QPainter *
            rectangle: const QRect &
            alignment int (Qt::Alignment)
            palette: const QPalette &
            enabled: bool
            text: const QString &
            textRole: QPalette::ColorRole textRole
        """
        # pylint: disable=invalid-name
        alignment &= ~Qt.AlignHCenter
        alignment |= Qt.AlignLeft
        self._style.drawItemText(painter, rectangle, alignment, palette,
                                 enabled, text, textRole)

    def drawControl(self, element, opt, p, widget=None):
        """Override drawControl to draw odd tabs in a different color.

        Draws the given element with the provided painter with the style
        options specified by option.

        Args:
            element: ControlElement
            option: const QStyleOption *
            painter: QPainter *
            widget: const QWidget *
        """
        if element == QStyle.CE_TabBarTab:
            # We override this so we can control TabBarTabShape/TabBarTabLabel.
            self.drawControl(QStyle.CE_TabBarTabShape, opt, p, widget)
            self.drawControl(QStyle.CE_TabBarTabLabel, opt, p, widget)
        elif element == QStyle.CE_TabBarTabShape:
            # We use super() rather than self._style here because we don't want
            # any sophisticated drawing.
            p.fillRect(opt.rect, opt.palette.window())
            super().drawControl(QStyle.CE_TabBarTabShape, opt, p, widget)
        elif element == QStyle.CE_TabBarTabLabel:
            # We use super() rather than self._style here so our drawItemText()
            # gets called.
            super().drawControl(QStyle.CE_TabBarTabLabel, opt, p, widget)
        else:
            # For any other elements we just delegate the work to our real
            # style.
            self._style.drawControl(element, opt, p, widget)
