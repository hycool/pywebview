import sys
from threading import Event
from cefpython3 import cefpython as cef
from uuid import uuid4
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


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


class BrowserView(QMainWindow):
    instances = {}

    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error

    def __init__(self, uid, title, url, width, height, resizable, fullscreen,
                 min_size, background_color, webview_ready):
        super(BrowserView, self).__init__()
        BrowserView.instances[uid] = self
        self.uid = uid
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

        setting = {
            "default_encoding": "utf-8",
            "plugins_disabled": True,
            "tab_to_links_disabled": True,
            "web_security_disabled": True,
        }
        if url is not None:
            self.view = cef.CreateBrowserSync(window_info, url=url, settings=setting)
        else:
            self.view = cef.CreateBrowserSync(window_info, url="about:blank", settings=setting)

        # self.view.ShowDevTools()
        self.load_event.set()

        if fullscreen:
            self.toggle_full_screen()

        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.activateWindow()
        self.raise_()
        if webview_ready is not None:
            webview_ready.set()

    """
    描述：监听qt窗口关闭事件
    :param event: 事件
    """
    def closeEvent(self, event):
        if event.spontaneous():
            event.ignore()
            self.view.ExecuteFunction('window.__cef__.dispatchCustomEvent', 'windowCloseEvent')
        else:
            event.accept()

    """
    描述：主调关闭当前窗口 
    """
    def closeWindow(self):
        self.close()


def generate_guid():
    return 'child_' + uuid4().hex[:8]


def open_new_window(url):
    create_browser_view(uid=generate_guid(), url=url)


def create_browser_view(uid, title="", url=None, width=800, height=600, resizable=True, full_screen=False,
                        min_size=(200, 100),
                        background_color="#ffffff", web_view_ready=None):
    browser = BrowserView(uid, title, url, width, height, resizable, full_screen, min_size,
                          background_color, web_view_ready)
    browser.show()
    set_javascript_bindings(uid)


def create_window(uid, title, url, width, height, resizable, full_screen, min_size,
                  background_color, web_view_ready, context_menu=False):
    app = CefApplication(sys.argv)
    settings = {
        'context_menu': {'enabled': context_menu},
    }
    cef.Initialize(settings)

    create_browser_view(uid, title, url, width, height, resizable, full_screen, min_size,
                        background_color, web_view_ready)
    app.exec_()
    app.stop_timer()
    del app
    cef.Shutdown()


def set_javascript_bindings(uid):
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    bindings.SetProperty("cefPython3", cef.GetVersion())
    bindings.SetFunction('open_new_window', open_new_window)
    bindings.SetProperty('windowId', uid)
    bindings.SetObject('windowInstance', BrowserView.instances[uid])
    BrowserView.instances[uid].view.SetJavascriptBindings(bindings)
