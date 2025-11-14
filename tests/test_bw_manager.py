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
# Author:
#     Alberto Ferrer Sánchez (alberefe@gmail.com)
#

import unittest
from unittest.mock import patch, MagicMock, call

from grimoirelab_toolkit.credential_manager.bw_manager import BitwardenManager
from grimoirelab_toolkit.credential_manager.exceptions import (
    InvalidCredentialsError,
    BitwardenCLIError,
    CredentialNotFoundError,
)


class TestBitwardenManager(unittest.TestCase):
    """Tests for BitwardenManager class."""

    def setUp(self):
        """Set up common test fixtures."""

        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.master_password = "test_master_password"
        self.session_key = "test_session_key"

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_initialization_success(self, mock_which):
        """Test successful initialization with valid credentials."""

        mock_which.return_value = "/usr/bin/bw"

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )

        self.assertEqual(manager.client_id, self.client_id)
        self.assertEqual(manager.client_secret, self.client_secret)
        self.assertEqual(manager.master_password, self.master_password)
        self.assertIsNone(manager.session_key)
        self.assertEqual(manager.bw_path, "/usr/bin/bw")
        self.assertIn("BW_CLIENTID", manager.env)
        self.assertIn("BW_CLIENTSECRET", manager.env)

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_initialization_bw_not_found(self, mock_which):
        """Test initialization fails when bw CLI is not found."""

        mock_which.return_value = None

        with self.assertRaises(BitwardenCLIError) as context:
            BitwardenManager(self.client_id, self.client_secret, self.master_password)

        self.assertIn("Bitwarden CLI (bw) not found in PATH", str(context.exception))

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_login_success(self, mock_which, mock_run):
        """Test successful login and unlock."""

        mock_which.return_value = "/usr/bin/bw"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Logged in!", stderr=""),  # login
            MagicMock(returncode=0, stdout="test_session_key\n", stderr=""),  # unlock
        ]

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        session_key = manager.login()

        self.assertEqual(session_key, "test_session_key")
        self.assertEqual(manager.session_key, "test_session_key")
        self.assertEqual(mock_run.call_count, 2)

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_login_failure(self, mock_which, mock_run):
        """Test login failure with invalid credentials."""

        mock_which.return_value = "/usr/bin/bw"
        mock_run.return_value = MagicMock(returncode=1, stderr="Invalid credentials")

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )

        with self.assertRaises(InvalidCredentialsError):
            manager.login()

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_unlock_failure(self, mock_which, mock_run):
        """Test unlock failure after successful login."""

        mock_which.return_value = "/usr/bin/bw"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Logged in!", stderr=""),  # login
            MagicMock(returncode=1, stderr="Unlock failed", stdout=""),  # unlock
        ]

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )

        with self.assertRaises(BitwardenCLIError) as context:
            manager.login()

        self.assertIn("Failed to unlock vault", str(context.exception))

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_get_secret_success(self, mock_which, mock_run):
        """Test successful secret retrieval."""

        mock_which.return_value = "/usr/bin/bw"
        secret_result = MagicMock(
            returncode=0, stdout='{"name":"github","login":{"password":"secret123"}}'
        )
        mock_run.return_value = secret_result

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        manager.session_key = self.session_key
        result = manager.get_secret("github")

        # Now returns a parsed dict, not subprocess result
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "github")
        self.assertEqual(result["login"]["password"], "secret123")
        mock_run.assert_called_once()

        # Verify the get_secret call includes session key
        call_args = mock_run.call_args
        self.assertEqual(
            call_args[0][0],
            ["/usr/bin/bw", "get", "item", "github", "--session", self.session_key],
        )
        self.assertTrue(call_args[1]["capture_output"])
        self.assertTrue(call_args[1]["text"])

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_get_secret_returns_parsed_dict(self, mock_which, mock_run):
        """Test that get_secret returns parsed dict from JSON response."""

        mock_which.return_value = "/usr/bin/bw"
        secret_result = MagicMock(returncode=0, stdout='{"data":"value"}', stderr="")
        mock_run.return_value = secret_result

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        manager.session_key = self.session_key
        result = manager.get_secret("my_item")

        # The method returns a parsed dict, not subprocess result
        self.assertIsInstance(result, dict)
        self.assertEqual(result["data"], "value")

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_get_secret_not_found(self, mock_which, mock_run):
        """Test get_secret raises error when item not found."""

        mock_which.return_value = "/usr/bin/bw"
        secret_result = MagicMock(returncode=1, stderr="Not found")
        mock_run.return_value = secret_result

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        manager.session_key = self.session_key

        with self.assertRaises(CredentialNotFoundError) as context:
            manager.get_secret("nonexistent")

        self.assertIn("Credential not found", str(context.exception))

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_get_secret_invalid_json(self, mock_which, mock_run):
        """Test get_secret raises error when response is not valid JSON."""

        mock_which.return_value = "/usr/bin/bw"
        secret_result = MagicMock(returncode=0, stdout="not valid json")
        mock_run.return_value = secret_result

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        manager.session_key = self.session_key

        with self.assertRaises(BitwardenCLIError) as context:
            manager.get_secret("github")

        self.assertIn("Invalid JSON response", str(context.exception))

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_logout_success(self, mock_which, mock_run):
        """Test successful logout clears session data."""

        mock_which.return_value = "/usr/bin/bw"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Logged in!"),  # login
            MagicMock(returncode=0, stdout="test_session_key"),  # unlock
            MagicMock(returncode=0, stdout="You have logged out."),  # logout
        ]

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        manager.login()

        self.assertEqual(manager.session_key, "test_session_key")

        manager.logout()

        self.assertIsNone(manager.session_key)
        self.assertEqual(mock_run.call_count, 3)

        # Verify logout was called
        logout_call = call(
            ["/usr/bin/bw", "logout"], capture_output=True, text=True, env=manager.env
        )
        self.assertIn(logout_call, mock_run.call_args_list)

    @patch("grimoirelab_toolkit.credential_manager.bw_manager.subprocess.run")
    @patch("grimoirelab_toolkit.credential_manager.bw_manager.shutil.which")
    def test_logout_failure_still_clears_data(self, mock_which, mock_run):
        """Test logout still clears session data even when command fails."""

        mock_which.return_value = "/usr/bin/bw"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Logged in!"),  # login
            MagicMock(returncode=0, stdout="test_session_key"),  # unlock
            MagicMock(returncode=1, stderr="Logout failed"),  # logout
        ]

        manager = BitwardenManager(
            self.client_id, self.client_secret, self.master_password
        )
        manager.login()
        manager.logout()

        self.assertIsNone(manager.session_key)
