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

import argparse
import getpass
import logging
import os
import sys

from .secrets_manager_factory import SecretsManagerFactory

CREDENTIAL_MANAGER_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
CREDENTIAL_MANAGER_DEBUG_LOG_FORMAT = (
    "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"
)

logger = logging.getLogger(__name__)


def get_secret(
    secrets_manager_name: str, service_name: str, credential_name: str
) -> str:
    """
    Retrieve a secret from the secrets manager.

    :param str secrets_manager_name: The name of the secrets manager to be used
    :param str service_name: The name of the service we want to access
    :param str credential_name: The name of the credential we want to retrieve
    :returns: The credential retrieved
    :rtype: str
    :raises ValueError: If the secrets manager is not supported or initialization fails
    """
    try:
        if secrets_manager_name == "bitwarden":
            # Get credentials from environment or prompt user
            email = os.environ.get("GRIMOIRELAB_BW_EMAIL")
            password = os.environ.get("GRIMOIRELAB_BW_PASSWORD")

            if not email or not password:
                if not email:
                    email = input("Bitwarden email: ")
                if not password:
                    password = getpass.getpass("Bitwarden master password: ")

            manager = SecretsManagerFactory.get_bitwarden_manager(email, password)
            return manager.get_secret(service_name, credential_name)

        elif secrets_manager_name == "hashicorp":
            # Get credentials from environment or prompt user
            vault_addr = os.environ.get("GRIMOIRELAB_VAULT_ADDR")
            token = os.environ.get("GRIMOIRELAB_VAULT_TOKEN")
            certificate = os.environ.get("GRIMOIRELAB_VAULT_CACERT")

            if not vault_addr or not token or not certificate:
                if not vault_addr:
                    vault_addr = input("Please enter vault address: ")
                if not token:
                    token = input("Please enter vault token: ")
                if not certificate:
                    certificate = input(
                        "Please enter path to a PEM-encoded CA certificate file: "
                    )

            manager = SecretsManagerFactory.get_hashicorp_manager(
                vault_addr, token, certificate
            )
            return manager.get_secret(service_name, credential_name)

        else:
            raise ValueError(f"Unsupported secrets manager: {secrets_manager_name}")

    except Exception as e:
        logger.error("Error retrieving secret: %s", e)
        raise


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


def configure_logging(debug=False):
    """Configure credential_manager logging

    The function configures the log messages produced by Credential_manager.
    By default, log messages are sent to stderr. Set the parameter
    `debug` to activate the debug mode.

    :param bool debug: set the debug mode
    """
    if not debug:
        logging.basicConfig(level=logging.INFO, format=CREDENTIAL_MANAGER_LOG_FORMAT)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    else:
        logging.basicConfig(
            level=logging.DEBUG, format=CREDENTIAL_MANAGER_DEBUG_LOG_FORMAT
        )


def main():
    """
    Main entry point for the command line interface.
    Parses arguments and retrieves secrets using the appropriate manager.

    :returns: None
    :rtype: None
    """
    parser = argparse.ArgumentParser(
        description="Retrieve a secret from a specified secrets manager."
    )
    parser.add_argument(
        "manager",
        choices=["bitwarden", "hashicorp"],
        help="The name of the secrets manager to use.",
    )
    parser.add_argument(
        "service", help="The name of the service for which to retrieve the credential."
    )
    parser.add_argument("credential", help="The name of the credential to retrieve.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    configure_logging(args.debug)

    logging.info("Starting credental manager.")

    try:
        secret = get_secret(args.manager, args.service, args.credential)
        return secret
    except Exception as e:
        logger.error("Failed to retrieve secret: %s", e)
        sys.exit(1)
