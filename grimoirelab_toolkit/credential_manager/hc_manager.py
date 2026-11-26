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
from typing import Any

import hvac
import hvac.exceptions

from .credential_manager import CredentialManager
from .exceptions import CredentialNotFoundError, HashicorpVaultError

logger = logging.getLogger(__name__)

DEFAULT_MOUNT_POINT = "secret"


class HashicorpManager(CredentialManager):
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

    def __init__(
        self,
        vault_url: str,
        token: str,
        certificate: str | bool | None = None,
        mount_point: str = DEFAULT_MOUNT_POINT,
    ) -> None:
        """
        Creates HashicorpManager object using token authentication

        :param str vault_url: The URL of the vault
        :param str token: The access token for authentication
        :param Union[str, bool, None] certificate: TLS verification setting. Either a boolean to indicate whether TLS
            verification should be performed, a string pointing at the CA bundle to use for
            verification
        :param str mount_point: Path where the KV version 2 secrets engine is mounted.
            Secrets are read relative to this path.

        """
        logger.debug("Creating Vault client")
        self.client: hvac.Client = hvac.Client(url=vault_url, token=token, verify=certificate)
        self.mount_point = mount_point
        logger.debug("Vault client initialized successfully")

    def get_secret(self, item_name: str) -> dict[str, Any]:
        """Retrieve an item from the HashiCorp Vault.

        Retrieves all the fields stored for an item with the name
        provided as an argument and returns them as a dictionary.
        The name is the path of the secret relative to the mount
        point of the secrets engine (e.g. "github" reads the secret
        "secret/github" when the mount point is "secret").

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
            logger.debug("Retrieving credentials from vault: %s/%s", self.mount_point, item_name)
            # Read secret from KV secrets engine
            secret = self.client.secrets.kv.read_secret(
                path=item_name, mount_point=self.mount_point
            )
            return secret
        except hvac.exceptions.InvalidPath:
            logger.error(
                "The path %s does not exist in the vault mount %s", item_name, self.mount_point
            )
            raise CredentialNotFoundError(
                f"Secret path '{item_name}' not found in Vault mount '{self.mount_point}'"
            )
        except Exception as e:
            logger.error("Error retrieving the secret: %s", str(e))
            raise HashicorpVaultError(f"Vault operation failed: {e}") from e

    def extract_field(self, secret: dict[str, Any], field_name: str) -> Any:
        """Extract a field value from a HashiCorp Vault secret.

        Reads from secret['data']['data'][field_name].

        :param dict secret: The HashiCorp Vault secret dictionary
        :param str field_name: The name of the field to extract

        :returns: The field value or None if not found
        """
        secret_data = secret.get("data", {}).get("data", {})
        return secret_data.get(field_name)
