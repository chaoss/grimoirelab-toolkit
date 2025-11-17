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

import logging

import hvac
import hvac.exceptions

from .exceptions import HashicorpVaultError, CredentialNotFoundError

logger = logging.getLogger(__name__)


class HashicorpManager:
    """Retrieve credentials from HashiCorp Vault.

    This class defines functions to initialize a client and retrieve
    secrets from HashiCorp Vault. The workflow is:

    manager = HashicorpManager(vault_url, token, certificate)
    manager.get_secret("github")
    manager.get_secret("elasticsearch")

    The manager initializes the client using the vault_url, token,
    and certificate given as arguments when creating the instance,
    so the object is reusable along the program.

    The get_secret function returns the whole item object, with metadata
    included, so the user can choose to store it and retrieve desired data.
    """

    def __init__(self, vault_url: str, token: str, certificate: str | bool = None):
        """
        Creates HashicorpManager object using token authentication

        :param str vault_url: The URL of the vault
        :param str token: The access token for authentication
        :param Union[str, bool, None] certificate: TLS verification setting. Either a boolean to indicate whether TLS
            verification should be performed, a string pointing at the CA bundle to use for
            verification

        :raises ConnectionError: If connection issues occur
        """
        try:
            logger.debug("Creating Vault client")
            # Initialize client with URL, token, and certificate verification setting
            self.client = hvac.Client(url=vault_url, token=token, verify=certificate)
            logger.debug("Vault client initialized successfully")
        except Exception as e:
            logger.error("An error occurred initializing the client: %s", str(e))
            raise e

    def get_secret(self, item_name: str) -> dict:
        """Retrieve an item from the HashiCorp Vault.

        Retrieves all the fields stored for an item with the name
        provided as an argument and returns them as a dictionary.

        The returned dictionary includes fields such as:
        - data: The actual secret data and metadata
        - request_id, lease_id, renewable, lease_duration
        - Other vault metadata

        :param str item_name: The name of the item to retrieve

        :returns: Dictionary containing the secret data and metadata
        :rtype: dict

        :raises CredentialNotFoundError: If the secret path is not found
        :raises HashicorpVaultError: If Vault operations fail
        """
        try:
            logger.info("Retrieving credentials from vault: %s", item_name)
            # Read secret from KV secrets engine
            secret = self.client.secrets.kv.read_secret(path=item_name)
            return secret
        except hvac.exceptions.InvalidPath:
            logger.error("The path %s does not exist in the vault", item_name)
            raise CredentialNotFoundError(
                f"Secret path '{item_name}' not found in Vault"
            )
        except Exception as e:
            logger.error("Error retrieving the secret: %s", str(e))
            raise HashicorpVaultError(f"Vault operation failed: {e}")
