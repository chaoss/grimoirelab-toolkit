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
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, EndpointConnectionError, SSLError

from grimoirelab_toolkit.credential_manager.aws_manager import AwsManager
from grimoirelab_toolkit.credential_manager.exceptions import SecretNotFoundError, AWSSecretsManagerError


class TestAwsManager(unittest.TestCase):
    """AwsManager unit tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_secret_response = {
            "ARN": "arn:aws:secretsmanager:region:account:secret:test-secret-123456",
            "Name": "test-secret",
            "VersionId": "12345678-1234-1234-1234-123456789012",
            "SecretString": '{"username": "test_user", "password": "test_pass", "api_key": "test_key"}',
            "VersionStages": ["AWSCURRENT"],
        }

    @patch("boto3.client")
    def test_initialization(self, mock_boto):
        """Test successful initialization"""
        mock_boto.return_value = MagicMock()
        manager = AwsManager()
        mock_boto.assert_called_once_with("secretsmanager")
        self.assertIsNotNone(manager.client)

    @patch("boto3.client")
    def test_initialization_endpoint_error(self, mock_boto):
        """Test initialization failure due to endpoint error"""
        mock_boto.side_effect = EndpointConnectionError(endpoint_url="http://example.com")
        with self.assertRaises(EndpointConnectionError):
            AwsManager()

    @patch("boto3.client")
    def test_initialization_ssl_error(self, mock_boto):
        """Test initialization failure due to SSL error"""
        mock_boto.side_effect = SSLError(error="SSL Validation failed", endpoint_url="http://example.com")
        with self.assertRaises(SSLError):
            AwsManager()

    @patch("boto3.client")
    def test_retrieve_and_format_credentials_success(self, mock_boto):
        """Test successful retrieval and formatting of credentials"""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = self.mock_secret_response
        mock_boto.return_value = mock_client

        manager = AwsManager()
        result = manager._retrieve_and_format_credentials("test-secret")

        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["password"], "test_pass")
        self.assertEqual(result["api_key"], "test_key")

    @patch("boto3.client")
    def test_retrieve_and_format_credentials_not_found(self, mock_boto):
        """Test handling of non-existent secrets"""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "ResourceNotFoundException", "Message": "Secret not found"}}

        mock_client.get_secret_value.side_effect = ClientError(error_response, "GetSecretValue")
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with self.assertRaises(SecretNotFoundError):
            manager._retrieve_and_format_credentials("nonexistent-secret")

    @patch("boto3.client")
    def test_retrieve_and_format_credentials_invalid_json(self, mock_boto):
        """Test handling of invalid JSON in secret value"""
        from grimoirelab_toolkit.credential_manager.exceptions import InvalidSecretFormatError

        mock_client = MagicMock()
        invalid_response = self.mock_secret_response.copy()
        invalid_response["SecretString"] = "invalid json"
        mock_client.get_secret_value.return_value = invalid_response
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with self.assertRaises(InvalidSecretFormatError):
            manager._retrieve_and_format_credentials("test-secret")

    @patch("boto3.client")
    def test_get_secret_success(self, mock_boto):
        """Test successful secret retrieval"""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = self.mock_secret_response
        mock_boto.return_value = mock_client

        manager = AwsManager()

        result = manager.get_secret("test-secret", "api_key")
        self.assertEqual(result, "test_key")

    @patch("boto3.client")
    def test_get_secret_missing_credential(self, mock_boto):
        """Test handling of non existant credential"""
        from grimoirelab_toolkit.credential_manager.exceptions import CredentialNotFoundError

        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = self.mock_secret_response
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with self.assertRaises(CredentialNotFoundError):
            manager.get_secret("test-secret", "nonexistent_credential")

    @patch("boto3.client")
    def test_get_secret_service_error(self, mock_boto):
        """Test handling of AWS service errors"""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "InternalServiceError", "Message": "Internal service error"}}
        mock_client.get_secret_value.side_effect = ClientError(error_response, "GetSecretValue")
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with self.assertRaises(AWSSecretsManagerError):
            manager.get_secret("test-secret", "api_key")


if __name__ == "__main__":
    unittest.main(warnings="ignore")
