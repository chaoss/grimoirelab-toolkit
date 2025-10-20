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

        Method follows these steps:
        1. Check if current session is valid and return if true
        2. Get current Bitwarden status
        3. Handle authentication for already logged user or not logged user
        4. Sync vault if needed

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
            if self._is_session_valid():
                self._sync_if_needed()
                return self.session_key

            status = self._get_bitwarden_status()

            if not status:
                raise SessionNotFoundError("Could not retrieve Bitwarden status")

            if status.get("userEmail") == bw_email:
                # the email in the returned status is the same introduced, so the user is logged in
                self._handle_existing_user_auth(bw_password, status)
            else:
                # logs in with the desired credentials
                self._handle_new_user_auth(bw_email, bw_password)

            if not self.session_key:
                # there is no session key after atempting to log in
                raise SessionNotFoundError("Session key not found cause could not log in")

            self._sync_if_needed()
            return self.session_key

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            raise ConnectionError(f"Bitwarden CLI command failed: {e}")

    def _is_session_valid(self) -> bool:
        """
        Check if there is an active session and doesn't need re-authentication.

        :returns: True if session is valid and active, False otherwise
        :rtype: bool
        """
        if self.session_key is not None and self._validate_session():
            return True
        return False

    def _sync_if_needed(self) -> None:
        """
        Sync vault if sync interval has passed.

        """
        if self._should_sync():
            self._sync_vault()

    def _get_bitwarden_status(self) -> dict:
        """
        Get current status information about the Bitwarden CLI.

        Retrieves configured server URL, timestamp for the last sync, user email
        and ID, and the vault status.

        :returns: Dictionary containing Bitwarden status information or None if command fails
        :rtype: dict or None
        """
        logger.debug("Checking Bitwarden login status")
        status_result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)

        if status_result.returncode != 0:
            return None

        return json.loads(status_result.stdout)

    def _handle_existing_user_auth(self, bw_password: str, status: dict) -> None:
        """
        Handle authentication for an existing authenticated user.

        Checks if the vault is unlocked or locked and handles accordingly.
        If unlocked, retrieves the existing session key. If locked, attempts
        to unlock the vault with the provided password.

        :param str bw_password: Bitwarden account password for unlocking if needed
        :param dict status: Bitwarden status dictionary containing vault state
        :raises SessionNotFoundError: If session key cannot be obtained
        :returns: None
        :rtype: None
        """
        logger.debug("User was already authenticated")
        vault_status = status.get("status")

        if vault_status == "unlocked":
            logger.debug("Vault unlocked, getting session key")
            self.session_key = status.get("sessionKey")

        elif vault_status == "locked":
            logger.debug("Vault locked, unlocking")
            self.session_key = self._unlock_vault(bw_password)

        if not self.session_key:
            raise SessionNotFoundError("Couldn't obtain session key during login")

    def _handle_new_user_auth(self, bw_email: str, bw_password: str) -> None:
        """
        Handle authentication for a new user.

        Performs login with the provided email and password to obtain
        a new session key.

        Sets the manager session key.

        :param str bw_email: Bitwarden account email
        :param str bw_password: Bitwarden account password
        :raises InvalidCredentialsError: If credentials are invalid
        :raises BitwardenCLIError: If login operation fails
        """
        logger.debug("Logging in: %s", bw_email)
        self.session_key = self._perform_login(bw_email, bw_password)

    def _unlock_vault(self, bw_password: str) -> str:
        """
        Unlock the vault with password.

        Executes the Bitwarden unlock command to obtain a session key
        for an already authenticated but locked vault.

        :param str bw_password: Bitwarden account password
        :returns: Session key for the unlocked vault
        :rtype: str
        :raises BitwardenCLIError: If unlock operation fails or returns empty session key
        :returns: None if unlock fails due to invalid credentials
        :rtype: str or None
        """
        unlock_result = subprocess.run(
            ["bw", "unlock", bw_password, "--raw"],
            capture_output=True,
            text=True,
            check=False,
        )

        if unlock_result.returncode != 0:
            error_msg = unlock_result.stderr.strip() if unlock_result.stderr else "Unknown error"
            logger.error("Error unlocking vault: %s", error_msg)
            if "invalid_grant" in error_msg.lower():
                logger.error("Invalid credentials provided for Bitwarden")
            return None

        session_key = unlock_result.stdout.strip() if unlock_result.stdout else ""
        if not session_key:
            raise BitwardenCLIError("Empty session key received from unlock command")

        return session_key

    def _perform_login(self, bw_email: str, bw_password: str) -> str:
        """
        Executes the login command to authenticate a user.

        Performs Bitwarden authentication using email and password
        credentials to obtain a new session key.

        :param str bw_email: Bitwarden account email
        :param str bw_password: Bitwarden account password
        :returns: Session key for the authenticated user
        :rtype: str
        :raises InvalidCredentialsError: If invalid credentials are provided
        :raises BitwardenCLIError: If login operation fails or returns empty session key
        """
        result = subprocess.run(
            ["bw", "login", bw_email, bw_password, "--raw"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error("Error logging in: %s", error_msg)
            if "invalid_grant" in error_msg.lower():
                raise InvalidCredentialsError("Invalid credentials provided for Bitwarden")
            raise BitwardenCLIError(f"Bitwarden CLI login failed: {error_msg}")

        logger.debug("Setting session key")
        session_key = result.stdout.strip() if result.stdout else ""
        if not session_key:
            raise BitwardenCLIError("Empty session key received from login command")

        return session_key

    def _validate_session(self) -> bool:
        """
        Checks current session validity.

        Verifies that the current session is still active, unlocked, and matches
        the stored email and session key.

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
        """
        Determines if vault sync is needed based on last sync time.

        Checks if enough time has passed since the last sync according to
        the configured sync interval.

        :returns: True if sync is needed, False otherwise
        :rtype: bool
        """
        return not self.last_sync_time or (datetime.now() - self.last_sync_time > self.sync_interval)

    def _sync_vault(self) -> None:
        """
        Syncs the vault and updates last sync time.

        Executes the Bitwarden sync command to retrieve the latest
        vault data from the server and updates the last sync timestamp.

        :raises subprocess.CalledProcessError: If sync command fails
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
