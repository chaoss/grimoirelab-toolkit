# -*- coding: utf-8 -*-
#
# Copyright (C) Grimoirelab Contributors
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

"""Tests for resolve_credentials and extract_field methods."""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock hvac before importing anything from credential_manager,
# since the import chain may fail in environments where hvac is not installed.
sys.modules.setdefault('hvac', MagicMock())
sys.modules.setdefault('hvac.exceptions', MagicMock())

from grimoirelab_toolkit.credential_manager.bw_manager import BitwardenManager
from grimoirelab_toolkit.credential_manager.hc_manager import HashicorpManager
from grimoirelab_toolkit.credential_manager.credential_manager import CredentialManager
from grimoirelab_toolkit.credential_manager.exceptions import CredentialNotFoundError


class TestBitwardenExtractField(unittest.TestCase):
    """Tests for BitwardenManager.extract_field."""

    def setUp(self):
        with patch.object(BitwardenManager, '__init__', lambda self, *a, **kw: None):
            self.manager = BitwardenManager()

    def test_extract_login_field(self):
        """Test extracting a field from the login section."""
        item = {
            'login': {'username': 'myuser', 'password': 'mypass'},
            'fields': [],
        }
        self.assertEqual(self.manager.extract_field(item, 'username'), 'myuser')
        self.assertEqual(self.manager.extract_field(item, 'password'), 'mypass')

    def test_extract_custom_field(self):
        """Test extracting a custom field from the fields array."""
        item = {
            'login': {},
            'fields': [
                {'name': 'api_key', 'value': 'tok123'},
                {'name': 'other', 'value': 'val'},
            ],
        }
        self.assertEqual(self.manager.extract_field(item, 'api_key'), 'tok123')

    def test_login_takes_priority_over_custom_field(self):
        """Test that login fields are checked before custom fields."""
        item = {
            'login': {'token': 'login_token'},
            'fields': [{'name': 'token', 'value': 'custom_token'}],
        }
        self.assertEqual(self.manager.extract_field(item, 'token'), 'login_token')

    def test_field_not_found(self):
        """Test that None is returned for missing fields."""
        item = {'login': {}, 'fields': []}
        self.assertIsNone(self.manager.extract_field(item, 'nonexistent'))

    def test_missing_login_key(self):
        """Test extraction when 'login' key is missing from item."""
        item = {'fields': [{'name': 'token', 'value': 'val'}]}
        self.assertEqual(self.manager.extract_field(item, 'token'), 'val')

    def test_missing_fields_key(self):
        """Test extraction when 'fields' key is missing from item."""
        item = {'login': {'username': 'user'}}
        self.assertEqual(self.manager.extract_field(item, 'username'), 'user')
        self.assertIsNone(self.manager.extract_field(item, 'nonexistent'))


class TestHashicorpExtractField(unittest.TestCase):
    """Tests for HashicorpManager.extract_field."""

    def setUp(self):
        with patch.object(HashicorpManager, '__init__', lambda self, *a, **kw: None):
            self.manager = HashicorpManager()

    def test_extract_field(self):
        """Test extracting a field from HashiCorp secret structure."""
        secret = {'data': {'data': {'api_key': 'hc_token', 'user': 'admin'}}}
        self.assertEqual(self.manager.extract_field(secret, 'api_key'), 'hc_token')
        self.assertEqual(self.manager.extract_field(secret, 'user'), 'admin')

    def test_field_not_found(self):
        """Test that None is returned for missing fields."""
        secret = {'data': {'data': {'api_key': 'tok'}}}
        self.assertIsNone(self.manager.extract_field(secret, 'nonexistent'))

    def test_missing_data_structure(self):
        """Test graceful handling of missing nested data keys."""
        self.assertIsNone(self.manager.extract_field({}, 'field'))
        self.assertIsNone(self.manager.extract_field({'data': {}}, 'field'))


class TestResolveCredentialsBitwarden(unittest.TestCase):
    """Tests for resolve_credentials on BitwardenManager."""

    def setUp(self):
        with patch.object(BitwardenManager, '__init__', lambda self, *a, **kw: None):
            self.manager = BitwardenManager()

    @patch.object(BitwardenManager, 'logout')
    @patch.object(BitwardenManager, 'get_secret')
    @patch.object(BitwardenManager, 'login')
    def test_extract_login_fields(self, mock_login, mock_get_secret, mock_logout):
        """Test resolving login fields (username, password) from Bitwarden."""
        mock_get_secret.return_value = {
            'login': {'username': 'myuser', 'password': 'mypass'},
            'fields': [],
        }

        result = self.manager.resolve_credentials('my-item', ['username', 'password'])

        self.assertEqual(result, {'username': 'myuser', 'password': 'mypass'})
        mock_login.assert_called_once()
        mock_logout.assert_called_once()

    @patch.object(BitwardenManager, 'logout')
    @patch.object(BitwardenManager, 'get_secret')
    @patch.object(BitwardenManager, 'login')
    def test_extract_custom_fields(self, mock_login, mock_get_secret, mock_logout):
        """Test resolving custom fields (token) from Bitwarden."""
        mock_get_secret.return_value = {
            'login': {},
            'fields': [{'name': 'api_key', 'value': 'tok123'}],
        }

        result = self.manager.resolve_credentials('my-item', ['api_key'])

        self.assertEqual(result, {'api_key': 'tok123'})

    @patch.object(BitwardenManager, 'logout')
    @patch.object(BitwardenManager, 'get_secret')
    @patch.object(BitwardenManager, 'login')
    def test_missing_field_omitted(self, mock_login, mock_get_secret, mock_logout):
        """Test that missing fields are omitted from result."""
        mock_get_secret.return_value = {
            'login': {'username': 'myuser'},
            'fields': [],
        }

        result = self.manager.resolve_credentials('my-item', ['username', 'nonexistent'])

        self.assertEqual(result, {'username': 'myuser'})

    @patch.object(BitwardenManager, 'logout')
    @patch.object(BitwardenManager, 'get_secret')
    @patch.object(BitwardenManager, 'login')
    def test_logout_called_on_failure(self, mock_login, mock_get_secret, mock_logout):
        """Test that logout is called even when get_secret fails."""
        mock_get_secret.side_effect = CredentialNotFoundError("not found")

        with self.assertRaises(CredentialNotFoundError):
            self.manager.resolve_credentials('my-item', ['username'])

        mock_login.assert_called_once()
        mock_logout.assert_called_once()


class TestResolveCredentialsHashicorp(unittest.TestCase):
    """Tests for resolve_credentials on HashicorpManager."""

    def setUp(self):
        with patch.object(HashicorpManager, '__init__', lambda self, *a, **kw: None):
            self.manager = HashicorpManager()

    @patch.object(HashicorpManager, 'get_secret')
    def test_extract_fields(self, mock_get_secret):
        """Test resolving fields from HashiCorp Vault."""
        mock_get_secret.return_value = {
            'data': {'data': {'api_key': 'hc_token', 'user': 'admin'}},
        }

        result = self.manager.resolve_credentials(
            'secret/my-service', ['api_key', 'user']
        )

        self.assertEqual(result, {'api_key': 'hc_token', 'user': 'admin'})

    @patch.object(HashicorpManager, 'get_secret')
    def test_missing_field_omitted(self, mock_get_secret):
        """Test that missing fields are omitted from result."""
        mock_get_secret.return_value = {
            'data': {'data': {'api_key': 'tok'}},
        }

        result = self.manager.resolve_credentials(
            'secret/path', ['api_key', 'missing']
        )

        self.assertEqual(result, {'api_key': 'tok'})

    @patch.object(HashicorpManager, 'get_secret')
    def test_item_not_found_propagates(self, mock_get_secret):
        """Test that CredentialNotFoundError from manager propagates."""
        mock_get_secret.side_effect = CredentialNotFoundError("not found")

        with self.assertRaises(CredentialNotFoundError):
            self.manager.resolve_credentials('missing/path', ['field'])


class TestResolveCredentialsGeneral(unittest.TestCase):
    """Tests for general resolve_credentials behavior."""

    def _make_stub_manager(self):
        """Create a minimal concrete CredentialManager for testing."""

        class StubManager(CredentialManager):
            def get_secret(self, item_name):
                return {}

            def extract_field(self, secret, field_name):
                return None

        return StubManager()

    def test_empty_item_name(self):
        """Test that empty item_name raises ValueError."""
        manager = self._make_stub_manager()
        with self.assertRaises(ValueError):
            manager.resolve_credentials('', ['field'])

    def test_empty_field_names(self):
        """Test that empty field_names returns empty dict without calling manager."""
        manager = self._make_stub_manager()
        result = manager.resolve_credentials('item', [])
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
