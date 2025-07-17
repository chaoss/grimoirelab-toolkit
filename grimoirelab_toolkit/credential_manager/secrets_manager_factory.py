# -*- coding: utf-8 -*-
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

import getpass
import logging
import os

from .aws_manager import AwsManager
from .bw_manager import BitwardenManager
from .hc_manager import HashicorpManager

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)


class SecretsManagerFactory:

    @staticmethod
    def get_bitwarden_manager(email=None, password=None):
        """
        Gets or creates a BitwardenManager instance.

        Args:
            email (str, optional): Bitwarden email. If not provided,
                                  will try environment variables or prompt.
            password (str, optional): Bitwarden password. If not provided,
                                     will try environment variables or prompt.

        Returns:
            BitwardenManager: The singleton BitwardenManager instance

        Raises:
            ValueError: If credentials cannot be obtained
        """
        _logger.debug("Creating new Bitwarden manager")

        if email is None:
            email = os.environ.get("GRIMOIRELAB_BW_EMAIL")
        if password is None:
            password = os.environ.get("GRIMOIRELAB_BW_PASSWORD")

        if not email or not password:
            email = input("Bitwarden email: ")
            password = getpass.getpass("Bitwarden master password: ")

            if not email or not password:
                raise ValueError("Bitwarden credentials are required")

        return BitwardenManager(email, password)

    @staticmethod
    def get_aws_manager():
        """
        Gets or creates an AwsManager instance.

        Returns:
            AwsManager: The singleton AwsManager instance
        """
        _logger.debug("Creating new AWS manager")

        return AwsManager()


    @staticmethod
    def get_hashicorp_manager(
        vault_addr=None, token=None, certificate=None
    ):
        """
        Gets or creates a HashicorpManager instance.

        Args:
            vault_addr (str, optional): Vault address.

            token (str, optional): Vault token.

            certificate (str, optional): Path to CA certificate.

        Returns:
            HashicorpManager: The singleton HashicorpManager instance

        Raises:
            ValueError: If required credentials cannot be obtained
        """
        _logger.debug("Creating new Hashicorp manager")

        if vault_addr is None:
            vault_addr = os.environ.get("GRIMOIRELAB_VAULT_ADDR")
        if token is None:
            token = os.environ.get("GRIMOIRELAB_VAULT_TOKEN")
        if certificate is None:
            certificate = os.environ.get("GRIMOIRELAB_VAULT_CACERT")

        if not vault_addr:
            vault_addr = input("Please enter vault address: ")
        if not token:
            token = input("Please enter vault token: ")
        if not certificate:
            certificate = input(
                "Please enter path to a PEM-encoded CA certificate file: "
            )

        if not all([vault_addr, token, certificate]):
            raise ValueError("All Hashicorp Vault credentials are required")

        return HashicorpManager(vault_addr, token, certificate)
