#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
pywebview is a lightweight cross-platform wrapper around a webview component that allows to display HTML content in its
own dedicated window. Works on Windows, OS X and Linux and compatible with Python 2 and 3.

(C) 2014-2016 Roman Sirokov and contributors
Licensed under BSD license

http://github.com/r0x0r/pywebview/
"""

import os
import re
import json
import logging
import time
from threading import Event, Thread, current_thread
from uuid import uuid4

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

OPEN_DIALOG = 10
FOLDER_DIALOG = 20
SAVE_DIALOG = 30

_webview_ready = Event()


# func:
def generate_guid():
    """generate_guid, created by hy@20180720"""
    return 'child_' + uuid4().hex[:8]


def create_file_dialog(dialog_type=OPEN_DIALOG, directory='', allow_multiple=False, save_filename='', file_types=()):
    """
    Create a file dialog
    :param dialog_type: Dialog type: open file (OPEN_DIALOG), save file (SAVE_DIALOG), open folder (OPEN_FOLDER). Default
                        is open file.
    :param directory: Initial directory
    :param allow_multiple: Allow multiple selection. Default is false.
    :param save_filename: Default filename for save file dialog.
    :param file_types: Allowed file types in open file dialog. Should be a tuple of strings in the format:
        filetypes = ('Description (*.extension[;*.extension[;...]])', ...)
    :return:
    """
    if type(file_types) != tuple and type(file_types) != list:
        raise TypeError('file_types must be a tuple of strings')
    for f in file_types:
        _parse_file_type(f)

    if not os.path.exists(directory):
        directory = ''

    try:
        _webview_ready.wait(5)
        return gui.create_file_dialog(dialog_type, directory, allow_multiple, save_filename, file_types)
    except NameError as e:
        raise Exception("Create a web view window first, before invoking this function", e)


def get_window_instance(url=''):
    def do_load_url():
        uid = generate_guid()
        create_window(
            uid=uid,
            url=url,
            title='The Title Of WebView @ {time} '.format(time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            width=1200,
            height=800,
            context_menu=True
        )

    new_web_view_thread = Thread(target=do_load_url)
    new_web_view_thread.start()


# 内置window对象
window_payload = {
    'py_console': {
        'type': 'function',
        'value': lambda msg='': print('py_console : ', msg)
    },
    'get_window_instance': {
        'type': 'function',
        'value': get_window_instance
    },
}


def load_url(url, uid='master'):
    """
    Load a new URL into a previously created WebView window. This function must be invoked after WebView windows is
    created with create_window(). Otherwise an exception is thrown.
    :param url: url to load
    :param uid: uid of the target instance
    """
    try:
        _webview_ready.wait(5)
        gui.load_url(url, uid)
    except NameError:
        raise Exception("Create a web view window first, before invoking this function")
    except KeyError:
        raise Exception("Cannot call function: No webview exists with uid: {}".format(uid))


def load_html(content, base_uri='', uid='master'):
    """
    Load a new content into a previously created WebView window. This function must be invoked after WebView windows is
    created with create_window(). Otherwise an exception is thrown.
    :param content: Content to load.
    :param base_uri: Base URI for resolving links. Default is "".
    :param uid: uid of the target instance
    """
    try:
        _webview_ready.wait(5)
        gui.load_html(_make_unicode(content), base_uri, uid)
    except NameError as e:
        raise Exception("Create a web view window first, before invoking this function")
    except KeyError:
        raise Exception("Cannot call function: No webview exists with uid: {}".format(uid))


def create_window(uid='master', title='', url=None, js_api=None, width=800, height=600,
                  resizable=True, fullscreen=False, min_size=(200, 100), strings={}, confirm_quit=False,
                  background_color='#FFFFFF', debug=False, context_menu=False, payload=window_payload):
    """
    Create a web view window using a native GUI. The execution blocks after this function is invoked, so other
    program logic must be executed in a separate thread.
    :param uid: the unique web view identifier
    :param title: Window title
    :param url: URL to load
    :param width: Optional window width (default: 800px)
    :param height: Optional window height (default: 600px)
    :param resizable True if window can be resized, False otherwise. Default is True
    :param fullscreen: True if start in fullscreen mode. Default is False
    :param min_size: a (width, height) tuple that specifies a minimum window size. Default is 200x100
    :param strings: a dictionary with localized strings
    :param confirm_quit: Display a quit confirmation dialog. Default is False
    :param background_color: Background color as a hex string that is displayed before the content of webview is loaded. Default is white.
    :param context_menu: enable devTool with context_menu
    :param payload: when window instance is created , the content of payload will be injected into global window object
    :return:
    """
    global gui
    import webview.qt as gui
    _webview_ready.clear()
    gui.create_window(uid, _make_unicode(title), _transform_url(url),
                      width, height, resizable, fullscreen, min_size, confirm_quit,
                      background_color, debug, js_api, _webview_ready, context_menu, payload)


def set_title(title, uid='master'):
    """
    Sets a new title of the window
    """
    try:
        _webview_ready.wait(5)
        return gui.set_title(title, uid)
    except NameError:
        raise Exception('Create a web view window first, before invoking this function')
    except KeyError:
        raise Exception('Cannot call function: No webview exists with uid: {}'.format(uid))


def get_current_url(uid='master'):
    """
    Get a current URL
    :param uid: uid of the target instance
    """
    try:
        _webview_ready.wait(5)
        return gui.get_current_url(uid)
    except NameError:
        raise Exception('Create a web view window first, before invoking this function')
    except KeyError:
        raise Exception('Cannot call function: No webview exists with uid: {}'.format(uid))


def destroy_window(uid='master'):
    """
    Destroy a web view window
    :param uid: uid of the target instance
    """
    try:
        _webview_ready.wait(5)
        gui.destroy_window(uid)
    except NameError:
        raise Exception('Create a web view window first, before invoking this function')
    except KeyError:
        raise Exception('Cannot call function: No webview exists with uid: {}'.format(uid))


def toggle_fullscreen(uid='master'):
    """
    Toggle fullscreen mode
    :param uid: uid of the target instance
    """
    try:
        _webview_ready.wait(5)
        gui.toggle_fullscreen(uid)
    except NameError:
        raise Exception('Create a web view window first, before invoking this function')
    except KeyError:
        raise Exception('Cannot call function: No webview exists with uid: {}'.format(uid))


def evaluate_js(script, uid='master'):
    """
    Evaluate given JavaScript code and return the result
    :param script: The JavaScript code to be evaluated
    :param uid: uid of the target instance
    :return: Return value of the evaluated code
    """
    try:
        _webview_ready.wait(5)
        return gui.evaluate_js(script, uid)
    except NameError:
        raise Exception('Create a web view window first, before invoking this function')
    except KeyError:
        raise Exception('Cannot call function: No webview exists with uid: {}'.format(uid))


def window_exists(uid='master'):
    """
    Check whether a webview with the given UID is up and running
    :param uid: uid of the target instance
    :return: True if the window exists, False otherwise
    """
    try:
        get_current_url(uid)
        return True
    except:
        return False


def _js_bridge_call(uid, api_instance, func_name, param):
    def _call():
        result = json.dumps(function(func_params))
        code = 'window.pywebview._returnValues["{0}"] = {{ isSet: true, value: {1}}}'.format(func_name,
                                                                                             _escape_line_breaks(
                                                                                                 result))
        evaluate_js(code, uid)

    function = getattr(api_instance, func_name, None)

    if function is not None:
        try:
            func_params = param if not param else json.loads(param)
            t = Thread(target=_call)
            t.start()
        except Exception as e:
            logger.exception('Error occurred while evaluating function {0}'.format(func_name))
    else:
        logger.error('Function {}() does not exist'.format(func_name))


def _parse_api_js(api_instance):
    base_dir = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(base_dir, 'js', 'npo.js')) as npo_js:
        js_code = npo_js.read()

    with open(os.path.join(base_dir, 'js', 'api.js')) as api_js:
        func_list = [str(f) for f in dir(api_instance) if callable(getattr(api_instance, f)) and str(f)[0] != '_']
        js_code += api_js.read() % func_list

    return js_code


def _escape_string(string):
    return string.replace('"', r'\"').replace('\n', r'\n').replace('\r', r'\\r')


def _escape_line_breaks(string):
    return string.replace('\\n', r'\\n').replace('\\r', r'\\r')


def _make_unicode(string):
    return string


def _transform_url(url):
    if url is None:
        return url
    if url.find(':') == -1:
        return 'file://' + os.path.abspath(url)
    else:
        return url


def _parse_file_type(file_type):
    '''
    :param file_type: file type string 'description (*.file_extension1;*.file_extension2)' as required by file filter in create_file_dialog
    :return: (description, file extensions) tuple
    '''
    valid_file_filter = r'^([\w ]+)\((\*(?:\.(?:\w+|\*))*(?:;\*\.\w+)*)\)$'
    match = re.search(valid_file_filter, file_type)

    if match:
        return match.group(1).rstrip(), match.group(2)
    else:
        raise ValueError('{0} is not a valid file filter'.format(file_type))
