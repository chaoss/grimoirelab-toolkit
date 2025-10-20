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
import subprocess
import datetime
from datetime import timedelta
from unittest.mock import patch, MagicMock

from grimoirelab_toolkit.credential_manager.bw_manager import BitwardenManager
from grimoirelab_toolkit.credential_manager.exceptions import SessionNotFoundError, CredentialNotFoundError

MOCK_BITWARDEN_RESPONSE = {
    "name": "test_service",
    "login": {"username": "test_user", "password": "test_pass"},
    "fields": [{"name": "api_key", "value": "test_key"}],
}


class TestBitwardenManager(unittest.TestCase):
    """BitwardenManager unit tests.

    Tests the BitwardenManager class which handles interaction with Bitwarden CLI
    for credential management.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.email = "test@example.com"
        self.password = "test_password"
        self.mock_bitwarden_response = {
            "name": "test_service",
            "login": {"username": "test_user", "password": "test_pass"},
            "fields": [{"name": "api_key", "value": "test_key"}],
        }

    def test_initialization(self):
        """Test initialization of attributes"""
        # Mock the login method to avoid real CLI calls
        with patch.object(BitwardenManager, "_login") as mock_login:
            mock_login.return_value = "test_session_key"

            manager = BitwardenManager(self.email, self.password)

            # Test basic attributes (session_key will be None since _login is mocked)
            self.assertEqual(manager._email, self.email)
            self.assertEqual(manager.last_sync_time, None)
            self.assertEqual(manager.sync_interval, timedelta(minutes=3))
            self.assertEqual(manager.formatted_credentials, {})

            # Verify _login was called during initialization
            mock_login.assert_called_once_with(self.email, self.password)

    @patch("subprocess.run")
    def test_login_success(self, mock_run):
        """Test successful login"""
        # Mock status check showing user needs to log in
        mock_status = MagicMock(returncode=0, stdout='{"status": "unauthenticated"}')

        # Mock successful login
        mock_login = MagicMock(returncode=0, stdout="test_session_key")

        # Mock successful sync
        mock_sync = MagicMock(returncode=0, stdout="")

        mock_run.side_effect = [mock_status, mock_login, mock_sync]

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        # Now test the _login method directly
        session_key = manager._login(self.email, self.password)
        self.assertEqual(session_key, "test_session_key")

    @patch("subprocess.run")
    def test_login_locked_vault(self, mock_run):
        """Test login with locked vault"""
        # Mock status check showing locked vault
        mock_status = MagicMock(returncode=0, stdout='{"status": "locked", "userEmail": "test@example.com"}')

        # Mock successful unlock
        mock_unlock = MagicMock(returncode=0, stdout="unlocked_session_key")

        # Mock successful sync
        mock_sync = MagicMock(returncode=0, stdout="")

        mock_run.side_effect = [mock_status, mock_unlock, mock_sync]

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        # Now test the _login method directly
        session_key = manager._login(self.email, self.password)
        self.assertEqual(session_key, "unlocked_session_key")

    @patch("subprocess.run")
    def test_login_already_logged_in(self, mock_run):
        """Test login attempt when user is already logged in"""

        # Mock status check showing user is already logged in
        mock_status = MagicMock(returncode=0, stdout='{"status": "unlocked", "userEmail": "test@example.com"}')

        mock_run.return_value = mock_status

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        # Test _login method - should raise exception because session_key extraction fails
        with self.assertRaises(SessionNotFoundError):
            manager._login(self.email, self.password)

    @patch("subprocess.run")
    def test_login_failure(self, mock_run):
        """Test login fail scenario"""

        # Mock failed login attempt
        mock_run.return_value = MagicMock(returncode=1, stderr="Login failed")

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        # Test _login method with failure - should raise SessionNotFoundError
        with self.assertRaises(SessionNotFoundError):
            manager._login(self.email, self.password)

    def test_validate_session_no_session(self):
        """Test session validation when there's no active session"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        self.assertFalse(manager._validate_session())

    @patch("subprocess.run")
    def test_validate_session_valid(self, mock_run):
        """Test validation of valid session"""
        # Mock status check for session validation
        mock_response = MagicMock(
            returncode=0, stdout='{"status": "unlocked", "userEmail": "test@example.com", "sessionKey": "test_key"}'
        )
        mock_run.return_value = mock_response

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.session_key = "test_key"
        self.assertTrue(manager._validate_session())

    def test_should_sync_initial(self):
        """Test sync decision with no previous sync"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        self.assertTrue(manager._should_sync())

    def test_should_sync_recent(self):
        """Test sync decision with recent sync"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.last_sync_time = datetime.datetime.now()
        self.assertFalse(manager._should_sync())

    def test_should_sync_old(self):
        """Test sync decision with too old sync"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.last_sync_time = datetime.datetime.now() - timedelta(minutes=5)
        self.assertTrue(manager._should_sync())

    @patch("subprocess.run")
    def test_sync_vault_success(self, mock_run):
        """Test successful vault sync"""
        # Mock successful sync
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.session_key = "test_key"
        manager._sync_vault()

        self.assertIsNotNone(manager.last_sync_time)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_sync_vault_failure(self, mock_run):
        """Test vault sync failure"""
        # Mock failed sync
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.session_key = "test_key"

        # Capture the last_sync_time before sync
        last_sync_before = manager.last_sync_time

        manager._sync_vault()

        # Should remain None when sync fails
        self.assertEqual(manager.last_sync_time, last_sync_before)

    def test_format_credentials_complete(self):
        """Test formatting credentials"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        raw_creds = self.mock_bitwarden_response.copy()

        formatted = manager._format_credentials(raw_creds)

        self.assertEqual(formatted["service_name"], "test_service")
        self.assertEqual(formatted["username"], "test_user")
        self.assertEqual(formatted["password"], "test_pass")
        self.assertEqual(formatted["api_key"], "test_key")

    def test_get_secret_success(self):
        """Test successful secret retrieval"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.formatted_credentials = {
            "service_name": "test_service",
            "test_credential": "test_value",
        }

        result = manager.get_secret("test_service", "test_credential")
        self.assertEqual(result, "test_value")

    def test_get_secret_missing(self):
        """Test secret retrieval with non existant credential"""
        # Create manager with mocked _login to avoid init issues
        with patch.object(BitwardenManager, "_login", return_value=None):
            manager = BitwardenManager(self.email, self.password)

        manager.formatted_credentials = {
            "service_name": "test_service",
            "other_credential": "other_value",
        }

        with self.assertRaises(CredentialNotFoundError):
            manager.get_secret("test_service", "missing_credential")


if __name__ == "__main__":
    unittest.main(warnings="ignore")
