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
from grimoirelab_toolkit.credential_manager.exceptions import ConnectionError, SecretNotFoundError, HashicorpVaultError


class TestHashicorpManager(unittest.TestCase):
    """HashicorpManager unit tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_secret_response = {
            "auth": None,
            "data": {
                "data": {"password": "test_pass", "username": "test_user", "api_key": "test_key"},
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
    def test_initialization(self, mock_hvac_client):
        """Test successful initialization of HashicorpManager"""
        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

        self.assertIsNotNone(manager.client)
        mock_hvac_client.assert_called_once_with(url="http://vault-url", token="test-token", verify="test-certificate")
        self.assertTrue(manager.client.sys.is_initialized())
        self.assertTrue(manager.client.is_authenticated())

    @patch("hvac.Client")
    def test_initialization_failure(self, mock_hvac_client):
        """Test handling of initialization failures"""

        mock_hvac_client.side_effect = hvac.exceptions.VaultError("Connection failed")

        with self.assertRaises(ConnectionError) as context:
            HashicorpManager("http://vault-url", "test-token", "test-certificate")
        self.assertIn("Failed to initialize Vault client", str(context.exception))

    @patch("hvac.Client")
    def test_get_secret_success(self, mock_hvac_client):
        """Test successful secret retrieval"""
        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.read_secret.return_value = self.mock_secret_response

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
        result = manager.get_secret("test_service", "api_key")

        self.assertEqual(result, "test_key")
        mock_instance.secrets.kv.read_secret.assert_called_once_with(path="test_service")

    @patch("hvac.Client")
    def test_get_secret_not_found(self, mock_hvac_client):
        """Test handling of non existant secrets"""

        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.InvalidPath()

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

        with self.assertRaises(SecretNotFoundError):
            manager.get_secret("test_service", "nonexistent")

    @patch("hvac.Client")
    def test_get_secret_permission_denied(self, mock_hvac_client):
        """Test handling of permission denied errors"""

        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.Forbidden()

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

        with self.assertRaises(HashicorpVaultError):
            manager.get_secret("test_service", "api_key")

    @patch("hvac.Client")
    def test_retrieve_credentials_success(self, mock_hvac_client):
        """Test successful retrieval of raw credentials"""
        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.read_secret.return_value = self.mock_secret_response

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
        result = manager._retrieve_credentials("test_service")

        self.assertEqual(result, self.mock_secret_response)
        mock_instance.secrets.kv.read_secret.assert_called_once_with(path="test_service")

    @patch("hvac.Client")
    def test_retrieve_credentials_failure(self, mock_hvac_client):
        """Test handling of credential retrieval failures"""

        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultError("Vault error")

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

        with self.assertRaises(HashicorpVaultError):
            manager._retrieve_credentials("test_service")

    @patch("hvac.Client")
    def test_vault_connection_error(self, mock_hvac_client):
        """Test handling of Vault connection errors"""

        mock_instance = mock_hvac_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultDown("Vault is sealed")

        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

        with self.assertRaises(HashicorpVaultError):
            manager.get_secret("test_service", "api_key")


if __name__ == "__main__":
    unittest.main(warnings="ignore")
