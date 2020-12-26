#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  credentials.py
#
#  Copyright © 2013-2017 Antergos
#
#  This file is part of Cnchi.
#
#  Cnchi is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  Cnchi is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The following additional terms are in effect as per Section 7 of the license:
#
#  The preservation of all legal notices and author attributions in
#  the material or in the Appropriate Legal Notices displayed
#  by works containing it is required.
#
#  You should have received a copy of the GNU General Public License
#  along with Cnchi; If not, see <http://www.gnu.org/licenses/>.

""" Lembrame credentials store module """

class LembrameCredentials(object):
    """ Lembrame credentials store class """

    user_id = False
    upload_code = False

    def __init__(self, user_id, upload_code):
        """ Store user id and code """
        self.user_id = user_id
        self.upload_code = upload_code

    def get_user_id(self):
        """ Returns user id """
        return self.user_id

    def get_upload_code(self):
        """ Returns user code """
        return self.upload_code
