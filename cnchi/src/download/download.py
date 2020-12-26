#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# download.py
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

""" Module to download packages """

import os
import logging

import pyalpm

try:
    import pacman.pac as pac
    import download.metalink as ml
    import download.download_requests as download_requests
except ModuleNotFoundError:
    import sys
    CNCHI_PATH = "/usr/share/cnchi"
    sys.path.append(CNCHI_PATH)
    sys.path.append(os.path.join(CNCHI_PATH, "src"))
    import pacman.pac as pac
    import metalink as ml
    import download_requests

from misc.events import Events
import misc.extra as misc

# When testing, no _() is available
try:
    _("")
except NameError as err:
    def _(message):
        return message

class DownloadPackages():
    """ Class to download packages. This class tries to previously download
        all necessary packages for  Antergos installation using requests. """

    def __init__(self, package_names, pacman_conf, settings=None, callback_queue=None):
        """ Initialize DownloadPackages class. Gets default configuration """

        self.package_names = package_names

        self.pacman_conf_file = pacman_conf['file']
        self.pacman_cache_dir = pacman_conf['cache']

        self.settings = settings
        if self.settings:
            self.xz_cache_dirs = self.settings.get('xz_cache')
        else:
            self.xz_cache_dirs = []

        self.events = Events(callback_queue)

        # Create pacman cache dir (it's ok if it already exists)
        os.makedirs(self.pacman_cache_dir, mode=0o755, exist_ok=True)

        # Stores last issued event for each event type
        # (to prevent repeating events)
        self.last_event = {}

        # List of packages' metalinks
        self.metalinks = None

    def start_download(self, metalinks=None):
        """ Begin download """
        if metalinks:
            self.metalinks = metalinks

        # Create downloads list from package list
        if self.metalinks is None:
            self.create_metalinks_list()

        if self.metalinks is None:
            # Still None? Error!
            txt = _("Can't create download package list.")
            raise misc.InstallError(txt)

        proxies = self.settings.get("proxies")

        download = download_requests.Download(
            self.pacman_cache_dir,
            self.xz_cache_dirs,
            self.events.queue,
            proxies)

        if not download.start(self.metalinks):
            # When we can't download (even one package), we stop right here
            txt = _("Can't download needed packages. Cnchi can't continue.")
            raise misc.InstallError(txt)

    def url_sort_helper(self, url):
        """ helper method for sorting mirror urls """
        if not url:
            return 9999
        # Use the mirrorlist we created earlier to determine a url's priority
        ranked = self.settings.get('rankmirrors_result')
        # Use the first part of the URL to find its position in the ranked mirror list
        partial = '/'.join(url.split('/')[:3])
        position = [i for i, s in enumerate(ranked) if partial in s] or [9999]
        return position[0]

    def add_metalink_info(self, metalink):
        """ Adds metalink info to metalinks list """
        # Get metalink info
        metalink_info = ml.get_info(metalink)

        # Update downloads list with the new info from
        # the processed metalink
        for key in metalink_info:
            if key not in self.metalinks:
                self.metalinks[key] = metalink_info[key]
                urls = metalink_info[key]['urls']
                if self.settings:
                    # Sort urls based on the rankmirrors mirrorlist
                    sorted_urls = sorted(urls, key=self.url_sort_helper)
                    self.metalinks[key]['urls'] = sorted_urls
                else:
                    # When testing, settings is not available
                    self.metalinks[key]['urls'] = urls

    @misc.raise_privileges
    def create_metalinks_list(self):
        """ Creates a downloads list (metalinks) from the package list """

        self.events.add('percent', 0)
        self.events.add(
            'info', _('Creating the list of packages to download...'))
        processed_packages = 0
        total_packages = len(self.package_names)

        self.metalinks = {}

        try:
            pacman = pac.Pac(
                conf_path=self.pacman_conf_file,
                callback_queue=self.events.queue)
            if pacman is None:
                return False
        except pyalpm.error as ex:
            self.metalinks = None
            template = "Can't initialize pyalpm. " \
                "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logging.error(message)
            return False

        try:
            for package_name in self.package_names:
                metalink = ml.create(pacman, package_name,
                                     self.pacman_conf_file)
                if metalink is None:
                    txt = "Error creating metalink for package %s. Installation will stop"
                    logging.error(txt, package_name)
                    txt = _("Error creating metalink for package {}. "
                            "Installation will stop").format(package_name)
                    raise misc.InstallError(txt)

                self.add_metalink_info(metalink)

                # Show progress to the user
                processed_packages += 1
                percent = round(float(processed_packages / total_packages), 2)
                self.events.add('percent', percent)

            pacman.release()
            del pacman
        except (KeyError, pyalpm.error) as ex:
            template = "Can't create download set. " \
                "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logging.error(message)
            self.metalinks = None
            return False

        # Overwrite last event (to clean up the last message)
        self.events.add('info', "")
        return True


def test():
    """ Test function """
    import gettext

    _ = gettext.gettext

    formatter = logging.Formatter(
        '[%(asctime)s] [%(module)s] %(levelname)s: %(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    pacman_conf = {}
    pacman_conf['file'] = '/etc/pacman.conf'
    pacman_conf['cache'] = '/tmp'

    download_packages = DownloadPackages(
        package_names=['ipw2200-fw'],
        pacman_conf=pacman_conf,
        settings={},
        callback_queue=None)
    download_packages.start_download()


if __name__ == '__main__':
    test()
