#
#
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
#

import logging

from .exceptions import HashicorpVaultError

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecretsManagerFactory:
    """Factory for creating secrets manager instances.

    This class defines static methods to create instances of different
    secrets manager implementations. The workflow is:

    bw_manager = SecretsManagerFactory.get_bitwarden_manager(client_id, client_secret, master_password)
    hc_manager = SecretsManagerFactory.get_hashicorp_manager(vault_url, token, certificate)

    Each factory method handles the instantiation of the appropriate
    manager class with the required credentials and configuration,
    providing a centralized way to create secrets manager objects.

    The factory validates required parameters before creating instances
    and raises appropriate exceptions if credentials are missing or invalid.
    """

    @staticmethod
    def get_bitwarden_manager(client_id: str, client_secret: str, master_password: str):
        """Create a BitwardenManager instance.

        Creates and returns a new BitwardenManager instance using the
        provided API credentials and master password.

        :param str client_id: Bitwarden API client ID
        :param str client_secret: Bitwarden API client secret
        :param str master_password: Master password for unlocking the vault

        :returns: A new BitwardenManager instance
        :rtype: BitwardenManager

        :raises BitwardenCLIError: If Bitwarden CLI is not found in PATH
        """
        from .bw_manager import BitwardenManager

        logger.debug("Creating new Bitwarden manager")

        return BitwardenManager(client_id, client_secret, master_password)

    @staticmethod
    def get_hashicorp_manager(
        vault_url: str, token: str, certificate: str | bool = None
    ):
        """Create a HashicorpManager instance.

        Creates and returns a new HashicorpManager instance using the
        provided Vault URL, authentication token, and certificate settings.

        :param str vault_url: The URL of the HashiCorp Vault
        :param str token: The access token for authentication
        :param Union[str, bool, None] certificate: TLS verification setting. Either a boolean to indicate whether TLS
            verification should be performed, a string pointing at the CA bundle to use for
            verification

        :returns: A new HashicorpManager instance
        :rtype: HashicorpManager

        :raises HashicorpVaultError: If required credentials cannot be obtained
        """
        from .hc_manager import HashicorpManager

        logger.debug("Creating new Hashicorp manager")

        if not all([vault_url, token]):
           raise HashicorpVaultError("HashiCorp Vault requires vault_url and token")

        return HashicorpManager(vault_url, token, certificate)
