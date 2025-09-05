import pytest
from unittest.mock import patch
import hvac.exceptions

from grimoirelab_toolkit.credential_manager.hc_manager import HashicorpManager

MOCK_SECRET_RESPONSE = {
    "auth": None,
    "data": {
        "data": {"password": "pass", "username": "user", "api_key": "test_key"},
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


@pytest.fixture
def mock_hvac_client():
    with patch("hvac.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        yield mock_client


def test_initialization(mock_hvac_client):
    """Test successful initialization of HashicorpManager."""

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

    assert manager.client is not None
    mock_hvac_client.assert_called_once_with(
        url="http://vault-url", token="test-token", verify="test-certificate"
    )
    assert manager.client.sys.is_initialized()
    assert manager.client.is_authenticated()


def test_initialization_failure(mock_hvac_client):
    """Test handling of initialization failures."""

    mock_hvac_client.side_effect = hvac.exceptions.VaultError("Connection failed")

    with pytest.raises(hvac.exceptions.VaultError) as exception_info:
        HashicorpManager("http://vault-url", "test-token", "test-certificate")
    assert "Connection failed" in str(exception_info.value)


def test_get_secret_success(mock_hvac_client):
    """Test successful secret retrieval."""

    # Mock that returns the test secret
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.return_value = MOCK_SECRET_RESPONSE

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "api_key")

    assert result == "test_key"
    mock_instance.secrets.kv.read_secret.assert_called_once_with(path="test_service")


def test_get_secret_not_found(mock_hvac_client):
    """Test handling of non existant secrets."""

    # Mock that simulates non existant secret
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.InvalidPath()

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "nonexistent")

    assert result == ""


def test_get_secret_permission_denied(mock_hvac_client):
    """Test handling of permission denied errors."""

    # Mock to simulate permission denied
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.Forbidden()

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "api_key")

    assert result == ""


def test_retrieve_credentials_success(mock_hvac_client):
    """Test successful retrieval of raw credentials."""

    # Mock that returns the test secret
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.return_value = MOCK_SECRET_RESPONSE

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager._retrieve_credentials("test_service")

    assert result == MOCK_SECRET_RESPONSE
    mock_instance.secrets.kv.read_secret.assert_called_once_with(path="test_service")


def test_retrieve_credentials_failure(mock_hvac_client):
    """Test handling of credential retrieval failures."""

    # Mock simulate Vault error
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultError(
        "Vault error"
    )

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

    with pytest.raises(hvac.exceptions.VaultError):
        manager._retrieve_credentials("test_service")


def test_vault_connection_error(mock_hvac_client):
    """Test handling of Vault connection errors."""

    # Mock that simulates connection error
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultDown(
        "Vault is sealed"
    )

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "api_key")

    assert result == ""
