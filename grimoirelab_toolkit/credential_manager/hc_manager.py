# -*- coding: utf-8 -*-
#
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the impglied warranty of
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
import hvac
import hvac.exceptions

logger = logging.getLogger(__name__)


class HashicorpManager:
    """
    A class to retrieve secrets from HashicorpVault
    """

    def __init__(self, vault_url: str, token: str, certificate: str):
        """
        Initializes the client with the corresponding token to interact with the vault, so no login
        is required in vault.

        :param str vault_url: The vault URL.
        :param str token: The access token.
        :param str certificate: The tls certificate.
        :raises Exception: If couldn't inizialize the client
        """
        try:
            logger.debug("Creating client and logging in.")
            self.client = hvac.Client(url=vault_url, token=token, verify=certificate)

        except Exception as e:
            logger.error("An error ocurred initializing the client: %s", str(e))
            # this is dealt with    in the get_secret function
            raise e

        if self.client.sys.is_initialized():
            logger.debug("Client is initialized")
        else:
            raise Exception("Vault client is not initialized")

        if self.client.is_authenticated():
            logger.debug("Client is authenticated")
        else:
            raise Exception("Client authentication failed")

    def _retrieve_credentials(self, service_name: str) -> dict:
        """
        Function responsible for retrieving credentials from vault

        :param str service_name: The name of the service to retrieve credentials for
        :returns: a dict containing all the data for that service. Includes metadata
            and other information stored in the vault
        :rtype: dict
        :raises Exception: If couldn't retrieve credentials'
        """
        try:
            logger.info("Retrieving credentials from vault.")
            secret = self.client.secrets.kv.read_secret(path=service_name)
            return secret
        except Exception as e:
            logger.error("Error retrieving the secret: %s", str(e))
            # this is dealt with in the get_secret function
            raise e

    def get_secret(self, service_name: str, credential_name: str) -> str:
        """
        Retrieves the value of the service + credential named.

        :param str service_name: The name of the service to retrieve credentials for
        :param str credential_name: The name of the credential to retrieve
        :returns: The value of the credential
        :rtype: str
        :raises Exception: If couldn't retrieve credentials'
        """
        try:
            credentials = self._retrieve_credentials(service_name)
            # We get the exact credential from the dict returned by the retrieval
            credential = credentials["data"]["data"][credential_name]
            logger.info("Credentials retrieved succesfully")
            return credential
        except (
            hvac.exceptions.Forbidden,
            hvac.exceptions.InternalServerError,
            hvac.exceptions.InvalidRequest,
            hvac.exceptions.RateLimitExceeded,
            hvac.exceptions.Unauthorized,
            hvac.exceptions.UnsupportedOperation,
            hvac.exceptions.VaultDown,
            hvac.exceptions.VaultError,
        ) as e:
            logger.error("There was an error retrieving the secret: %s", e)
            return ""
        except KeyError:
            logger.error("The credential %s was not found", credential_name)
            return ""
        except hvac.exceptions.InvalidPath:
            logger.error("The path %s does not exist in the vault", service_name)
            return ""
