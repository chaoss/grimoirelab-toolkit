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

import gc
import unittest
from typing import Annotated
from unittest.mock import patch

from grimoirelab_toolkit.credential_manager import (
    BitwardenManager,
    CredentialManager,
    CredentialManagerError,
    HashicorpManager,
    ManagerSpec,
    Secret,
    available_managers,
    create_credential_manager,
)

HC_MANAGER_HVAC = "grimoirelab_toolkit.credential_manager.hc_manager.hvac"


class BaseDummyManager(CredentialManager):
    """Manager without a name, so it is not available"""


class DummyManager(BaseDummyManager):
    """Manager defined outside the toolkit"""

    NAME = "dummy"

    def __init__(
        self,
        user: Annotated[str, "User name"],
        password: Annotated[str, Secret("User password")],
        timeout: int = 10,
        **kwargs,
    ):
        self.user = user
        self.password = password
        self.timeout = timeout


class DummyManagerSubclass(DummyManager):
    """Subclass that doesn't set its own name, so it is not available"""


class TestAvailableManagers(unittest.TestCase):
    """Tests for available_managers function."""

    def test_managers(self):
        """Test whether the built-in managers are described."""

        specs = available_managers()

        for name, spec in specs.items():
            self.assertIsInstance(spec, ManagerSpec)
            self.assertEqual(spec.name, name)

        bw = specs["bitwarden"]
        self.assertEqual(bw.title, "Bitwarden")
        self.assertEqual(bw.prefix, "bw")
        self.assertIsNone(bw.extra)
        self.assertIs(bw.manager_class, BitwardenManager)
        self.assertListEqual(
            [(p.name, p.help, p.required, p.secret, p.default) for p in bw.parameters],
            [
                ("client_id", "Bitwarden API client ID", True, False, None),
                ("client_secret", "Bitwarden API client secret", True, True, None),
                ("master_password", "Bitwarden master password", True, True, None),
            ],
        )

        hc = specs["hashicorp"]
        self.assertEqual(hc.title, "HashiCorp Vault")
        self.assertEqual(hc.prefix, "vault")
        self.assertEqual(hc.extra, "hashicorp-manager")
        self.assertIs(hc.manager_class, HashicorpManager)
        self.assertListEqual(
            [(p.name, p.help, p.required, p.secret, p.default) for p in hc.parameters],
            [
                ("url", "HashiCorp Vault URL", True, False, None),
                ("token", "HashiCorp Vault authentication token", True, True, None),
                (
                    "certificate",
                    "Path to CA certificate for HashiCorp Vault TLS verification",
                    False,
                    False,
                    None,
                ),
                (
                    "mount_point",
                    "Path where the KV version 2 secrets engine is mounted",
                    False,
                    False,
                    "secret",
                ),
            ],
        )

    def test_managers_without_name(self):
        """Test whether managers without a name are not available."""

        classes = [spec.manager_class for spec in available_managers().values()]

        self.assertNotIn(CredentialManager, classes)
        self.assertNotIn(BaseDummyManager, classes)

    def test_managers_with_inherited_name(self):
        """Test whether subclasses that inherit the name are not available."""

        classes = [spec.manager_class for spec in available_managers().values()]

        self.assertIn(DummyManager, classes)
        self.assertNotIn(DummyManagerSubclass, classes)
        self.assertIs(available_managers()["dummy"].manager_class, DummyManager)

        manager = create_credential_manager("dummy", user="alice", password="secret")
        self.assertIs(type(manager), DummyManager)

    def test_managers_with_same_name(self):
        """Test whether it fails when two managers have the same name."""

        class FirstManager(CredentialManager):
            NAME = "duplicated"

        class SecondManager(CredentialManager):
            NAME = "duplicated"

        expected = (
            r"Credential manager name 'duplicated' is used by "
            r"'test_credential_manager\..*FirstManager' "
            r"and 'test_credential_manager\..*SecondManager'"
        )

        with self.assertRaisesRegex(CredentialManagerError, expected):
            available_managers()

        with self.assertRaisesRegex(CredentialManagerError, expected):
            create_credential_manager("dummy", user="alice", password="secret")

        # Remove the managers, so they don't affect other tests
        del FirstManager, SecondManager
        gc.collect()

        self.assertNotIn("duplicated", available_managers())

    def test_managers_defined_outside(self):
        """Test whether any subclass of CredentialManager is described."""

        dummy = available_managers()["dummy"]

        # Title and prefix are the name when they are not set
        self.assertEqual(dummy.title, "dummy")
        self.assertEqual(dummy.prefix, "dummy")
        self.assertIsNone(dummy.extra)
        self.assertIs(dummy.manager_class, DummyManager)

        # Parameters without description have an empty help and
        # variable arguments are not parameters of the manager
        self.assertListEqual(
            [(p.name, p.help, p.required, p.secret, p.default) for p in dummy.parameters],
            [
                ("user", "User name", True, False, None),
                ("password", "User password", True, True, None),
                ("timeout", "", False, False, 10),
            ],
        )

    def test_managers_without_dependencies(self):
        """Test whether managers are described when their dependencies are missing."""

        with patch(HC_MANAGER_HVAC, None):
            specs = available_managers()

        self.assertIn("hashicorp", specs)


class TestCreateCredentialManager(unittest.TestCase):
    """Tests for create_credential_manager function."""

    @patch("shutil.which", return_value="/usr/bin/bw")
    def test_bitwarden(self, mock_which):
        """Test whether a Bitwarden manager is created."""

        manager = create_credential_manager(
            "bitwarden",
            client_id="cid",
            client_secret="csecret",
            master_password="mpass",
        )

        self.assertIsInstance(manager, BitwardenManager)
        self.assertEqual(manager.client_id, "cid")
        self.assertEqual(manager.client_secret, "csecret")
        self.assertEqual(manager.master_password, "mpass")

    @patch(HC_MANAGER_HVAC)
    def test_hashicorp(self, mock_hvac):
        """Test whether a HashiCorp Vault manager is created."""

        manager = create_credential_manager(
            "hashicorp",
            url="http://vault-url",
            token="vtoken",
            certificate="/ca.crt",
            mount_point="grimoirelab",
        )

        self.assertIsInstance(manager, HashicorpManager)
        self.assertEqual(manager.mount_point, "grimoirelab")
        mock_hvac.Client.assert_called_once_with(
            url="http://vault-url", token="vtoken", verify="/ca.crt"
        )

    def test_manager_defined_outside(self):
        """Test whether a manager defined outside the toolkit is created."""

        manager = create_credential_manager("dummy", user="alice", password="secret")

        self.assertIsInstance(manager, DummyManager)
        self.assertEqual(manager.user, "alice")
        self.assertEqual(manager.password, "secret")
        self.assertEqual(manager.timeout, 10)

    @patch(HC_MANAGER_HVAC)
    def test_parameters_without_value(self, mock_hvac):
        """Test whether parameters with None or empty values are ignored."""

        manager = create_credential_manager(
            "hashicorp",
            url="http://vault-url",
            token="vtoken",
            certificate=None,
            mount_point="",
        )

        self.assertEqual(manager.mount_point, "secret")
        mock_hvac.Client.assert_called_once_with(
            url="http://vault-url", token="vtoken", verify=None
        )

    def test_unknown_manager(self):
        """Test whether it fails when the manager is not available."""

        with self.assertRaisesRegex(ValueError, "Unknown credential manager: 'keepass'"):
            create_credential_manager("keepass")

    def test_unknown_parameters(self):
        """Test whether it fails when a parameter is not supported by the manager."""

        with self.assertRaisesRegex(
            ValueError, "Unknown parameters for 'bitwarden' credential manager: url, vault_token"
        ):
            create_credential_manager(
                "bitwarden",
                client_id="cid",
                client_secret="csecret",
                master_password="mpass",
                vault_token="vtoken",
                url="http://vault-url",
            )

    def test_missing_parameters(self):
        """Test whether it fails when required parameters are missing."""

        with self.assertRaisesRegex(
            ValueError,
            "Missing parameters for 'bitwarden' credential manager: client_secret, master_password",
        ):
            create_credential_manager("bitwarden", client_id="cid", client_secret="")

    def test_missing_dependencies(self):
        """Test whether it fails when the dependencies of the manager are not installed."""

        expected = (
            "'hashicorp' credential manager is not available; "
            r"install it with 'grimoirelab-toolkit\[hashicorp-manager\]'"
        )

        with (
            patch(HC_MANAGER_HVAC, None),
            self.assertRaisesRegex(CredentialManagerError, expected),
        ):
            create_credential_manager("hashicorp", url="http://vault-url", token="vtoken")


if __name__ == "__main__":
    unittest.main()
