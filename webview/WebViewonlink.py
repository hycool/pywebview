import os

from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
# from PyQt5.QtWidgets import *


# class MyPage(QWebEnginePage):
#     def __init__(self, parent=None):
#         super(MyPage, self).__init__(parent)
#     def triggerAction(self, action, checked=False):
#         if action == QWebEnginePage.OpenLinkInNewWindow:
#             self.createWindow(QWebEnginePage.WebBrowserWindow)
#
#         return super(MyPage, self).triggerAction(action, checked)

class WebViewonlink(QWebEngineView):
    def __init__(self, parent=None):
        super(WebViewonlink, self).__init__(parent)

        # self.myPage = MyPage(self)
        #
        # self.setPage(self.myPage)

    def createWindow(self, windowType):
        if windowType == QWebEnginePage.WebBrowserTab:
            self.webView = WebViewonlink()
            self.webView.setAttribute(Qt.WA_DeleteOnClose, True)
            self.webView.show()
            return self.webView

        if windowType == QWebEnginePage.WebBrowserWindow:
            self.webView = WebViewonlink()
            self.webView.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

            return self.webView

        return super(WebViewonlink, self).createWindow(windowType)