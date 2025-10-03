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

import logging
import json
import boto3
from botocore.exceptions import ClientError

from .exceptions import AWSSecretsManagerError, SecretNotFoundError, CredentialNotFoundError, InvalidSecretFormatError

logger = logging.getLogger(__name__)


class AwsManager:
    def __init__(self):
        """
        Initializes the client that will access to the credentials management service.

        This takes the credentials to log into aws from the .aws folder.
        This constructor also takes other relevant information from that folder if it exists.

        :raises AWSSecretsManagerError: If AWS Secrets Manager operations fail
        :raises CredentialConnectionError: If connection issues occur
        """

        # Creates a client using the credentials found in the .aws folder (the possible exceptions are propagated)
        logger.info("Initializing client and login in")
        self.client = boto3.client("secretsmanager")

    def _retrieve_and_format_credentials(self, service_name: str) -> dict:
        """
        Retrieves credentials using the class client.

        :param str service_name: Name of the service to retrieve credentials for (or name of the secret)
        :returns: Dictionary containing the credentials retrieved and formatted as a dict
        :rtype: dict
        :raises AWSSecretsManagerError: If AWS Secrets Manager operations fail
        :raises CredentialConnectionError: If connection issues occur
        """
        try:
            logger.info("Retrieving credentials: %s", service_name)
            secret_value_response = self.client.get_secret_value(SecretId=service_name)
            formatted_credentials = json.loads(secret_value_response["SecretString"])
            return formatted_credentials
        except ClientError as e:
            logger.error("Error retrieving the secret: %s", str(e))
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise SecretNotFoundError(f"Secret '{service_name}' not found in AWS Secrets Manager")
            raise AWSSecretsManagerError(f"AWS Secrets Manager error: {e}")
        except json.JSONDecodeError as e:
            logger.error("Error parsing secret JSON: %s", str(e))
            raise InvalidSecretFormatError(f"Invalid secret format: {e}")

    def get_secret(self, service_name: str, credential_name: str) -> str:
        """
        Gets a secret based on the service name and the desired credential.

        :param str service_name: Name of the service to retrieve credentials for
        :param str credential_name: Name of the credential
        :returns: The credential value if found
        :rtype: str
        :raises CredentialNotFoundError: If the credential name is not found in the secret
        :raises SecretNotFoundError: If the secret is not found
        :raises AWSSecretsManagerError: If AWS Secrets Manager operations fail
        :raises InvalidSecretFormatError: If secret data is malformed
        """
        try:
            formatted_credentials = self._retrieve_and_format_credentials(service_name)
            credential = formatted_credentials[credential_name]
            return credential
        except KeyError:
            # This handles when the credential doesn't exist in the secret
            logger.error("The credential '%s' was not found in secret '%s'", credential_name, service_name)
            raise CredentialNotFoundError(f"Credential '{credential_name}' not found in secret '{service_name}'")
