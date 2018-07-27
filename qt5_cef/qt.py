import sys
import os
from PyQt5 import QtCore
from threading import Event
import qt5_cef.constant as constant
from gpuinfo.windows import get_gpus
from cefpython3 import cefpython as cef
from uuid import uuid4
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

default_window_width = constant.default_window_width
default_window_height = constant.default_window_height
default_window_title = constant.default_window_title
min_window_width = constant.min_window_width
min_window_height = constant.min_window_height


class CefApplication(QApplication):
    def __init__(self, args):
        super(CefApplication, self).__init__(args)
        self.timer = self.create_timer()

    def create_timer(self):
        timer = QTimer()
        timer.timeout.connect(self.on_timer)
        timer.start(10)
        return timer

    @staticmethod
    def on_timer():
        cef.MessageLoopWork()

    def stop_timer(self):
        # Stop the timer after Qt's message loop has ended
        self.timer.stop()


class LoadHandler(object):
    def __init__(self, uid, payload):
        self.payload = payload
        self.uid = uid

    def OnLoadStart(self, browser, frame):
        with open(os.path.dirname(__file__) + '/burgeon.cef.sdk.js', 'r', encoding='UTF-8') as js:
            browser.ExecuteJavascript(js.read())
        append_payload(self.uid, self.payload)

    def OnLoadError(self, browser, frame, error_code, error_text_out, failed_url):
        with open(os.path.dirname(__file__) + '/burgeon.cef.sdk.js', 'r', encoding='UTF-8') as js:
            browser.ExecuteJavascript(js.read())
        append_payload(self.uid, self.payload)


class BrowserView(QMainWindow):
    instances = {}

    full_screen_trigger = QtCore.pyqtSignal()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error

    def __init__(self, uid, title, url, width, height, resizable, full_scrren,
                 min_size, background_color, webview_ready):
        super(BrowserView, self).__init__()
        BrowserView.instances[uid] = self
        self.uid = uid
        self.is_full_screen = False
        self.load_event = Event()

        self.resize(width, height)  # QWidget.resize 重新调整qt 窗口大小
        self.title = title
        self.setWindowTitle(title)  # QWidget.setWindowTitle 窗口标题重命名

        # Set window background color
        self.background_color = QColor()
        self.background_color.setNamedColor(background_color)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), self.background_color)
        self.setPalette(palette)

        if not resizable:
            self.setFixedSize(width, height)

        self.setMinimumSize(min_size[0], min_size[1])

        window_info = cef.WindowInfo()
        rect = [0, 0, self.width(), self.height()]
        window_info.SetAsChild(int(self.winId()), rect)
        # window_info.SetAsChild(int(self.winId()))

        setting = {
            "standard_font_family": "Microsoft YaHei",
            "default_encoding": "utf-8",
            "plugins_disabled": True,
            "tab_to_links_disabled": True,
            "web_security_disabled": True,
        }

        if url is not None:
            pass
            self.view = cef.CreateBrowserSync(window_info, url=url, settings=setting)
        else:
            self.view = cef.CreateBrowserSync(window_info, url="about:blank", settings=setting)

        # self.view.ShowDevTools()
        self.full_screen_trigger.connect(self.toggleFullScreen)
        self.load_event.set()

        if full_scrren:
            self.emit_full_screen_signal()

        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.activateWindow()
        self.raise_()
        if webview_ready is not None:
            webview_ready.set()

    def closeEvent(self, event):
        if self.uid == 'master':
            self.closeAllWindows()
        else:
            if event.spontaneous():
                event.ignore()
                self.view.ExecuteFunction('window.__cef__.dispatchCustomEvent', 'windowCloseEvent')
            else:
                event.accept()

    def resizeEvent(self, event):
        cef.WindowUtils.OnSize(self.winId(), 0, 0, 0)

    def closeWindow(self):
        """
        This method can be invoked by Javascript.
        :return:
        """
        self.view.CloseDevTools()  # 关闭cef的devTools
        self.close()  # 关闭qt的窗口

    def closeAllWindows(self):
        """
        This method can be invoked by Javascript.
        :return:
        """
        for qt_main_window in BrowserView.instances.values():
            qt_main_window.close()

    def open(self, param=None):
        """
        This method can be invoked by Javascript.
        :return:
        """
        if param is None:
            param = {}
        if isinstance(param, dict):
            param.setdefault('url', 'about:blank')
            param.setdefault('title', default_window_title)
            param.setdefault('payload', {})
            open_new_window(url=param["url"], title=param["title"], payload=param["payload"])
        elif isinstance(param, str):
            open_new_window(url=param)

    def toggleFullScreen(self):
        if self.is_full_screen:
            self.showNormal()
        else:
            self.showFullScreen()

        self.is_full_screen = not self.is_full_screen

    def emit_full_screen_signal(self):
        self.full_screen_trigger.emit()

    def create_cef_pure_window(self, url):
        """
        This method can be invoked by Javascript.
        :return:
        """
        cef_window = cef.CreateBrowserSync(url=url)
        cef_window.SetZoomLevel(5.0)


def generate_guid():
    return 'child_' + uuid4().hex[:8]


def open_new_window(url, title=default_window_title, payload=None):
    create_browser_view(uid=generate_guid(), url=url, title=title, payload=payload)


def create_browser_view(uid, title="", url=None, width=default_window_width, height=default_window_height,
                        resizable=True, full_screen=False,
                        min_size=(min_window_width, min_window_height),
                        background_color="#ffffff", web_view_ready=None, payload=None):
    browser = BrowserView(uid, title, url, width, height, resizable, full_screen, min_size,
                          background_color, web_view_ready)
    browser.show()
    set_client_handler(uid, payload)
    set_javascript_bindings(uid)


def launch_main_window(uid, title, url, width, height, resizable, full_screen, min_size,
                       background_color, web_view_ready, context_menu=False):
    app = CefApplication(sys.argv)
    settings = {
        'context_menu': {'enabled': context_menu},
        'auto_zooming': 0.0
    }
    switches = {}
    if len(get_gpus()) == 0:
        switches.setdefault('disable-gpu', '')
    cef.Initialize(settings=settings, switches=switches)
    create_browser_view(uid, title, url, width, height, resizable, full_screen, min_size,
                        background_color, web_view_ready)
    app.exec_()
    app.stop_timer()
    del app
    cef.Shutdown()


def set_client_handler(uid, payload):
    BrowserView.instances[uid].view.SetClientHandler(LoadHandler(uid, payload))


def set_javascript_bindings(uid):
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    bindings.SetProperty("cefPython3", cef.GetVersion())
    bindings.SetProperty('windowId', uid)
    bindings.SetObject('windowInstance', BrowserView.instances[uid])
    BrowserView.instances[uid].view.SetJavascriptBindings(bindings)


def append_payload(uid, payload):
    BrowserView.instances[uid].view.ExecuteFunction('window.__cef__.updateWindowInstance', 'id', uid)
    if payload is None:
        return
    if isinstance(payload, dict):
        fun_list = []
        for (k, v) in payload.items():
            if isinstance(v, cef.JavascriptCallback):
                fun_list.append(k)
                BrowserView.instances[uid].view.ExecuteFunction('window.__cef__.console',
                                                                '检测到 payload.{key} 是函数类型，启动新窗口时挂载的payload中不允许包含函数'
                                                                .format(key=k),
                                                                'warn')
        for key in fun_list:
            del payload[key]
        BrowserView.instances[uid].view.ExecuteFunction('window.__cef__.initializeCustomizePayload', payload)
    else:
        BrowserView.instances[uid].view.ExecuteFunction('window.__cef__.console',
                                                        '启动新窗口时挂载的payload必须为JsonObject，且对象属性不能为函数: payload = {payload}'
                                                        .format(payload=payload))
