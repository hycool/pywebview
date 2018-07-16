import webview
import threading

"""
This example demonstrates evaluating JavaScript in a webpage.
"""

def evaluate_js():
    import time
    time.sleep(2)

    # Change document background color and print document title
    print(webview.evaluate_js("(function(){var a=123;alert(a)})()"))


if __name__ == '__main__':
    t = threading.Thread(target=evaluate_js)
    t.start()
    webview.config.use_qt = True
    webview.create_window('Run custom JavaScript')