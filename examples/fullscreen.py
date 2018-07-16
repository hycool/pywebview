import webview

"""
This example demonstrates how to create a full-screen webview window.
"""

if __name__ == '__main__':
    webview.config.use_qt = True
    # Create a non-resizable webview window with 800x600 dimensions
    webview.create_window("Full-screen browser", "index.html", fullscreen=True)