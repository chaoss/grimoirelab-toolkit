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

from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CredentialManager(ABC):
    """Abstract base class for credential managers.

    Defines the interface that all credential manager implementations
    must follow. Provides a concrete `resolve_credentials` method
    (Template Method) that orchestrates the shared workflow of
    logging in, fetching a secret, extracting fields, and logging out.

    Subclasses must implement `get_secret` and `extract_field`.
    Subclasses that require authentication (e.g. Bitwarden) should
    override `login` and `logout`.
    """

    @abstractmethod
    def get_secret(self, item_name: str) -> dict:
        """Retrieve a secret item from the vault.

        :param str item_name: The name/path of the secret item

        :returns: Dictionary containing the secret data
        :rtype: dict
        """
        raise NotImplementedError

    @abstractmethod
    def extract_field(self, secret: dict, field_name: str) -> str | None:
        """Extract a single field value from a secret item.

        :param dict secret: The secret dictionary returned by `get_secret`
        :param str field_name: The name of the field to extract

        :returns: The field value, or None if not found
        :rtype: str or None
        """
        raise NotImplementedError

    def login(self):
        """Log into the secrets manager. No-op by default."""
        pass

    def logout(self):
        """Log out from the secrets manager. No-op by default."""
        pass

    def resolve_credentials(
        self,
        item_name: str,
        field_names: list[str],
    ) -> dict[str, str]:
        """Resolve credentials from the secrets manager.

        Fetches a secret item and extracts the requested fields.
        Handles login/logout lifecycle automatically.

        :param str item_name: Name/path of the secret item in the vault
        :param list field_names: List of field names to extract

        :returns: Dict mapping field names to their resolved values.
            Only fields that were found are included.
        :rtype: dict[str, str]

        :raises ValueError: If item_name is empty
        """
        if not item_name:
            raise ValueError("Missing item name")

        if not field_names:
            return {}

        self.login()
        try:
            secret = self.get_secret(item_name)
            result = {}
            for field_name in field_names:
                value = self.extract_field(secret, field_name)
                if value is None:
                    logger.warning(
                        "Field '%s' not found in secret '%s'",
                        field_name, item_name,
                    )
                    continue
                result[field_name] = value
        finally:
            self.logout()

        return result
