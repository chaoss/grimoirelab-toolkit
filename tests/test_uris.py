#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#     Jesus M. Gonzalez-Barahona <jgb@gsyc.es>
#     Valerio Cosentino <valcos@bitergia.com>
#

import unittest

from grimoirelab_toolkit.uris import urijoin


class TestURIJoin(unittest.TestCase):
    """Unit tests for urijoin."""

    def test_join(self):
        """Test basic joins."""

        base_url = 'http://example.com/'
        base_url_alt = 'http://example.com'
        path0 = 'owner'
        path1 = 'repository'
        path2 = '/owner/repository'
        path3 = 'issues/8'

        url = urijoin(base_url, path0, path1)
        self.assertEqual(url, 'http://example.com/owner/repository')

        url = urijoin(base_url, path2)
        self.assertEqual(url, 'http://example.com/owner/repository')

        url = urijoin(base_url, path0, path1, path3)
        self.assertEqual(url, 'http://example.com/owner/repository/issues/8')

        url = urijoin(base_url_alt, path0, path1)
        self.assertEqual(url, 'http://example.com/owner/repository')

    def test_remove_trailing_backslash(self):
        """Test if trailing backslash is removed from URLs."""

        base_url = 'http://example.com/'
        path0 = 'repository/'

        url = urijoin(base_url)
        self.assertEqual(url, 'http://example.com')

        url = urijoin(base_url, path0)
        self.assertEqual(url, 'http://example.com/repository')

    def test_remove_double_slash(self):
        """Test if double backslash are removed from URIs."""

        base_url = 'http://example.com/'
        path0 = '/repository/'

        url = urijoin(base_url, path0)
        self.assertEqual(url, 'http://example.com/repository')

        base_uri = 'file:///tmp/'
        path0 = '/repository//'

        url = urijoin(base_uri, path0)
        self.assertEqual(url, 'file:///tmp/repository')


if __name__ == "__main__":
    unittest.main(warnings='ignore')
