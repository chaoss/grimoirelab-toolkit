#!/usr/bin/env python3
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

import argparse
import logging
import sys

from .secrets_manager_factory import SecretsManagerFactory

CREDENTIAL_MANAGER_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
CREDENTIAL_MANAGER_DEBUG_LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"

logger = logging.getLogger(__name__)


def get_secret(secrets_manager_name: str, service_name: str, credential_name: str) -> str:
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
            manager = SecretsManagerFactory.get_bitwarden_manager()
            return manager.get_secret(service_name, credential_name)

        elif secrets_manager_name == "hashicorp":
            manager = SecretsManagerFactory.get_hashicorp_manager()
            return manager.get_secret(service_name, credential_name)

        elif secrets_manager_name == "aws":
            manager = SecretsManagerFactory.get_aws_manager()
            return manager.get_secret(service_name, credential_name)

        else:
            raise ValueError(f"Unsupported secrets manager: {secrets_manager_name}")

    except Exception as e:
        logger.error("Error retrieving secret: %s", e)
        raise


def configure_logging(debug=False):
    """Configure credential_manager logging

    The function configures the log messages produced by Credential_manager.
    By default, log messages are sent to stderr. Set the parameter
    `debug` to activate the debug mode.

    :param debug: set the debug mode
    """
    if not debug:
        logging.basicConfig(level=logging.INFO, format=CREDENTIAL_MANAGER_LOG_FORMAT)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
    else:
        logging.basicConfig(level=logging.DEBUG, format=CREDENTIAL_MANAGER_DEBUG_LOG_FORMAT)


def main():
    """
    Main entry point for the command line interface.
    Parses arguments and retrieves secrets using the appropriate manager.

    :returns: None
    :rtype: None
    """
    parser = argparse.ArgumentParser(description="Retrieve a secret from a specified secrets manager.")
    parser.add_argument(
        "manager",
        choices=["bitwarden", "hashicorp", "aws"],
        help="The name of the secrets manager to use.",
    )
    parser.add_argument("service", help="The name of the service for which to retrieve the credential.")
    parser.add_argument("credential", help="The name of the credential to retrieve.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    configure_logging(args.debug)

    logging.info("Starting credental manager.")

    try:
        secret = get_secret(args.manager, args.service, args.credential)
        # return secret
        print(f"Retrieved {args.credential} for {args.service}: {secret}")
    except Exception as e:
        logger.error("Failed to retrieve secret: %s", e)
        sys.exit(1)
