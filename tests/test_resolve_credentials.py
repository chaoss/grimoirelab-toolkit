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

"""Tests for the resolve_credentials function."""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock hvac before importing anything from credential_manager,
# since the import chain may fail in environments where hvac is not installed.
sys.modules.setdefault('hvac', MagicMock())
sys.modules.setdefault('hvac.exceptions', MagicMock())

from grimoirelab_toolkit.credential_manager.credential_manager import (
    resolve_credentials,
    _extract_bitwarden_field,
    _extract_hashicorp_field,
)
from grimoirelab_toolkit.credential_manager.exceptions import CredentialNotFoundError


class TestExtractBitwardenField(unittest.TestCase):
    """Tests for _extract_bitwarden_field helper."""

    def test_extract_login_field(self):
        """Test extracting a field from the login section."""
        item = {
            'login': {'username': 'myuser', 'password': 'mypass'},
            'fields': [],
        }
        self.assertEqual(_extract_bitwarden_field(item, 'username'), 'myuser')
        self.assertEqual(_extract_bitwarden_field(item, 'password'), 'mypass')

    def test_extract_custom_field(self):
        """Test extracting a custom field from the fields array."""
        item = {
            'login': {},
            'fields': [
                {'name': 'api_key', 'value': 'tok123'},
                {'name': 'other', 'value': 'val'},
            ],
        }
        self.assertEqual(_extract_bitwarden_field(item, 'api_key'), 'tok123')

    def test_login_takes_priority_over_custom_field(self):
        """Test that login fields are checked before custom fields."""
        item = {
            'login': {'token': 'login_token'},
            'fields': [{'name': 'token', 'value': 'custom_token'}],
        }
        self.assertEqual(_extract_bitwarden_field(item, 'token'), 'login_token')

    def test_field_not_found(self):
        """Test that None is returned for missing fields."""
        item = {'login': {}, 'fields': []}
        self.assertIsNone(_extract_bitwarden_field(item, 'nonexistent'))

    def test_missing_login_key(self):
        """Test extraction when 'login' key is missing from item."""
        item = {'fields': [{'name': 'token', 'value': 'val'}]}
        self.assertEqual(_extract_bitwarden_field(item, 'token'), 'val')

    def test_missing_fields_key(self):
        """Test extraction when 'fields' key is missing from item."""
        item = {'login': {'username': 'user'}}
        self.assertEqual(_extract_bitwarden_field(item, 'username'), 'user')
        self.assertIsNone(_extract_bitwarden_field(item, 'nonexistent'))


class TestExtractHashicorpField(unittest.TestCase):
    """Tests for _extract_hashicorp_field helper."""

    def test_extract_field(self):
        """Test extracting a field from HashiCorp secret structure."""
        secret = {'data': {'data': {'api_key': 'hc_token', 'user': 'admin'}}}
        self.assertEqual(_extract_hashicorp_field(secret, 'api_key'), 'hc_token')
        self.assertEqual(_extract_hashicorp_field(secret, 'user'), 'admin')

    def test_field_not_found(self):
        """Test that None is returned for missing fields."""
        secret = {'data': {'data': {'api_key': 'tok'}}}
        self.assertIsNone(_extract_hashicorp_field(secret, 'nonexistent'))

    def test_missing_data_structure(self):
        """Test graceful handling of missing nested data keys."""
        self.assertIsNone(_extract_hashicorp_field({}, 'field'))
        self.assertIsNone(_extract_hashicorp_field({'data': {}}, 'field'))


class TestResolveCredentialsBitwarden(unittest.TestCase):
    """Tests for resolve_credentials with Bitwarden manager."""

    def setUp(self):
        self.manager_config = {
            'client_id': 'cid',
            'client_secret': 'csecret',
            'master_password': 'mpass',
        }

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_extract_login_fields(self, mock_factory):
        """Test resolving login fields (username, password) from Bitwarden."""
        mock_manager = MagicMock()
        mock_manager.get_secret.return_value = {
            'login': {'username': 'myuser', 'password': 'mypass'},
            'fields': [],
        }
        mock_factory.get_bitwarden_manager.return_value = mock_manager

        result = resolve_credentials(
            'bitwarden',
            self.manager_config,
            'my-item',
            {'username': 'user', 'password': 'password'},
        )

        self.assertEqual(result, {'user': 'myuser', 'password': 'mypass'})
        mock_manager.login.assert_called_once()
        mock_manager.logout.assert_called_once()

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_extract_custom_fields(self, mock_factory):
        """Test resolving custom fields (token) from Bitwarden."""
        mock_manager = MagicMock()
        mock_manager.get_secret.return_value = {
            'login': {},
            'fields': [{'name': 'api_key', 'value': 'tok123'}],
        }
        mock_factory.get_bitwarden_manager.return_value = mock_manager

        result = resolve_credentials(
            'bitwarden',
            self.manager_config,
            'my-item',
            {'api_key': 'api_token'},
        )

        self.assertEqual(result, {'api_token': 'tok123'})

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_missing_field_omitted(self, mock_factory):
        """Test that missing fields are omitted from result."""
        mock_manager = MagicMock()
        mock_manager.get_secret.return_value = {
            'login': {'username': 'myuser'},
            'fields': [],
        }
        mock_factory.get_bitwarden_manager.return_value = mock_manager

        result = resolve_credentials(
            'bitwarden',
            self.manager_config,
            'my-item',
            {'username': 'user', 'nonexistent': 'password'},
        )

        self.assertEqual(result, {'user': 'myuser'})

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_logout_called_on_failure(self, mock_factory):
        """Test that logout is called even when get_secret fails."""
        mock_manager = MagicMock()
        mock_manager.get_secret.side_effect = CredentialNotFoundError("not found")
        mock_factory.get_bitwarden_manager.return_value = mock_manager

        with self.assertRaises(CredentialNotFoundError):
            resolve_credentials(
                'bitwarden',
                self.manager_config,
                'my-item',
                {'username': 'user'},
            )

        mock_manager.login.assert_called_once()
        mock_manager.logout.assert_called_once()


class TestResolveCredentialsHashicorp(unittest.TestCase):
    """Tests for resolve_credentials with HashiCorp manager."""

    def setUp(self):
        self.manager_config = {
            'vault_url': 'https://vault.example.com',
            'token': 'hvs.token123',
            'certificate': '/path/to/cert.pem',
        }

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_extract_fields(self, mock_factory):
        """Test resolving fields from HashiCorp Vault."""
        mock_manager = MagicMock()
        mock_manager.get_secret.return_value = {
            'data': {'data': {'api_key': 'hc_token', 'user': 'admin'}},
        }
        mock_factory.get_hashicorp_manager.return_value = mock_manager

        result = resolve_credentials(
            'hashicorp',
            self.manager_config,
            'secret/my-service',
            {'api_key': 'api_token', 'user': 'user'},
        )

        self.assertEqual(result, {'api_token': 'hc_token', 'user': 'admin'})

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_missing_field_omitted(self, mock_factory):
        """Test that missing fields are omitted from result."""
        mock_manager = MagicMock()
        mock_manager.get_secret.return_value = {
            'data': {'data': {'api_key': 'tok'}},
        }
        mock_factory.get_hashicorp_manager.return_value = mock_manager

        result = resolve_credentials(
            'hashicorp',
            self.manager_config,
            'secret/path',
            {'api_key': 'api_token', 'missing': 'password'},
        )

        self.assertEqual(result, {'api_token': 'tok'})


class TestResolveCredentialsGeneral(unittest.TestCase):
    """Tests for general resolve_credentials behavior."""

    def test_unsupported_manager_type(self):
        """Test that unsupported manager type raises ValueError."""
        with self.assertRaises(ValueError):
            resolve_credentials('unknown', {}, 'item', {'f': 'p'})

    def test_empty_item_name(self):
        """Test that empty item_name raises ValueError."""
        with self.assertRaises(ValueError):
            resolve_credentials('bitwarden', {}, '', {'f': 'p'})

    def test_empty_field_mapping(self):
        """Test that empty field_mapping returns empty dict without calling manager."""
        result = resolve_credentials('bitwarden', {}, 'item', {})
        self.assertEqual(result, {})

    @patch('grimoirelab_toolkit.credential_manager.credential_manager.SecretsManagerFactory')
    def test_item_not_found_propagates(self, mock_factory):
        """Test that CredentialNotFoundError from manager propagates."""
        mock_manager = MagicMock()
        mock_manager.get_secret.side_effect = CredentialNotFoundError("not found")
        mock_factory.get_hashicorp_manager.return_value = mock_manager

        with self.assertRaises(CredentialNotFoundError):
            resolve_credentials(
                'hashicorp',
                {'vault_url': 'url', 'token': 'tok'},
                'missing/path',
                {'field': 'param'},
            )


if __name__ == '__main__':
    unittest.main()
