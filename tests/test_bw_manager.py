import unittest
import subprocess
import datetime
from datetime import timedelta
from unittest.mock import patch, MagicMock

from grimoirelab_toolkit.credential_manager.bw_manager import BitwardenManager


class TestBitwardenManager(unittest.TestCase):
    """BitwardenManager unit tests"""

    def setUp(self):
        self.email = "test@example.com"
        self.password = "test_password"
        self.manager = BitwardenManager(self.email, self.password)

    def tearDown(self):
        """Clean up after each test"""
        self.manager = None

    def test_initialization(self):
        """Test initialization of attributes"""
        self.assertEqual(self.manager._email, self.email)
        self.assertEqual(self.manager.session_key, None)
        self.assertEqual(self.manager.last_sync_time, None)
        self.assertEqual(self.manager.sync_interval, timedelta(minutes=3))
        self.assertEqual(self.manager.formatted_credentials, {})

    @patch("subprocess.run")
    def test_login_success(self, mock_run):
        """Test successful login"""

        # First call checks status - user not logged in
        mock_status = MagicMock()
        mock_status.returncode = 0
        mock_status.stdout = '{"status": "unauthenticated"}'  # User needs to log in

        # Second call simulates login, returns just the session key
        mock_login = MagicMock()
        mock_login.returncode = 0
        mock_login.stdout = "test_session_key"

        # Third call might be sync
        mock_sync = MagicMock()
        mock_sync.returncode = 0

        mock_run.side_effect = [mock_status, mock_login, mock_sync]

        session_key = self.manager._login(self.email, self.password)
        self.assertEqual(session_key, "test_session_key")

    @patch("subprocess.run")
    def test_login_locked_vault(self, mock_run):
        """Test login with locked vault"""

        # First call returns status check showing locked
        mock_status = MagicMock()
        mock_status.returncode = 0
        mock_status.stdout = '{"status": "locked", "userEmail": "test@example.com"}'

        # Second call is unlock attempt
        mock_unlock = MagicMock()
        mock_unlock.returncode = 0
        mock_unlock.stdout = "unlocked_session_key"

        # Third call is sync after unlock
        mock_sync = MagicMock()
        mock_sync.returncode = 0

        mock_run.side_effect = [mock_status, mock_unlock, mock_sync]

        session_key = self.manager._login(self.email, self.password)
        self.assertEqual(session_key, "unlocked_session_key")

    @patch("subprocess.run")
    def test_login_already_logged_in(self, mock_run):
        """Test login attempt when user is already logged in"""

        # First call to check status - showing user is authenticated
        mock_status = MagicMock()
        mock_status.returncode = 0
        mock_status.stdout = '{"status": "unlocked", "userEmail": "test@example.com"}'

        # If login is attempted, it would return the "already logged in" message
        mock_login = MagicMock()
        mock_login.returncode = 1
        mock_login.stderr = "You are already logged in as test@example.com."

        mock_run.side_effect = [mock_status]

    @patch("subprocess.run")
    def test_login_failure(self, mock_run):
        """Test login fail scenario"""
        mock_run.return_value = MagicMock(returncode=1, stderr="Login failed")

        session_key = self.manager._login(self.email, self.password)
        self.assertEqual(session_key, "")

    def test_validate_session_no_session(self):
        """Test session validation when there's no active session"""
        self.assertFalse(self.manager._validate_session())

    @patch("subprocess.run")
    def test_validate_session_valid(self, mock_run):
        """Test validation of valid session"""
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = (
            '{"status": "unlocked", '
            '"userEmail": "test@example.com", '
            '"sessionKey": "test_key"}'
        )
        mock_run.return_value = mock_response

        self.manager.session_key = "test_key"
        self.assertTrue(self.manager._validate_session())

    def test_should_sync_initial(self):
        """Test sync decision with no previous sync"""
        self.assertTrue(self.manager._should_sync())

    def test_should_sync_recent(self):
        """Test sync decision with recent sync"""
        self.manager.last_sync_time = datetime.datetime.now()
        self.assertFalse(self.manager._should_sync())

    def test_should_sync_old(self):
        """Test sync decision with too old sync"""
        self.manager.last_sync_time = datetime.datetime.now() - timedelta(minutes=5)
        self.assertTrue(self.manager._should_sync())

    @patch("subprocess.run")
    def test_sync_vault_success(self, mock_run):
        """Test successful vault sync"""
        mock_run.return_value = MagicMock(returncode=0)
        self.manager.session_key = "test_key"

        self.manager._sync_vault()
        self.assertIsNotNone(self.manager.last_sync_time)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_sync_vault_failure(self, mock_run):
        """Test vault sync failure"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.manager.session_key = "test_key"

        self.manager._sync_vault()
        self.assertIsNone(self.manager.last_sync_time)


    def test_format_credentials_complete(self):
        """Test formatting credentials"""
        raw_creds = {
            "name": "test_service",
            "login": {"username": "user", "password": "pass"},
            "fields": [{"name": "api_key", "value": "xyz"}],
        }

        formatted = self.manager._format_credentials(raw_creds)

        self.assertEqual(formatted["service_name"], "test_service")
        self.assertEqual(formatted["username"], "user")
        self.assertEqual(formatted["password"], "pass")
        self.assertEqual(formatted["api_key"], "xyz")

    def test_get_secret_success(self):
        """Test successful secret retrieval"""
        self.manager.formatted_credentials = {
            "service_name": "test_service",
            "test_credential": "test_value",
        }

        result = self.manager.get_secret("test_service", "test_credential")
        self.assertEqual(result, "test_value")

    def test_get_secret_missing(self):
        """Test secret retrieval with non existant credential"""
        self.manager.formatted_credentials = {"service_name": "test_service"}

        result = self.manager.get_secret("test_service", "missing_credential")
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
