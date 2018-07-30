#!/usr/bin/python
# -*- coding: utf-8 -*-

import qt5_cef.qt as gui
import qt5_cef.constant as constant
from threading import Event, Thread
from uuid import uuid4

default_window_width = constant.default_window_width
default_window_height = constant.default_window_height
default_window_title = constant.default_window_title
min_window_width = constant.min_window_width
min_window_height = constant.min_window_height
web_view_ready = Event()


def generate_guid():
    return 'child_' + uuid4().hex[:8]


def create_main_window_sub_thread(url='', full_screen=False, width=default_window_width, height=default_window_height,
                                  context_menu=True):
    def new_web_view():
        uid = generate_guid()
        create_window(
            uid=uid,
            url=url,
            title=default_window_title,
            width=width,
            height=height,
            context_menu=context_menu,
            full_screen=full_screen
        )

    new_web_view_thread = Thread(target=new_web_view)
    new_web_view_thread.start()


def create_window(title=default_window_title, url=None, uid='master', width=default_window_height,
                  height=default_window_height, resizable=True,
                  full_screen=False,
                  min_size=(min_window_width, min_window_height), background_color='#FFFFFF', context_menu=False,
                  url_type='document'):
    web_view_ready.clear()
    format_url = url
    if url_type == 'string':
        format_url = gui.html_to_data_uri(url)
    gui.launch_main_window(uid, title, url=format_url, width=width, height=height, resizable=resizable,
                           full_screen=full_screen, min_size=min_size,
                           background_color=background_color, web_view_ready=web_view_ready, context_menu=context_menu)


def evaluate_js(script, uid='master'):
    gui.execute_javascript(script, uid)
