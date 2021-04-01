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
#     Valerio Cosentino <valcos@bitergia.com>
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#     Jesus M. Gonzalez-Barahona <jgb@gsyc.es>
#

import datetime
import unittest

import dateutil

from grimoirelab_toolkit.datetime import (InvalidDateError,
                                          datetime_to_utc,
                                          str_to_datetime,
                                          unixtime_to_datetime,
                                          datetime_utcnow)


class TestInvalidDateError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = InvalidDateError(date='1900-13-01')
        self.assertEqual('1900-13-01 is not a valid date',
                         str(e))


class TestDatetimeToUTC(unittest.TestCase):
    """Unit tests for datetime_to_utc function."""

    def test_conversion(self):
        """Check if it converts some timestamps to timestamps with UTC+0."""

        date = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                 tzinfo=dateutil.tz.tzoffset(None, -21600))
        expected = datetime.datetime(2001, 12, 2, 5, 15, 32,
                                     tzinfo=dateutil.tz.tzutc())
        utc = datetime_to_utc(date)
        self.assertIsInstance(utc, datetime.datetime)
        self.assertEqual(utc, expected)

        date = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                 tzinfo=dateutil.tz.tzutc())
        expected = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                     tzinfo=dateutil.tz.tzutc())
        utc = datetime_to_utc(date)
        self.assertIsInstance(utc, datetime.datetime)
        self.assertEqual(utc, expected)

        date = datetime.datetime(2001, 12, 1, 23, 15, 32)
        expected = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                     tzinfo=dateutil.tz.tzutc())
        utc = datetime_to_utc(date)
        self.assertIsInstance(utc, datetime.datetime)
        self.assertEqual(utc, expected)

    def test_invalid_timezone(self):
        """ Check whether datetime converts to UTC when timezone invalid """

        date = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                 tzinfo=dateutil.tz.tzoffset(None, 93600))
        expected = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                     tzinfo=dateutil.tz.tzutc())
        utc = datetime_to_utc(date)
        self.assertIsInstance(utc, datetime.datetime)
        self.assertEqual(utc, expected)

    def test_invalid_datetime(self):
        """Check if it raises an exception on invalid instances."""

        self.assertRaises(InvalidDateError, datetime_to_utc, "2016-01-01 01:00:00 +0800")
        self.assertRaises(InvalidDateError, datetime_to_utc, None)
        self.assertRaises(InvalidDateError, datetime_to_utc, 1)


class TestStrToDatetime(unittest.TestCase):
    """Unit tests for str_to_datetime function."""

    def test_dates(self):
        """Check if it converts some dates to datetime objects."""

        date = str_to_datetime('2001-12-01')
        expected = datetime.datetime(2001, 12, 1, tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('13-01-2001')
        expected = datetime.datetime(2001, 1, 13, tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('12-01-01')
        expected = datetime.datetime(2001, 12, 1, tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('2001-12-01 23:15:32')
        expected = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('2001-12-01 23:15:32 -0600')
        expected = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                     tzinfo=dateutil.tz.tzoffset(None, -21600))
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('2001-12-01 23:15:32Z')
        expected = datetime.datetime(2001, 12, 1, 23, 15, 32,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Wed, 26 Oct 2005 15:20:32 -0100 (GMT+1)')
        expected = datetime.datetime(2005, 10, 26, 15, 20, 32,
                                     tzinfo=dateutil.tz.tzoffset(None, -3600))
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Wed, 22 Jul 2009 11:15:50 +0300 (FLE Daylight Time)')
        expected = datetime.datetime(2009, 7, 22, 11, 15, 50,
                                     tzinfo=dateutil.tz.tzoffset(None, 10800))
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Thu, 14 Aug 2008 02:07:59 +0200 CEST')
        expected = datetime.datetime(2008, 8, 14, 2, 7, 59,
                                     tzinfo=dateutil.tz.tzoffset(None, 7200))
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Tue, 06 Jun 2006 20:50:46 00200 (CEST)')
        expected = datetime.datetime(2006, 6, 6, 20, 50, 46,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Sat, 2 Aug 2008 04:18:59 +0500\x1b[D\x1b[D\x1b[D\x1b[-\x1b[C\x1b[C\x1b[C\x1b[C)')
        expected = datetime.datetime(2008, 8, 2, 4, 18, 59,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Thu, 14 Aug 2008 02:07:59 +0200 +0100')
        expected = datetime.datetime(2008, 8, 14, 2, 7, 59,
                                     tzinfo=dateutil.tz.tzoffset(None, 7200))
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        # This date is invalid because the timezone section.
        # Timezone will be removed, setting UTC as default
        date = str_to_datetime('2001-12-01 02:00 +08888')
        expected = datetime.datetime(2001, 12, 1, 2, 0, 0,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = str_to_datetime('Sun, 28 Feb 1999 19:17:37 -7700 (EST)')
        expected = datetime.datetime(1999, 2, 28, 19, 17, 37,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

    def test_invalid_unixtime_to_datetime(self):
        """Check whether it fails with an invalid unixtime."""

        self.assertRaises(InvalidDateError, unixtime_to_datetime, '2017-07-24')

    def test_invalid_date(self):
        """Check whether it fails with an invalid date."""

        self.assertRaises(InvalidDateError, str_to_datetime, '2001-13-01')
        self.assertRaises(InvalidDateError, str_to_datetime, '2001-04-31')

    def test_invalid_format(self):
        """Check whether it fails with invalid formats."""

        self.assertRaises(InvalidDateError, str_to_datetime, '2001-12-01mm')
        self.assertRaises(InvalidDateError, str_to_datetime, 'nodate')
        self.assertRaises(InvalidDateError, str_to_datetime, None)
        self.assertRaises(InvalidDateError, str_to_datetime, '')

    def test_datetime_utcnow(self):
        """Check whether timezone information is added"""

        now = datetime_utcnow()
        timezone = str(now.tzinfo)
        expected = "UTC+00:00"

        self.assertTrue(timezone, expected)


class TestUnixTimeToDatetime(unittest.TestCase):
    """Unit tests for str_to_datetime function."""

    def test_dates(self):
        """Check if it converts some timestamps to datetime objects."""

        date = unixtime_to_datetime(0)
        expected = datetime.datetime(1970, 1, 1, 0, 0, 0,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

        date = unixtime_to_datetime(1426868155.0)
        expected = datetime.datetime(2015, 3, 20, 16, 15, 55,
                                     tzinfo=dateutil.tz.tzutc())
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, expected)

    def test_invalid_format(self):
        """Check whether it fails with invalid formats."""

        self.assertRaises(InvalidDateError, str_to_datetime, '2001-12-01mm')
        self.assertRaises(InvalidDateError, str_to_datetime, 'nodate')
        self.assertRaises(InvalidDateError, str_to_datetime, None)
        self.assertRaises(InvalidDateError, str_to_datetime, '')


if __name__ == "__main__":
    unittest.main(warnings='ignore')
