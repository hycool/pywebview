#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import time
import qt5_cef.qt as gui
from threading import Event, Thread
from uuid import uuid4

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

OPEN_DIALOG = 10
FOLDER_DIALOG = 20
SAVE_DIALOG = 30

web_view_ready = Event()


def generate_guid():
    return 'child_' + uuid4().hex[:8]


def load_url(url='', full_screen=False, width=800, height=600):
    def new_web_view():
        uid = generate_guid()
        create_window(
            uid=uid,
            url=url,
            title='FC-POS',
            width=width,
            height=height,
            context_menu=True,
            full_screen=full_screen
        )
    new_web_view_thread = Thread(target=new_web_view)
    new_web_view_thread.start()


def create_window(
        uid='master',
        title='',
        url=None,
        width=800,
        height=600,
        resizable=True,
        full_screen=False,
        min_size=(200, 100),
        background_color='#FFFFFF',
        context_menu=False):
    web_view_ready.clear()
    gui.create_window(uid, title, url, width, height, resizable, full_screen, min_size,
                      background_color, web_view_ready, context_menu)
