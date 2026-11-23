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


import dataclasses
import logging
import typing

from ..introspect import inspect_signature_parameters
from .exceptions import CredentialManagerError

logger = logging.getLogger(__name__)


class Secret:
    """Description of a parameter with a sensitive value.

    Use it in the annotations of the parameters of a credential
    manager's constructor, instead of a plain description, to mark
    those parameters with values that must not be logged or
    displayed (e.g. tokens or passwords).

    :param str help: description of the parameter
    """

    def __init__(self, help: str):
        self.help = help


class CredentialManager:
    """Base class for credential managers.

    Defines the interface that all credential manager implementations
    must follow. Provides a concrete `resolve_credentials` method
    (Template Method) that orchestrates the shared workflow of
    logging in, fetching a secret, extracting fields, and logging out.

    Subclasses must implement `get_secret` and `extract_field`.
    Subclasses that require authentication (e.g. Bitwarden) should
    override `login` and `logout`.

    Subclasses that set their own `NAME` are available to applications
    (see `available_managers`). The name is not inherited, so subclasses
    of an available manager must set theirs, and it must be unique
    among all managers. The parameters of their constructors are
    the configuration of the manager, so each one must be annotated
    with its description, e.g. `Annotated[str, "Vault URL"]`, or
    `Annotated[str, Secret("Vault token")]` for sensitive values.
    Parameters without a default value are required.

    :cvar NAME: identifier of the manager
    :cvar TITLE: human readable name of the manager
    :cvar PREFIX: short prefix that applications can use to name the
        parameters of the manager (e.g. command line arguments or
        environment variables)
    :cvar EXTRA: package extra that installs the dependencies of
        the manager, if any
    """

    NAME: str | None = None
    TITLE: str | None = None
    PREFIX: str | None = None
    EXTRA: str | None = None

    def get_secret(self, secret_name: str) -> dict:
        """Retrieve a secret item from the vault.

        :param str secret_name: The name/path of the secret item

        :returns: Dictionary containing the secret data
        :rtype: dict
        """
        raise NotImplementedError

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

    def logout(self):
        """Log out from the secrets manager. No-op by default."""

    def resolve_credentials(
        self,
        secret_name: str,
        field_names: list[str],
    ) -> dict[str, str]:
        """Resolve credentials from the secrets manager.

        Fetches a secret item and extracts the requested fields.
        Handles login/logout lifecycle automatically.

        :param str secret_name: Name/path of the secret item in the vault
        :param list field_names: List of field names to extract

        :returns: Dict mapping field names to their resolved values.
            Only fields that were found are included.
        :rtype: dict[str, str]

        :raises ValueError: If secret_name is empty
        """
        if not secret_name:
            raise ValueError("Missing item name")

        if not field_names:
            return {}

        self.login()
        try:
            secret = self.get_secret(secret_name)
            result = {}
            for field_name in field_names:
                value = self.extract_field(secret, field_name)
                if value is None:
                    logger.warning(
                        "Field '%s' not found in secret '%s'",
                        field_name,
                        secret_name,
                    )
                    continue
                result[field_name] = value
        finally:
            self.logout()

        return result


@dataclasses.dataclass(frozen=True)
class ManagerParameter:
    """Configuration parameter of a credential manager.

    :param name: name of the parameter; it is the key used to give
        its value to `create_credential_manager`
    :param help: short description of the parameter
    :param required: whether the parameter must have a value
    :param secret: whether the value is sensitive (e.g. a token or
        a password), so applications must not log or display it
    :param default: value used when the parameter is not given
    """

    name: str
    help: str
    required: bool = False
    secret: bool = False
    default: typing.Any = None


@dataclasses.dataclass(frozen=True)
class ManagerSpec:
    """Description of a credential manager.

    :param name: unique identifier of the manager
    :param title: human readable name of the manager
    :param prefix: short prefix that applications can use to name
        the parameters of this manager (e.g. command line arguments
        or environment variables)
    :param parameters: configuration parameters of the manager
    :param manager_class: class that implements the manager
    :param extra: package extra that installs the dependencies
        of the manager, if any
    """

    name: str
    title: str
    prefix: str
    parameters: tuple[ManagerParameter, ...]
    manager_class: type[CredentialManager]
    extra: str | None = None


def available_managers() -> dict[str, ManagerSpec]:
    """Return the descriptions of the available credential managers.

    The available credential managers are the subclasses of
    `CredentialManager` that set their own `NAME`. Their descriptions are
    obtained by introspection, from the parameters of their
    constructors. Applications can use these descriptions to build
    their own configuration (e.g. command line arguments or
    environment variables) without knowing the details of each
    manager.

    Managers are described even when their dependencies are not
    installed. In that case, they will fail when they are created.

    :returns: a dict of `ManagerSpec` objects, indexed by the name
        of the manager

    :raises CredentialManagerError: when two managers have the same name
    """
    return {cls.NAME: _describe_manager(cls) for cls in _find_manager_classes()}


def create_credential_manager(name: str, **config) -> CredentialManager:
    """Create a credential manager by its name.

    The configuration of the manager is given as keyword arguments,
    using the names of its parameters (see `available_managers`).
    Parameters with `None` or empty values are considered as not
    given, so the manager uses its default values for them.

    :param name: name of the credential manager
    :param config: values of the parameters of the manager

    :returns: a credential manager instance

    :raises ValueError: when the manager is not available, any of
        its required parameters is missing, or any of the given
        parameters is unknown
    :raises CredentialManagerError: when the dependencies of the
        manager are not installed or two managers have the same name
    """
    specs = available_managers()

    if name not in specs:
        raise ValueError(f"Unknown credential manager: '{name}'")

    spec = specs[name]
    parameters = [param.name for param in spec.parameters]

    unknown = sorted(set(config) - set(parameters))
    if unknown:
        msg = f"Unknown parameters for '{name}' credential manager: {', '.join(unknown)}"
        raise ValueError(msg)

    config = {key: value for key, value in config.items() if value is not None and value != ""}

    missing = [
        param.name for param in spec.parameters if param.required and param.name not in config
    ]
    if missing:
        msg = f"Missing parameters for '{name}' credential manager: {', '.join(missing)}"
        raise ValueError(msg)

    return spec.manager_class(**config)


def _find_manager_classes():
    """Find the subclasses of `CredentialManager` that set their own name"""

    found = {}
    visited = set()
    pending = list(CredentialManager.__subclasses__())

    while pending:
        cls = pending.pop(0)

        # With multiple inheritance, a class can be found more than once
        if cls in visited:
            continue
        visited.add(cls)

        pending.extend(cls.__subclasses__())

        # Names are not inherited, so a subclass of an available
        # manager doesn't replace it unless it sets its own name
        name = cls.__dict__.get("NAME")
        if not name:
            continue

        if name in found:
            first = found[name]
            msg = (
                f"Credential manager name '{name}' is used by "
                f"'{first.__module__}.{first.__qualname__}' "
                f"and '{cls.__module__}.{cls.__qualname__}'"
            )
            raise CredentialManagerError(msg)

        found[name] = cls

    return list(found.values())


def _describe_manager(cls) -> ManagerSpec:
    """Describe a manager using the parameters of its constructor"""

    parameters = []

    for param in inspect_signature_parameters(cls.__init__, excluded=("self",)):
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        # The description is the first metadata element of 'Annotated'
        metadata = getattr(param.annotation, "__metadata__", ())
        description = metadata[0] if metadata else ""
        required = param.default is param.empty

        parameters.append(
            ManagerParameter(
                name=param.name,
                help=description.help if isinstance(description, Secret) else description,
                required=required,
                secret=isinstance(description, Secret),
                default=None if required else param.default,
            )
        )

    return ManagerSpec(
        name=cls.NAME,
        title=cls.TITLE or cls.NAME,
        prefix=cls.PREFIX or cls.NAME,
        parameters=tuple(parameters),
        manager_class=cls,
        extra=cls.EXTRA,
    )
