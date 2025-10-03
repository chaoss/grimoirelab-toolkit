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

import logging

from . import HashicorpVaultError, BitwardenCLIError
from .aws_manager import AwsManager
from .bw_manager import BitwardenManager
from .hc_manager import HashicorpManager

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SecretsManagerFactory:
    @staticmethod
    def get_bitwarden_manager(email=None, password=None):
        """
            Gets or creates a BitwardenManager instance.

        :param str email: Bitwarden email.
        :param str password: Bitwarden password.
        :returns: The singleton BitwardenManager instance
        :rtype: BitwardenManager
        :raises BitwardenCLIError: If credentials cannot be obtained
        """
        logger.debug("Creating new Bitwarden manager")

        if not email or not password:
            raise BitwardenCLIError("Bitwarden credentials are required")

        return BitwardenManager(email, password)

    @staticmethod
    def get_aws_manager():
        """
        Gets or creates an AwsManager instance.

        :returns: The singleton AwsManager instance
        :rtype: AwsManager
        """
        logger.debug("Creating new AWS manager")

        return AwsManager()

    @staticmethod
    def get_hashicorp_manager(vault_addr=None, token=None, certificate=None):
        """
        Gets or creates a HashicorpManager instance.

        :param str vault_addr: Vault address.
        :param str token: Vault token.
        :param str certificate: Path to CA certificate.
        :returns: The singleton HashicorpManager instance
        :rtype: HashicorpManager
        :raises HashicorpVaultError: If required credentials cannot be obtained
        """
        logger.debug("Creating new Hashicorp manager")

        if not all([vault_addr, token, certificate]):
            raise HashicorpVaultError("All Hashicorp Vault credentials are required")

        return HashicorpManager(vault_addr, token, certificate)
