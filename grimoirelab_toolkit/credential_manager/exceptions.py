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

"""Custom exceptions for the credential manager module."""

__all__ = [
    "CredentialManagerError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "SessionExpiredError",
    "SessionNotFoundError",
    "ConnectionError",
    "ServiceUnavailableError",
    "NetworkTimeoutError",
    "ConfigurationError",
    "SecretRetrievalError",
    "SecretNotFoundError",
    "CredentialNotFoundError",
    "InvalidSecretFormatError",
    "BitwardenCLIError",
    "AWSSecretsManagerError",
    "HashicorpVaultError",
    "UnsupportedSecretsManagerError",
]


class CredentialManagerError(Exception):
    """Base exception for all credential manager errors."""

    pass


class AuthenticationError(CredentialManagerError):
    """Base exception for authentication-related errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when invalid credentials are provided."""

    pass


class SessionExpiredError(AuthenticationError):
    """Raised when session token has expired."""

    pass


class SessionNotFoundError(AuthenticationError):
    """Raised when no active session is found."""

    pass


class ConnectionError(CredentialManagerError):
    """Base exception for connection-related errors."""

    pass


class ServiceUnavailableError(ConnectionError):
    """Raised when the secret manager service is unavailable."""

    pass


class NetworkTimeoutError(ConnectionError):
    """Raised when a network request times out."""

    pass


class ConfigurationError(ConnectionError):
    """Raised when there is a configuration error."""

    pass


class SecretRetrievalError(CredentialManagerError):
    """Base exception for secret retrieval errors."""

    pass


class SecretNotFoundError(SecretRetrievalError):
    """Raised when a secret is not found."""

    pass


class CredentialNotFoundError(SecretRetrievalError):
    """Raised when a specific credential is not found in a secret."""

    pass


class InvalidSecretFormatError(SecretRetrievalError):
    """Raised when secret data is malformed."""

    pass


class BitwardenCLIError(CredentialManagerError):
    """Raised for Bitwarden CLI specific errors."""

    pass


class AWSSecretsManagerError(CredentialManagerError):
    """Raised for AWS Secrets Manager specific errors."""

    pass


class HashicorpVaultError(CredentialManagerError):
    """Raised for HashiCorp Vault specific errors."""

    pass


class UnsupportedSecretsManagerError(CredentialManagerError):
    """Raised when an unsupported secrets manager is requested."""

    pass
