# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Bitergia
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
#

import sys
import unittest

import pkg_resources

sys.path.insert(0, '..')
pkg_resources.declare_namespace('grimoirelab.toolkit')

from grimoirelab.toolkit.introspect import (inspect_signature_parameters,
                                            find_signature_parameters)


class FakeCallable:
    """Fake class for testing introspection."""

    def __init__(self, *args, **kwargs):
        pass

    def test(self, a, b, c=None):
        pass

    @classmethod
    def class_test(cls, a, b):
        pass

    @staticmethod
    def static_test(a, b):
        pass


class TestInspectSignatureParameters(unittest.TestCase):
    """Unit tests for inspect_signature_parameters."""

    def test_inspect(self):
        """Check the parameters from a callable."""

        expected = ['args', 'kwargs']
        params = inspect_signature_parameters(FakeCallable)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['self', 'args', 'kwargs']
        params = inspect_signature_parameters(FakeCallable.__init__)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['self', 'a', 'b', 'c']
        params = inspect_signature_parameters(FakeCallable.test)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['a', 'b']
        params = inspect_signature_parameters(FakeCallable.class_test)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['a', 'b']
        params = inspect_signature_parameters(FakeCallable.static_test)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

    def test_inspect_excluding_parameters(self):
        """Check the parameters from a callable when some are excluded."""

        excluded = ['self', 'cls', 'a']

        expected = ['args', 'kwargs']
        params = inspect_signature_parameters(FakeCallable,
                                              excluded=excluded)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['b', 'c']
        params = inspect_signature_parameters(FakeCallable.test,
                                              excluded=excluded)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['b']
        params = inspect_signature_parameters(FakeCallable.class_test,
                                              excluded=excluded)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)

        expected = ['b']
        params = inspect_signature_parameters(FakeCallable.static_test,
                                              excluded=excluded)
        params = [p.name for p in params]
        self.assertListEqual(params, expected)


class TestFindSignatureParameters(unittest.TestCase):
    """Unit tests for find_signature_parameters."""

    def test_find_parameters(self):
        """Test if a list of parameters is generated."""

        expected = {'a': 1, 'b': 2, 'c': 3}
        params = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        found = find_signature_parameters(FakeCallable.test, params)
        self.assertDictEqual(found, expected)

        expected = {'a': 1, 'b': 2}
        params = {'a': 1, 'b': 2, 'd': 3}
        found = find_signature_parameters(FakeCallable.test, params)
        self.assertDictEqual(found, expected)

    def test_find_excluding_parameters(self):
        """Test if a list of parameters is generated excluding some."""

        expected = {'b': 2, 'c': 3}
        params = {'a': 1, 'b': 2, 'c': 3}
        excluded = ('self', 'a')
        found = find_signature_parameters(FakeCallable.test, params,
                                          excluded=excluded)
        self.assertDictEqual(found, expected)

    def test_attribute_error(self):
        """Test if it raises an exception for not found parameters."""

        with self.assertRaises(AttributeError) as e:
            params = {'a': 1, 'd': 3}
            _ = find_signature_parameters(FakeCallable.test, params)

        self.assertEqual(e.exception.args[1], 'b')


if __name__ == "__main__":
    unittest.main(warnings='ignore')
