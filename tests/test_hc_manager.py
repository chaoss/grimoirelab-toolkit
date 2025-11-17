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
# Author:
#     Alberto Ferrer Sánchez (alberefe@gmail.com)
#

import unittest
from unittest.mock import patch
import hvac.exceptions

from grimoirelab_toolkit.credential_manager.hc_manager import HashicorpManager
from grimoirelab_toolkit.credential_manager.exceptions import (
    CredentialNotFoundError,
    HashicorpVaultError,
)


class TestHashicorpManager(unittest.TestCase):
    """Tests for HashicorpManager class."""

    def setUp(self):
        """Set up common test fixtures."""
        self.vault_url = "http://vault-url"
        self.token = "test-token"
        self.certificate = "test-certificate"

        self.mock_secret_response = {
            "auth": None,
            "data": {
                "data": {
                    "password": "test_pass",
                    "username": "test_user",
                    "api_key": "test_key",
                },
                "metadata": {
                    "created_time": "2024-11-23T12:20:59.985132927Z",
                    "custom_metadata": None,
                    "deletion_time": "",
                    "destroyed": False,
                    "version": 1,
                },
            },
            "lease_duration": 0,
            "lease_id": "",
            "mount_type": "kv",
            "renewable": False,
            "request_id": "d09e2bb5-00ee-576b-6078-5d291d35ccc3",
            "warnings": None,
            "wrap_info": None,
        }

    @patch("hvac.Client")
    def test_initialization_success(self, mock_hvac_client):
        """Test successful initialization with valid credentials."""
        mock_instance = mock_hvac_client.return_value

        manager = HashicorpManager(self.vault_url, self.token, self.certificate)

        self.assertIsNotNone(manager.client)
        mock_hvac_client.assert_called_once_with(
            url=self.vault_url, token=self.token, verify=self.certificate
        )

    @patch("hvac.Client")
    def test_initialization_failure(self, mock_hvac_client):
        """Test initialization fails when connection to Vault fails."""
        mock_hvac_client.side_effect = hvac.exceptions.VaultError("Connection failed")

        with self.assertRaises(hvac.exceptions.VaultError) as context:
            HashicorpManager(self.vault_url, self.token, self.certificate)

        self.assertIn("Connection failed", str(context.exception))

    @patch("hvac.Client")
    def test_get_secret_success(self, mock_hvac_client):
        """Test successful secret retrieval."""
        mock_instance = mock_hvac_client.return_value
        mock_instance.secrets.kv.read_secret.return_value = self.mock_secret_response

        manager = HashicorpManager(self.vault_url, self.token, self.certificate)
        result = manager.get_secret("test_service")

        # Verify it returns the full secret object
        self.assertIsInstance(result, dict)
        self.assertEqual(result, self.mock_secret_response)
        self.assertEqual(result["data"]["data"]["api_key"], "test_key")
        mock_instance.secrets.kv.read_secret.assert_called_once_with(
            path="test_service"
        )

    @patch("hvac.Client")
    def test_get_secret_not_found(self, mock_hvac_client):
        """Test get_secret raises error when secret path not found."""
        mock_instance = mock_hvac_client.return_value
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.InvalidPath()

        manager = HashicorpManager(self.vault_url, self.token, self.certificate)

        with self.assertRaises(CredentialNotFoundError) as context:
            manager.get_secret("nonexistent_service")

        self.assertIn("nonexistent_service", str(context.exception))
        self.assertIn("not found", str(context.exception))

    @patch("hvac.Client")
    def test_get_secret_permission_denied(self, mock_hvac_client):
        """Test get_secret raises error when access is forbidden."""
        mock_instance = mock_hvac_client.return_value
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.Forbidden()

        manager = HashicorpManager(self.vault_url, self.token, self.certificate)

        with self.assertRaises(HashicorpVaultError) as context:
            manager.get_secret("test_service")

        self.assertIn("Vault operation failed", str(context.exception))

    @patch("hvac.Client")
    def test_vault_connection_error(self, mock_hvac_client):
        """Test get_secret raises error when Vault is down or sealed."""
        mock_instance = mock_hvac_client.return_value
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultDown(
            "Vault is sealed"
        )

        manager = HashicorpManager(self.vault_url, self.token, self.certificate)

        with self.assertRaises(HashicorpVaultError) as context:
            manager.get_secret("test_service")

        self.assertIn("Vault operation failed", str(context.exception))


if __name__ == "__main__":
    unittest.main(warnings="ignore")
