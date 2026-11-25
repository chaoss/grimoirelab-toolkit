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


# The built-in managers must be imported, so they are registered
# as subclasses of 'CredentialManager' (see 'available_managers')
from .bw_manager import BitwardenManager
from .credential_manager import (
    CredentialManager,
    ManagerParameter,
    ManagerSpec,
    Secret,
    available_managers,
    create_credential_manager,
)
from .exceptions import (
    BitwardenCLIError,
    CredentialManagerError,
    CredentialNotFoundError,
    HashicorpVaultError,
    InvalidCredentialsError,
)
from .hc_manager import HashicorpManager

__all__ = [
    "BitwardenCLIError",
    "BitwardenManager",
    "CredentialManager",
    "CredentialManagerError",
    "CredentialNotFoundError",
    "HashicorpManager",
    "HashicorpVaultError",
    "InvalidCredentialsError",
    "ManagerParameter",
    "ManagerSpec",
    "Secret",
    "available_managers",
    "create_credential_manager",
]
