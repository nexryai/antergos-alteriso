#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webcam_widget.py
#
# Copyright © 2013-2018 Antergos
#
# This file is part of Cnchi.
#
# Cnchi is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Cnchi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# The following additional terms are in effect as per Section 7 of the license:
#
# The preservation of all legal notices and author attributions in
# the material or in the Appropriate Legal Notices displayed
# by works containing it is required.
#
# You should have received a copy of the GNU General Public License
# along with Cnchi; If not, see <http://www.gnu.org/licenses/>.

""" Widget that shows a web camera feed """

import logging
import os

import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gst, Gtk

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
gi.require_version('GstVideo', '1.0')
from gi.repository import GdkX11, GstVideo


class WebcamWidget(Gtk.DrawingArea):
    """ Webcam widget """
    __gtype_name__ = 'WebcamWidget'

    def __init__(self, width=160, height=90):

        Gtk.DrawingArea.__init__(self)

        self.pipeline = None
        self.xid = None
        self.bus = None
        self.error = False

        if not os.path.exists("/dev/video0"):
            logging.warning("Cannot find any camera. Camera widget won't be used")
            self.error = True
            self.destroy()
            return

        self.set_size_request(width, height)

        # Initialize GStreamer
        Gst.init(None)

        self.create_video_pipeline(width, height)

        self.connect('destroy', self.on_destroy)

    def create_video_pipeline(self, width, height):
        """ Create GStreamer pipeline """

        # Create pipeline
        self.pipeline = Gst.Pipeline.new()

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)
        # This is needed to make the video output in our DrawingArea:
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)

        # Create GStreamer elements
        self.source = Gst.ElementFactory.make('autovideosrc', 'source')
        self.sink = Gst.ElementFactory.make('autovideosink', 'sink')

        if self.source and self.sink:
            #fmt_str = 'video/x-raw, format=(string)YV12, '
            fmt_str = 'video/x-raw, '
            fmt_str += 'width=(int){0}, height=(int){1}, '.format(width, height)
            fmt_str += 'pixel-aspect-ratio=(fraction)1/1, '
            fmt_str += 'interlace-mode=(string)progressive, '
            fmt_str += 'framerate=(fraction){ 30/1, 24/1, 20/1, 15/1, 10/1, 15/2, 5/1 }'
            caps = Gst.caps_from_string(fmt_str)

            # Add elements to the pipeline
            self.pipeline.add(self.source)
            self.pipeline.add(self.sink)
            self.source.link_filtered(self.sink, caps)

            logging.debug("Camera found. Video pipeline created.")
        else:
            logging.debug("Cannot initialize camera.")
            self.error = True

    def show_all(self):
        """ You need to get the XID after window.show_all().  You shouldn't get it
        in the on_sync_message() handler because threading issues will cause
        segfaults there. """
        self.xid = self.get_property('window').get_xid()
        if self.pipeline:
            # Start playing
            self.pipeline.set_state(Gst.State.PLAYING)

    def on_destroy(self, _data):
        """ Widget is destroyed. Stop playing """
        if self.pipeline:
            # Stop playing
            self.pipeline.set_state(Gst.State.NULL)
        self.destroy()

    def on_sync_message(self, _bus, msg):
        """ This is needed to make the video output in our DrawingArea """
        if msg.get_structure().get_name() == 'prepare-window-handle':
            msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.xid)

    @staticmethod
    def on_error(_bus, msg):
        """ A gst error has occurred """
        logging.error(msg.parse_error())

    def clicked(self, _event_box, _event_button):
        """ User clicks on camera widget """
        pass

GObject.type_register(WebcamWidget)


def test_module():
    """ function to test this module """
    window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    window.set_title("Webcam test")
    window.set_default_size(160, 90)
    window.connect("destroy", Gtk.main_quit, "WM destroy")
    vbox = Gtk.VBox()
    window.add(vbox)

    overlay = Gtk.Overlay.new()
    overlay.show()
    webcam = WebcamWidget()

    event_box = Gtk.EventBox.new()
    event_box.connect(
        'button-press-event',
        webcam.clicked)

    overlay.add_overlay(event_box)
    event_box.add(webcam)

    webcam.set_halign(Gtk.Align.START)
    webcam.set_valign(Gtk.Align.START)

    vbox.add(overlay)
    window.show_all()
    webcam.show_all()
    GObject.threads_init()
    Gtk.main()

if __name__ == '__main__':
    test_module()
