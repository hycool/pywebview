import webview
import threading
import time

"""
This example demonstrates how to load HTML in a web view window
"""


def load_html():
    webview.load_url("http://www.baidu.com")
    # time.sleep(2)


if __name__ == '__main__':
    t = threading.Thread(target=load_html)
    t.start()
    # Create a non-resizable webview window with 800x600 dimensions
    webview.create_window("Simple browser", width=800, height=600, resizable=True)
