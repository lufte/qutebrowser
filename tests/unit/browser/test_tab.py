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

import pytest

from qutebrowser.browser import browserpane
from qutebrowser.utils import utils

pytestmark = pytest.mark.usefixtures('redirect_webengine_data')

try:
    from PyQt5.QtWebKitWidgets import QWebView
except ImportError:
    QWebView = None

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None


@pytest.fixture(params=[QWebView, QWebEngineView])
def view(qtbot, config_stub, request):
    if request.param is None:
        pytest.skip("View not available")

    v = request.param()
    qtbot.add_widget(v)
    return v


@pytest.fixture(params=['webkit', 'webengine'])
def tab(request, qtbot, tab_registry, cookiejar_and_cache, mode_manager):
    if request.param == 'webkit':
        webkitpane = pytest.importorskip('qutebrowser.browser.webkit.webkitpane')
        tab_class = webkitpane.WebKitTab
    elif request.param == 'webengine':
        webenginepane = pytest.importorskip(
            'qutebrowser.browser.webengine.webenginepane')
        tab_class = webenginepane.WebEngineTab
    else:
        raise utils.Unreachable

    t = tab_class(win_id=0, mode_manager=mode_manager)
    qtbot.add_widget(t)
    yield t


class Zoom(browserpane.AbstractZoom):

    def _set_factor_internal(self, _factor):
        pass

    def factor(self):
        raise utils.Unreachable


class Tab(browserpane.AbstractTab):

    # pylint: disable=abstract-method

    def __init__(self, win_id, mode_manager, parent=None):
        super().__init__(win_id=win_id, mode_manager=mode_manager,
                         parent=parent)
        self.history = browserpane.AbstractHistory(self)
        self.scroller = browserpane.AbstractScroller(self, parent=self)
        self.caret = browserpane.AbstractCaret(win_id=self.win_id,
                                              mode_manager=mode_manager,
                                              tab=self, parent=self)
        self.zoom = Zoom(win_id=self.win_id)
        self.search = browserpane.AbstractSearch(parent=self)
        self.printing = browserpane.AbstractPrinting()
        self.elements = browserpane.AbstractElements(self)
        self.action = browserpane.AbstractAction()

    def _install_event_filter(self):
        pass


@pytest.mark.xfail(run=False, reason='Causes segfaults, see #1638')
def test_tab(qtbot, view, config_stub, tab_registry, mode_manager):
    tab_w = Tab(win_id=0, mode_manager=mode_manager)
    qtbot.add_widget(tab_w)

    assert tab_w.win_id == 0
    assert tab_w._widget is None

    tab_w._set_widget(view)
    assert tab_w._widget is view
    assert tab_w.history._tab is tab_w
    assert tab_w.history._history is view.history()
    assert view.parent() is tab_w

    with qtbot.waitExposed(tab_w):
        tab_w.show()
