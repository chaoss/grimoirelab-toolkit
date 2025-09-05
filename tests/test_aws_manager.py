import pytest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError, EndpointConnectionError, SSLError

from grimoirelab_toolkit.credential_manager.aws_manager import AwsManager

MOCK_SECRET_RESPONSE = {
    "ARN": "arn:aws:secretsmanager:region:account:secret:test-secret-123456",
    "Name": "test-secret",
    "VersionId": "12345678-1234-1234-1234-123456789012",
    "SecretString": '{"username": "test_user", "password": "test_pass", "api_key": "test_key"}',
    "VersionStages": ["AWSCURRENT"]
}

def test_initialization():
    """Test successful initialization"""
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        manager = AwsManager()
        mock_boto.assert_called_once_with('secretsmanager')
        assert manager.client is not None

def test_initialization_endpoint_error():
    """Test initialization failure due to endpoint error"""
    with patch('boto3.client') as mock_boto:
        mock_boto.side_effect = EndpointConnectionError(endpoint_url="http://example.com")
        with pytest.raises(EndpointConnectionError):
            AwsManager()

def test_initialization_ssl_error():
    """Test initialization failure due to SSL error"""
    with patch('boto3.client') as mock_boto:
        mock_boto.side_effect = SSLError(
            error="SSL Validation failed",
            endpoint_url="http://example.com"
        )
        with pytest.raises(SSLError):
            AwsManager()

def test_retrieve_and_format_credentials_success():
    """Test successful retrieval and formatting of credentials"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = MOCK_SECRET_RESPONSE
        mock_boto.return_value = mock_client

        manager = AwsManager()
        result = manager._retrieve_and_format_credentials("test-secret")

        assert result["username"] == "test_user"
        assert result["password"] == "test_pass"
        assert result["api_key"] == "test_key"

def test_retrieve_and_format_credentials_not_found():
    """Test handling of non-existent secrets"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Secret not found'
            }
        }

        mock_client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with pytest.raises(Exception):
            manager._retrieve_and_format_credentials("nonexistent-secret")

def test_retrieve_and_format_credentials_invalid_json():
    """Test handling of invalid JSON in secret value"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        invalid_response = MOCK_SECRET_RESPONSE.copy()
        invalid_response['SecretString'] = 'invalid json'
        mock_client.get_secret_value.return_value = invalid_response
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with pytest.raises(json.JSONDecodeError):
            manager._retrieve_and_format_credentials("test-secret")

def test_get_secret_success():
    """Test successful secret retrieval"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = MOCK_SECRET_RESPONSE
        mock_boto.return_value = mock_client

        manager = AwsManager()

        result = manager.get_secret("test-secret", "api_key")
        assert result == "test_key"

def test_get_secret_missing_credential():
    """Test handling of non existant credential"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = MOCK_SECRET_RESPONSE
        mock_boto.return_value = mock_client

        manager = AwsManager()

        result = manager.get_secret("test-secret", "nonexistent_credential")
        assert result == ""

def test_get_secret_service_error():
    """Test handling of AWS service errors"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        error_response = {
            'Error': {
                'Code': 'InternalServiceError',
                'Message': 'Internal service error'
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        mock_boto.return_value = mock_client

        manager = AwsManager()

        with pytest.raises(Exception):
            manager.get_secret("test-secret", "api_key")