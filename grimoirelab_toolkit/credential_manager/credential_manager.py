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


import logging

from .secrets_manager_factory import SecretsManagerFactory

logger = logging.getLogger(__name__)

SUPPORTED_MANAGERS = ("bitwarden", "hashicorp")


def _extract_bitwarden_field(item, field_name):
    """Extract a field value from a Bitwarden item.

    Searches in the 'login' dict first, then in the 'fields' array.

    :param dict item: The Bitwarden item dictionary
    :param str field_name: The name of the field to extract

    :returns: The field value or None if not found
    :rtype: str or None
    """
    # Check login fields first (username, password, etc.)
    login_data = item.get('login', {})
    if login_data and field_name in login_data:
        return login_data[field_name]

    # Check custom fields array
    for field in item.get('fields', []):
        if field.get('name') == field_name:
            return field.get('value')

    return None


def _extract_hashicorp_field(secret, field_name):
    """Extract a field value from a HashiCorp Vault secret.

    Reads from secret['data']['data'][field_name].

    :param dict secret: The HashiCorp Vault secret dictionary
    :param str field_name: The name of the field to extract

    :returns: The field value or None if not found
    :rtype: str or None
    """
    secret_data = secret.get('data', {}).get('data', {})
    return secret_data.get(field_name)


def resolve_credentials(
    manager_type: str,
    manager_config: dict,
    item_name: str,
    field_mapping: dict[str, str],
) -> dict[str, str]:
    """Resolve credentials from a secrets manager.

    Fetches a secret item from the specified secrets manager and extracts
    the requested fields. This function works independently of any CLI
    framework, making it usable from any caller (BackendCommand, KingArthur,
    scripts, etc.).

    :param str manager_type: The secrets manager to use
        ('bitwarden' or 'hashicorp')
    :param dict manager_config: Manager-specific authentication config.
        Bitwarden: {'client_id', 'client_secret', 'master_password'}
        HashiCorp: {'vault_url', 'token', 'certificate'}
    :param str item_name: Name/path of the secret item in the vault
    :param dict field_mapping: Maps secret field names to output parameter
        names. Example: {'api_key': 'api_token', 'username': 'user'}

    :returns: Dict mapping output parameter names to resolved string values.
        Only fields that were found are included.
    :rtype: dict[str, str]

    :raises ValueError: If manager_type is unsupported or item_name is empty
    :raises CredentialNotFoundError: If the secret item is not found
    :raises CredentialManagerError: If manager authentication fails
    """
    if manager_type not in SUPPORTED_MANAGERS:
        raise ValueError(
            f"Unsupported secrets manager: '{manager_type}'. "
            f"Supported: {', '.join(SUPPORTED_MANAGERS)}"
        )

    if not item_name:
        raise ValueError("item_name must be non-empty")

    if not field_mapping:
        return {}

    result = {}

    if manager_type == 'bitwarden':
        manager = SecretsManagerFactory.get_bitwarden_manager(
            manager_config['client_id'],
            manager_config['client_secret'],
            manager_config['master_password'],
        )
        manager.login()
        try:
            item = manager.get_secret(item_name)
            for secret_field, output_param in field_mapping.items():
                value = _extract_bitwarden_field(item, secret_field)
                if value is None:
                    logger.warning(
                        "Field '%s' not found in Bitwarden item '%s'",
                        secret_field, item_name,
                    )
                    continue
                result[output_param] = value
        finally:
            manager.logout()

    elif manager_type == 'hashicorp':
        manager = SecretsManagerFactory.get_hashicorp_manager(
            manager_config['vault_url'],
            manager_config['token'],
            manager_config.get('certificate'),
        )
        secret = manager.get_secret(item_name)
        for secret_field, output_param in field_mapping.items():
            value = _extract_hashicorp_field(secret, secret_field)
            if value is None:
                logger.warning(
                    "Field '%s' not found in HashiCorp secret '%s'",
                    secret_field, item_name,
                )
                continue
            result[output_param] = value

    return result
