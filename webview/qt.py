'''
(C) 2014-2016 Roman Sirokov and contributors
Licensed under BSD license

http://github.com/r0x0r/pywebview/
'''

import logging
import os
import sys
import base64
from threading import Semaphore, Event
from cefpython3 import cefpython as cef

from webview import OPEN_DIALOG, FOLDER_DIALOG, SAVE_DIALOG
from webview import _parse_api_js, _js_bridge_call
from webview.localization import localization

# Fix for PyCharm hints warnings when using static methods
WindowUtils = cef.WindowUtils()

logger = logging.getLogger(__name__)

# Try importing Qt5 modules
try:
    from PyQt5 import QtCore

    # Check to see if we're running Qt > 5.5
    from PyQt5.QtCore import QT_VERSION_STR

    _qt_version = [int(n) for n in QT_VERSION_STR.split('.')]

    # if _qt_version >= [5, 5]:
    #
    #     # # from webview.WebViewonlink import WebViewonlink as QWebView
    #     # from PyQt5.QtWebEngineWidgets import  QWebEngineSettings as QWebSettings
    #     # from PyQt5.QtWebChannel import QWebChannel
    #     # from widget.mainwindow import MainWindow
    # else:
    #     from PyQt5.QtWebKitWidgets import QWebView

    from PyQt5.QtGui import *
    # noinspection PyUnresolvedReferences
    from PyQt5.QtCore import *
    # noinspection PyUnresolvedReferences
    from PyQt5.QtWidgets import *

    # logger.debug('Using Qt5')
except ImportError as e:
    logger.exception('PyQt5 or one of dependencies is not found')
    _import_error = True
else:
    _import_error = False


class BrowserView(QMainWindow):
    instances = {}

    create_window_trigger = QtCore.pyqtSignal(object)
    set_title_trigger = QtCore.pyqtSignal(str)
    load_url_trigger = QtCore.pyqtSignal(str)
    html_trigger = QtCore.pyqtSignal(str, str)
    dialog_trigger = QtCore.pyqtSignal(int, str, bool, str, str)
    destroy_trigger = QtCore.pyqtSignal()
    fullscreen_trigger = QtCore.pyqtSignal()
    current_url_trigger = QtCore.pyqtSignal()
    evaluate_js_trigger = QtCore.pyqtSignal(str)

    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error

    class JSBridge(QtCore.QObject):
        api = None
        parent_uid = None

        try:
            qtype = QtCore.QJsonValue  # QT5
        except AttributeError:
            qtype = str  # QT4

        def __init__(self):
            super(BrowserView.JSBridge, self).__init__()

        @QtCore.pyqtSlot(str, qtype, result=str)
        def call(self, func_name, param):
            func_name = BrowserView._convert_string(func_name)
            param = BrowserView._convert_string(param)

            return _js_bridge_call(self.parent_uid, self.api, func_name, param)

    def __init__(self, uid, title, url, width, height, resizable, fullscreen,
                 min_size, confirm_quit, background_color, debug, js_api, webview_ready):
        super(BrowserView, self).__init__()
        BrowserView.instances[uid] = self
        self.uid = uid

        self.is_fullscreen = False
        self.confirm_quit = confirm_quit

        self._file_name_semaphore = Semaphore(0)
        self._current_url_semaphore = Semaphore()
        self._evaluate_js_semaphore = Semaphore(0)
        self.load_event = Event()

        self._evaluate_js_result = None
        self._current_url = None
        self._file_name = None

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
        self.check_versions()

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

        # self.browser.SetClientHandler(LoadHandler(self.parent.navigation_bar))
        # self.browser.SetClientHandler(FocusHandler(self))

        self.create_window_trigger.connect(BrowserView.on_create_window)
        self.load_url_trigger.connect(self.on_load_url)
        self.html_trigger.connect(self.on_load_html)
        self.dialog_trigger.connect(self.on_file_dialog)
        self.destroy_trigger.connect(self.on_destroy_window)
        self.fullscreen_trigger.connect(self.on_fullscreen)
        self.current_url_trigger.connect(self.on_current_url)
        self.evaluate_js_trigger.connect(self.on_evaluate_js)
        self.set_title_trigger.connect(self.on_set_title)

        self.js_bridge = BrowserView.JSBridge()
        self.js_bridge.api = js_api
        self.js_bridge.parent_uid = self.uid

        # if _qt_version >= [5, 5]:
        #     self.channel = QWebChannel(self.view.page())
        #     self.view.page().setWebChannel(self.channel)

        self.load_event.set()

        if fullscreen:
            self.toggle_fullscreen()

        # self.view.setContextMenuPolicy(QtCore.Qt.NoContextMenu)  # disable right click context menu

        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())

        # self.view.settings().setAttribute(QWebSettings.LocalContentCanAccessFileUrls, True);
        #
        # self.view.settings().setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True);

        self.activateWindow()
        self.raise_()
        webview_ready.set()

    def on_set_title(self, title):
        self.setWindowTitle(title)

    def on_file_dialog(self, dialog_type, directory, allow_multiple, save_filename, file_filter):
        if dialog_type == FOLDER_DIALOG:
            self._file_name = QFileDialog.getExistingDirectory(self, localization['linux.openFolder'],
                                                               options=QFileDialog.ShowDirsOnly)
        elif dialog_type == OPEN_DIALOG:
            if allow_multiple:
                self._file_name = QFileDialog.getOpenFileNames(self, localization['linux.openFiles'], directory,
                                                               file_filter)
            else:
                self._file_name = QFileDialog.getOpenFileName(self, localization['linux.openFile'], directory,
                                                              file_filter)
        elif dialog_type == SAVE_DIALOG:
            if directory:
                save_filename = os.path.join(str(directory), str(save_filename))

            self._file_name = QFileDialog.getSaveFileName(self, localization['global.saveFile'], save_filename)

        self._file_name_semaphore.release()

    def on_current_url(self):
        self._current_url = self.view.GetUrl()
        self._current_url_semaphore.release()

    def on_load_url(self, url):
        self.view.LoadUrl(url)
        self.load_event.set()

    def on_load_html(self, html, js_callback=None):
        # This function is called in two ways:
        # 1. From Python: in this case value is returned
        # 2. From Javascript: in this case value cannot be returned because
        #    inter-process messaging is asynchronous, so must return value
        #    by calling js_callback.
        html = html.encode("utf-8", "replace")
        b64 = base64.b64encode(html).decode("utf-8", "replace")
        ret = "data:text/html;base64,{data}".format(data=b64)
        if js_callback:
            self.view.js_print(js_callback.GetFrame().GetBrowser(),
                               "Python", "html_to_data_uri",
                               "Called from Javascript. Will call Javascript callback now.")
            js_callback.Call(ret)
        else:
            self.view.LoadUrl(ret)
        self.load_event.set()

    def check_versions(self):
        """
        ver = cef.GetVersion()
        print("[tutorial.py] CEF Python {ver}".format(ver=ver["version"]))
        print("[tutorial.py] Chromium {ver}".format(ver=ver["chrome_version"]))
        print("[tutorial.py] CEF {ver}".format(ver=ver["cef_version"]))
        print("[tutorial.py] Python {ver} {arch}".format(
            ver=platform.python_version(),
            arch=platform.architecture()[0]))
        """
        assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"

    def closeEvent(self, event):
        if self.confirm_quit:
            reply = QMessageBox.question(self, self.title, localization['global.quitConfirmation'],
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.No:
                event.ignore()
                return

        event.accept()
        # del BrowserView.instances[self.uid]

        super(BrowserView, self).closeEvent(event)

    def setCookie(self, cookie):
        cookieStore = self.view.page().profile().cookieStore()
        cookieStore.setCookie(cookie)

    def on_destroy_window(self):
        self.close()

    def on_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()

        self.is_fullscreen = not self.is_fullscreen

    def on_evaluate_js(self, script):

        self._evaluate_js_semaphore.release()

        self.view.GetMainFrame().ExecuteJavascript(script)

        # self._evaluate_js_result = self.view.ExecuteJavascript(script)

    def on_load_finished(self):
        if self.js_bridge.api:
            self._set_js_api()
        else:
            self.load_event.set()

    def set_title(self, title):
        self.set_title_trigger.emit(title)

    def get_current_url(self):
        self.current_url_trigger.emit()
        self._current_url_semaphore.acquire()

        return self._current_url

    def load_url(self, url):
        self.load_event.clear()
        self.load_url_trigger.emit(url)

    def load_html(self, content, base_uri):
        self.load_event.clear()
        self.html_trigger.emit(content, base_uri)

    def create_file_dialog(self, dialog_type, directory, allow_multiple, save_filename, file_filter):
        self.dialog_trigger.emit(dialog_type, directory, allow_multiple, save_filename, file_filter)
        self._file_name_semaphore.acquire()

        if _qt_version >= [5, 0]:  # QT5
            if dialog_type == FOLDER_DIALOG:
                file_names = (self._file_name,)
            elif dialog_type == SAVE_DIALOG or not allow_multiple:
                file_names = (self._file_name[0],)
            else:
                file_names = tuple(self._file_name[0])

        else:  # QT4
            if dialog_type == FOLDER_DIALOG:
                file_names = (BrowserView._convert_string(self._file_name),)
            elif dialog_type == SAVE_DIALOG or not allow_multiple:
                file_names = (BrowserView._convert_string(self._file_name[0]),)
            else:
                file_names = tuple([BrowserView._convert_string(s) for s in self._file_name])

        # Check if we got an empty tuple, or a tuple with empty string
        if len(file_names) == 0 or len(file_names[0]) == 0:
            return None
        else:
            return file_names

    def destroy_(self):
        self.destroy_trigger.emit()

    def toggle_fullscreen(self):
        self.fullscreen_trigger.emit()

    def evaluate_js(self, script):
        self.load_event.wait()
        print("evaluate_js")
        self.evaluate_js_trigger.emit(script)
        self._evaluate_js_semaphore.acquire()

        return self._evaluate_js_result

    def js_api(self, content):
        # Execute Javascript function "js_print"
        self.view.ExecuteFunction("eval", content)

    def _set_js_api(self):
        def _register_window_object():
            frame.addToJavaScriptWindowObject('external', self.js_bridge)

        script = _parse_api_js(self.js_bridge.api)

        if _qt_version >= [5, 5]:
            qwebchannel_js = QtCore.QFile('://qtwebchannel/qwebchannel.js')
            if qwebchannel_js.open(QtCore.QFile.ReadOnly):
                source = bytes(qwebchannel_js.readAll()).decode('utf-8')
                self.view.page().runJavaScript(source)
                self.channel.registerObject('external', self.js_bridge)
                qwebchannel_js.close()
        elif _qt_version >= [5, 0]:
            frame = self.view.page().mainFrame()
            _register_window_object()
        else:
            frame = self.view.page().mainFrame()
            _register_window_object()

        try:  # PyQt4
            self.view.page().mainFrame().evaluateJavaScript(script)
        except AttributeError:  # PyQt5
            self.view.page().runJavaScript(script)

        self.load_event.set()

    @staticmethod
    def _convert_string(qstring):
        try:
            qstring = qstring.toString()  # QJsonValue conversion
        except:
            pass

        if sys.version < '3':
            return unicode(qstring)
        else:
            return str(qstring)

    @staticmethod
    # Receive func from subthread and execute it on the main thread
    def on_create_window(func):
        func()


def create_window_test(url='http://wwww.baidu.com'):
    cef.CreateBrowserSync(url=url)


def create_window(uid, title, url, width, height, resizable, fullscreen, min_size,
                  confirm_quit, background_color, debug, js_api, webview_ready, context_menu, payload):
    # app = QApplication.instance() or QApplication([])

    app = CefApplication(sys.argv)
    settings = {
        'context_menu': {'enabled': context_menu},
    }
    cef.Initialize(settings)

    def _create():
        browser = BrowserView(uid, title, url, width, height, resizable, fullscreen,
                              min_size, confirm_quit, background_color, debug, js_api,
                              webview_ready)
        browser.show()
        set_javascript_bindings(uid, payload)

    _create()
    app.exec_()
    app.stopTimer()
    del app
    cef.Shutdown()

    # annotation by hy@20180720
    # if uid == 'master':
    #     _create()
    #     app.exec_()
    #     app.stopTimer()
    #     # del browser  # Just to be safe, similarly to "del app"
    #     del app  # Must destroy app object before calling Shutdown
    #     cef.Shutdown()
    # else:
    #     i = list(BrowserView.instances.values())[0]  # arbitary instance
    #     i.create_window_trigger.emit(_create)


def set_javascript_bindings(uid, payload):
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    for k, v in payload.items():
        if v['type'] == 'function':
            bindings.SetFunction(k, v['value'])
    bindings.SetProperty("cefPython3", cef.GetVersion())
    bindings.SetFunction('create_window_test', create_window_test)
    BrowserView.instances[uid].view.SetJavascriptBindings(bindings)


def set_title(title, uid):
    BrowserView.instances[uid].set_title(title)


def get_current_url(uid):
    return BrowserView.instances[uid].get_current_url()


def load_url(url, uid):
    BrowserView.instances[uid].load_url(url)


def setCookie(cookie, uid):
    BrowserView.instances[uid].setCookie(cookie)


def load_html(content, base_uri, uid):
    BrowserView.instances[uid].load_html(content, base_uri)


def destroy_window(uid):
    BrowserView.instances[uid].destroy_()


def toggle_fullscreen(uid):
    BrowserView.instances[uid].toggle_fullscreen()


def create_file_dialog(dialog_type, directory, allow_multiple, save_filename, file_types):
    # Create a file filter by parsing allowed file types
    file_types = [s.replace(';', ' ') for s in file_types]
    file_filter = ';;'.join(file_types)

    i = list(BrowserView.instances.values())[0]
    return i.create_file_dialog(dialog_type, directory, allow_multiple, save_filename, file_filter)


def evaluate_js(script, uid):
    return BrowserView.instances[uid].evaluate_js(script)


class CefApplication(QApplication):
    def __init__(self, args):
        super(CefApplication, self).__init__(args)
        self.timer = self.createTimer()
        # self.setupIcon()

    def createTimer(self):
        timer = QTimer()
        # noinspection PyUnresolvedReferences
        timer.timeout.connect(self.onTimer)
        timer.start(10)
        return timer

    def onTimer(self):
        cef.MessageLoopWork()

    def stopTimer(self):
        # Stop the timer after Qt's message loop has ended
        self.timer.stop()

    def setupIcon(self):
        icon_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 "resources", "{0}.png".format(sys.argv[1]))
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))
