import qt5_cef
# import threading


# def get_window_instance(url):
#     def load_url():
#         uid = webview.generate_guid()
#         load_thread = threading.Thread(target=webview.load_url, args=(url, uid))
#         load_thread.start()
#         webview.create_window(uid=uid, title='The Title Of WebView', width=1200, height=800, context_menu=True)
#
#     new_web_view_thread = threading.Thread(target=load_url, name='child_thread_1')
#     new_web_view_thread.start()


if __name__ == '__main__':
    qt5_cef.load_url('http://localhost:8421/pywebview/burgeon/assets/index.html')
