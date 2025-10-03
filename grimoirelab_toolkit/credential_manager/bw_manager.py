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
# Author:
#       Alberto Ferrer Sánchez (alberefe@gmail.com)
#

import json
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Any

from .exceptions import (
    BitwardenCLIError,
    InvalidCredentialsError,
    SessionNotFoundError,
    SecretNotFoundError,
    CredentialNotFoundError,
    ConnectionError,
)

logger = logging.getLogger(__name__)


class BitwardenManager:
    def __init__(self, email: str, password: str):
        """
        Logs in bitwarden if not already.

        :param str email: The email of the user
        :param str password: The password of the user
        :raises InvalidCredentialsError: If invalid credentials are provided
        :raises BitwardenCLIError: If Bitwarden CLI operations fail
        :raises CredentialConnectionError: If connection issues occur
        """
        # Session key of the bw session
        self.session_key = None
        self.formatted_credentials = {}
        # store email for session validation
        self._email = email
        self.last_sync_time = None
        self.sync_interval = timedelta(minutes=3)

        try:
            self._login(email, password)
        except (InvalidCredentialsError, BitwardenCLIError, ConnectionError) as e:
            logger.error("Failed to initialize Bitwarden manager: %s", e)
            raise

    def _login(self, bw_email: str, bw_password: str) -> str | None:
        """
        Logs into Bitwarden and obtains a session key.

        Checks the current Bitwarden session status, unlocking or logging in as necessary
        If successful, synchronizes the vault.

        :param str bw_email: Bitwarden account email.
        :param str bw_password: Bitwarden account password.
        :returns: The session key for the current Bitwarden session.
        :rtype: str
        :raises InvalidCredentialsError: If invalid credentials are provided
        :raises SessionNotFoundError: If session cannot be established
        :raises BitwardenCLIError: If Bitwarden CLI operations fail
        :raises CredentialConnectionError: If connection issues occur
        """
        try:
            # If we have a session key, check if sync is needed
            if self.session_key and self._validate_session():
                if self._should_sync():
                    self._sync_vault()
                return self.session_key

            logger.debug("Checking Bitwarden login status")
            # bw has to be in PATH
            status_result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)

            if status_result.returncode == 0:
                logger.debug("Checking vault status")
                status = json.loads(status_result.stdout)

                if status.get("userEmail") == bw_email:
                    logger.debug("User was already authenticated: %s", bw_email)

                    if status.get("status") == "unlocked":
                        logger.debug("Vault unlocked, getting session key")
                        self.session_key = status.get("sessionKey")

                    elif status.get("status") == "locked":
                        logger.debug("Vault locked, unlocking")
                        unlock_result = subprocess.run(
                            ["bw", "unlock", bw_password, "--raw"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        if unlock_result.returncode != 0:
                            error_msg = unlock_result.stderr.strip() if unlock_result.stderr else "Unknown error"
                            logger.error("Error unlocking vault: %s", error_msg)
                            # Handle specific authentication errors
                            if "invalid_grant" in error_msg.lower():
                                logger.error("Invalid credentials provided for Bitwarden")
                            return None

                        session_key = unlock_result.stdout.strip() if unlock_result.stdout else ""
                        if not session_key:
                            raise BitwardenCLIError("Empty session key received from unlock command")
                        self.session_key = session_key

                    if not self.session_key:
                        raise SessionNotFoundError("Couldn't obtain session key during login")

                else:
                    logger.debug("Login in: %s", bw_email)
                    result = subprocess.run(
                        ["bw", "login", bw_email, bw_password, "--raw"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode != 0:
                        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                        logger.error("Error logging in: %s", error_msg)
                        # Handle specific authentication errors
                        if "invalid_grant" in error_msg.lower():
                            raise InvalidCredentialsError("Invalid credentials provided for Bitwarden")
                        raise BitwardenCLIError(f"Bitwarden CLI unlock failed: {error_msg}")

                    logger.debug("Setting session key")
                    session_key = result.stdout.strip() if result.stdout else ""
                    if not session_key:
                        raise BitwardenCLIError("Empty session key received from login command")
                    self.session_key = session_key

            if self.session_key:
                # Only sync if needed based on time interval
                if self._should_sync():
                    logger.debug("Syncing local vault with Bitwarden")
                    sync_result = subprocess.run(
                        ["bw", "sync", "--session", self.session_key],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if sync_result.returncode == 0:
                        self.last_sync_time = datetime.now()
                    else:
                        error_msg = sync_result.stderr.strip() if sync_result.stderr else "Unknown sync error"
                        logger.debug("Sync failed but continuing: %s", error_msg)
                return self.session_key

            if not self.session_key:
                raise SessionNotFoundError("Session key not found - could not log in")
            return self.session_key

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            raise ConnectionError(f"Bitwarden CLI command failed: {e}")

    def _validate_session(self) -> bool:
        """Checks current session.

        :returns: True if session is valid, False otherwise
        :rtype: bool
        """
        try:
            status_result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)

            if status_result.returncode != 0:
                return False

            status = json.loads(status_result.stdout)
            return (
                status.get("status") == "unlocked"
                and status.get("userEmail") == self._email
                and status.get("sessionKey") == self.session_key
            )
        except Exception:
            return False

    def _should_sync(self) -> bool:
        """Determines if vault sync is needed based on last sync time.

        :returns: True if sync is needed, False otherwise
        :rtype: bool
        """
        return not self.last_sync_time or (datetime.now() - self.last_sync_time > self.sync_interval)

    def _sync_vault(self) -> None:
        """Syncs the vault and updates last sync time.

        :returns: None
        :rtype: None
        """
        try:
            logger.debug("Syncing vault")
            subprocess.run(["bw", "sync", "--session", self.session_key], check=True)
            self.last_sync_time = datetime.now()
        except subprocess.CalledProcessError as e:
            logger.error("Sync failed: %s", e)

    def _retrieve_credentials(self, service_name: str) -> dict:
        """
        Retrieves a secret from a particular service from the Bitwarden vault.

        :param str service_name: The name of the data source for which to retrieve the secret
        :returns: The secret item retrieved from Bitwarden as a dictionary.
        :rtype: dict
        :raises BitwardenCLIError: If Bitwarden CLI operations fail
        :raises CredentialConnectionError: If connection issues occur
        :raises InvalidSecretFormatError: If secret data is malformed
        """
        try:
            logger.info("Retrieving credential from Bitwarden CLI: %s", service_name)

            logger.debug("Session key = %s", self.session_key or "None")

            # Check if session key is available
            if not self.session_key:
                raise SessionNotFoundError("No valid session key available")

            # Get list of items
            list_items = subprocess.run(
                ["bw", "list", "items", "--session", self.session_key],
                capture_output=True,
                text=True,
                check=False,
            )

            if list_items.returncode != 0:
                error_msg = list_items.stderr.strip() if list_items.stderr else "Unknown error"
                raise BitwardenCLIError(f"Failed to list items: {error_msg}")

            items = json.loads(list_items.stdout)

            # Find exact match
            match_item = None
            for item in items:
                if item.get("name", "").lower() == service_name.lower():
                    match_item = item
                    break

            if not match_item:
                raise SecretNotFoundError(f"No exact match found for item: {service_name}")

            # Retrieve exact match by id
            item_id = match_item.get("id")
            result = subprocess.run(
                ["bw", "get", "item", item_id, "--session", self.session_key],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise BitwardenCLIError(f"Failed to retrieve secret: {error_msg}")

            retrieved_secrets = json.loads(result.stdout)
            logger.info("Secrets successfully retrieved")
            return retrieved_secrets

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            raise ConnectionError(f"Bitwarden CLI operation failed: {e}")

    def _format_credentials(self, credentials: dict) -> dict:
        """
        Formats the credentials retrieved from Bitwarden into a standardized format.

        :param dict credentials: Raw credentials from Bitwarden
        :returns: Formatted credentials with standardized keys
        :rtype: dict
        """
        formatted = {"service_name": credentials["name"].lower()}

        # Get username and password from login section
        login = credentials.get("login", {})
        if login.get("username"):
            formatted["username"] = login["username"]
        if login.get("password"):
            formatted["password"] = login["password"]

        # Get custom fields
        for field in credentials.get("fields", []):
            formatted[field["name"]] = field["value"]

        return formatted

    def get_secret(self, service_name: str, credential_name: str) -> Any | None:
        """
        Retrieves a secret by name from the Bitwarden vault.

        :param str service_name: The name of the secret to retrieve.
        :param str credential_name: The concrete credential to retrieve.
        :raises CredentialNotFoundError: If the specific credential is not found
        :raises BitwardenCLIError: If Bitwarden CLI operations fail
        :raises CredentialConnectionError: If connection issues occur
        """

        # If stored credentials are not available or belong to a different service
        if not self.formatted_credentials or self.formatted_credentials.get("service_name") != service_name:
            unformatted_credentials = self._retrieve_credentials(service_name)
            self.formatted_credentials = self._format_credentials(unformatted_credentials)

        secret = self.formatted_credentials.get(credential_name)
        if not secret:
            raise CredentialNotFoundError(f"Credential '{credential_name}' not found in service '{service_name}'")

        return secret
