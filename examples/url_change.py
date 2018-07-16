import webview
import threading

"""
This example demonstrates how a webview window is created and URL is changed after 10 seconds.
"""

def change_url():
    import time
    time.sleep(3)
    webview.load_url("http://www.hao123.com/")
    webview.gui.set_title("nihao","master")
    print(webview.get_current_url())


if __name__ == '__main__':
    webview.config.use_qt = True
    t = threading.Thread(target=change_url)
    t.start()

    # Create a non-resizable webview window with 800x600 dimensions
    webview.create_window("Simple browser", "http://www.baidu.com", width=800, height=600, resizable=True)

