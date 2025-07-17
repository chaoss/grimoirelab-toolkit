#!/usr/bin/env python3
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

import argparse
import logging
import sys

from .secrets_manager_factory import SecretsManagerFactory

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)


def get_secret(
    secrets_manager_name: str, service_name: str, credential_name: str
) -> str:
    """
    Retrieve a secret from the secrets manager.

    Args:
        secrets_manager_name (str): The name of the secrets manager to be used
        service_name (str): The name of the service we want to access
        credential_name (str): The name of the credential we want to retrieve

    Returns:
        str: The credential retrieved

    Raises:
        ValueError: If the secrets manager is not supported or initialization fails
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
        _logger.error("Error retrieving secret: %s", e)
        raise


def main():
    """
    Main entry point for the command line interface.
    Parses arguments and retrieves secrets using the appropriate manager.
    """
    parser = argparse.ArgumentParser(
        description="Retrieve a secret from a specified secrets manager."
    )
    parser.add_argument(
        "manager",
        choices=["bitwarden", "hashicorp", "aws"],
        help="The name of the secrets manager to use.",
    )
    parser.add_argument(
        "service", help="The name of the service for which to retrieve the credential."
    )
    parser.add_argument("credential", help="The name of the credential to retrieve.")

    args = parser.parse_args()

    try:
        secret = get_secret(args.manager, args.service, args.credential)
        print(f"Retrieved {args.credential} for {args.service}: {secret}")
    except Exception as e:
        _logger.error("Failed to retrieve secret: %s", e)
        sys.exit(1)