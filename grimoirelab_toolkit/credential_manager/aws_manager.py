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

import json
import logging

import boto3
from botocore.exceptions import ClientError

from .credential_manager import CredentialManager
from .exceptions import AWSSecretsManagerError, CredentialNotFoundError

logger = logging.getLogger(__name__)


class AwsManager(CredentialManager):
    """Retrieve credentials from AWS Secrets Manager.

    This class defines functions to initialize a client and retrieve
    secrets from AWS Secrets Manager. The workflow is:

    manager = AwsManager()
    manager.get_secret("github")
    manager.get_secret("elasticsearch")

    The manager initializes the client using the default AWS credential
    provider chain (environment variables, ~/.aws/credentials, IAM role,
    etc.), so the object is reusable along the program.

    Secrets are expected to be stored as JSON strings in the SecretString
    field. The get_secret function returns the parsed JSON object as a
    dictionary, so the user can choose to store it and retrieve desired
    data.
    """

    def __init__(self):
        """
        Creates AwsManager object using the default AWS credential chain
        """
        logger.debug("Creating AWS Secrets Manager client")
        self.client = boto3.client("secretsmanager")
        logger.debug("AWS Secrets Manager client initialized successfully")

    def get_secret(self, item_name: str) -> dict:
        """Retrieve an item from AWS Secrets Manager.

        Retrieves the secret stored under the name provided as an argument,
        parses its SecretString as JSON, and returns the result as a
        dictionary.

        The returned dictionary contains the user-defined key-value pairs
        stored in the secret's SecretString field.

        :param str item_name: The name of the secret to retrieve

        :returns: Dictionary containing the secret data
        :rtype: dict

        :raises CredentialNotFoundError: If the secret is not found
        :raises AWSSecretsManagerError: If AWS Secrets Manager operations
            fail
        """
        try:
            logger.debug("Retrieving credentials from AWS: %s", item_name)
            # Retrieve secret from AWS Secrets Manager
            response = self.client.get_secret_value(SecretId=item_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                logger.error("Secret '%s' not found in AWS Secrets Manager", item_name)
                raise CredentialNotFoundError(
                    f"Secret '{item_name}' not found in AWS Secrets Manager"
                )
            logger.error("Error retrieving the secret: %s", str(e))
            raise AWSSecretsManagerError(f"AWS Secrets Manager operation failed: {e}")

        if "SecretString" not in response:
            raise AWSSecretsManagerError(
                f"Secret '{item_name}' does not contain a SecretString"
            )

        # Parse the SecretString JSON into a dictionary
        try:
            return json.loads(response["SecretString"])
        except json.JSONDecodeError as e:
            logger.error("Failed to parse secret JSON: %s", str(e))
            raise AWSSecretsManagerError(
                f"Invalid secret format for '{item_name}': {e}"
            )

    def extract_field(self, secret: dict, field_name: str) -> str | None:
        """Extract a field value from an AWS Secrets Manager secret.

        Reads from secret[field_name].

        :param dict secret: The parsed secret dictionary
        :param str field_name: The name of the field to extract

        :returns: The field value or None if not found
        :rtype: str or None
        """
        return secret.get(field_name)
