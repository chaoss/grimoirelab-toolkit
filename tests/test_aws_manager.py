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

import unittest
from unittest.mock import patch

from botocore.exceptions import ClientError

from grimoirelab_toolkit.credential_manager.aws_manager import AwsManager
from grimoirelab_toolkit.credential_manager.exceptions import (
    AWSSecretsManagerError,
    CredentialNotFoundError,
)


class TestAwsManager(unittest.TestCase):
    """Tests for AwsManager class."""

    def setUp(self):
        """Set up common test fixtures."""

        self.mock_secret_response = {
            "ARN": "arn:aws:secretsmanager:region:account:secret:test-secret-123456",
            "Name": "test-secret",
            "VersionId": "12345678-1234-1234-1234-123456789012",
            "SecretString": (
                '{"username": "test_user", "password": "test_pass", '
                '"api_key": "test_key"}'
            ),
            "VersionStages": ["AWSCURRENT"],
        }

    @patch("boto3.client")
    def test_initialization_success(self, mock_boto):
        """Test successful initialization."""

        manager = AwsManager()

        self.assertIsNotNone(manager.client)
        mock_boto.assert_called_once_with("secretsmanager")

    @patch("boto3.client")
    def test_get_secret_success(self, mock_boto):
        """Test successful secret retrieval."""

        mock_client = mock_boto.return_value
        mock_client.get_secret_value.return_value = self.mock_secret_response

        manager = AwsManager()
        result = manager.get_secret("test_service")

        # Verify it returns the parsed JSON dict
        self.assertIsInstance(result, dict)
        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["password"], "test_pass")
        self.assertEqual(result["api_key"], "test_key")
        mock_client.get_secret_value.assert_called_once_with(SecretId="test_service")

    @patch("boto3.client")
    def test_get_secret_not_found(self, mock_boto):
        """Test get_secret raises error when secret is not found."""

        mock_client = mock_boto.return_value
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secret not found",
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AwsManager()

        with self.assertRaises(CredentialNotFoundError) as context:
            manager.get_secret("nonexistent_service")

        self.assertIn("nonexistent_service", str(context.exception))
        self.assertIn("not found", str(context.exception))

    @patch("boto3.client")
    def test_get_secret_aws_error(self, mock_boto):
        """Test get_secret raises error on generic AWS service errors."""

        mock_client = mock_boto.return_value
        error_response = {
            "Error": {
                "Code": "InternalServiceError",
                "Message": "Internal service error",
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AwsManager()

        with self.assertRaises(AWSSecretsManagerError) as context:
            manager.get_secret("test_service")

        self.assertIn("AWS Secrets Manager operation failed", str(context.exception))

    @patch("boto3.client")
    def test_get_secret_invalid_json(self, mock_boto):
        """Test get_secret raises error when SecretString is not valid JSON."""

        mock_client = mock_boto.return_value
        invalid_response = dict(self.mock_secret_response, SecretString="not-json")
        mock_client.get_secret_value.return_value = invalid_response

        manager = AwsManager()

        with self.assertRaises(AWSSecretsManagerError) as context:
            manager.get_secret("test_service")

        self.assertIn("Invalid secret format", str(context.exception))

    @patch("boto3.client")
    def test_get_secret_missing_secret_string(self, mock_boto):
        """Test get_secret raises error when response has no SecretString."""

        mock_client = mock_boto.return_value
        binary_only_response = {
            "ARN": "arn:aws:secretsmanager:region:account:secret:binary",
            "Name": "binary-secret",
            "SecretBinary": b"raw-bytes",
            "VersionStages": ["AWSCURRENT"],
        }
        mock_client.get_secret_value.return_value = binary_only_response

        manager = AwsManager()

        with self.assertRaises(AWSSecretsManagerError) as context:
            manager.get_secret("binary_secret")

        self.assertIn("does not contain a SecretString", str(context.exception))

    @patch("boto3.client")
    def test_extract_field_success(self, mock_boto):
        """Test extracting an existing field from a secret."""

        manager = AwsManager()
        secret = {"username": "test_user", "password": "test_pass"}
        result = manager.extract_field(secret, "username")

        self.assertEqual(result, "test_user")

    @patch("boto3.client")
    def test_extract_field_not_found(self, mock_boto):
        """Test extracting a non-existent field returns None."""

        manager = AwsManager()
        secret = {"username": "test_user"}
        result = manager.extract_field(secret, "nonexistent")

        self.assertIsNone(result)

    @patch("boto3.client")
    def test_extract_field_empty_secret(self, mock_boto):
        """Test extracting a field from an empty secret returns None."""

        manager = AwsManager()
        result = manager.extract_field({}, "username")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(warnings="ignore")
