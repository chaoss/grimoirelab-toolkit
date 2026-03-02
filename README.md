# GrimoireLab Toolkit [![Build Status](https://github.com/chaoss/grimoirelab-toolkit/workflows/tests/badge.svg)](https://github.com/chaoss/grimoirelab-toolkit/actions?query=workflow:tests+branch:main+event:push) [![Coverage Status](https://img.shields.io/coveralls/chaoss/grimoirelab-toolkit.svg)](https://coveralls.io/r/chaoss/grimoirelab-toolkit?branch=main)

Toolkit of common functions used across GrimoireLab projects.

This package provides a library composed by functions widely used in other
GrimoireLab projects. These function deal with date handling, introspection,
URIs/URLs, among other topics.

## Requirements

 * Python >= 3.8

You will also need some other libraries for running the tool, you can find the
whole list of dependencies in [pyproject.toml](pyproject.toml) file.

## Installation

There are several ways to install GrimoireLab Toolkit on your system: packages or source 
code using Poetry or pip.

### PyPI

GrimoireLab Toolkit can be installed using pip, a tool for installing Python packages. 
To do it, run the next command:
```
$ pip install grimoirelab-toolkit
```

### Source code

To install from the source code you will need to clone the repository first:
```
$ git clone https://github.com/chaoss/grimoirelab-toolkit
$ cd grimoirelab-toolkit
```

Then use pip or Poetry to install the package along with its dependencies.

#### Pip
To install the package from local directory run the following command:
```
$ pip install .
```
In case you are a developer, you should install GrimoireLab Toolkit in editable mode:
```
$ pip install -e .
```

#### Poetry
We use [poetry](https://python-poetry.org/) for dependency management and 
packaging. You can install it following its [documentation](https://python-poetry.org/docs/#installation).
Once you have installed it, you can install GrimoireLab Toolkit and the dependencies in 
a project isolated environment using:
```
$ poetry install
```
To spaw a new shell within the virtual environment use:
```
$ poetry shell
```

## Credential Manager Library

This is a module made to retrieve credentials from different secrets management systems like Bitwarden.
It accesses the secrets management service, looks for the desired credential and returns it in String form.

To use the module in your python code

### Bitwarden

```
from grimoirelab_toolkit.credential_manager import BitwardenManager


# Instantiate the Bitwarden manager using the api credentials for login
bw_manager = BitwardenManager("your_client_id", "your_client_secret", "your_master_password")

# Login
bw_manager.login()

# Retrieve a secret from Bitwarden
username = bw_manager.get_secret("github")
password = bw_manager.get_secret("elasticsearch")

# Logout
bw_manager.logout()
```


#### Response format

When calling `get_secret(item_name)`, the method returns a JSON object with the following structure:

_NOTE: the parameter "item_name" corresponds with the field "name" of the json. That's the name of the item._
(in this case, GitHub)


##### Example Response

  ```json
  {
    "passwordHistory": [
      {
        "lastUsedDate": "2024-11-05T10:27:18.411Z",
        "password": "previous_password_value_1"
      },
      {
        "lastUsedDate": "2024-11-05T09:20:06.512Z",
        "password": "previous_password_value_2"
      }
    ],
    "revisionDate": "2025-05-11T14:40:19.456Z",
    "creationDate": "2024-10-30T18:56:41.023Z",
    "object": "item",
    "id": "91300380-620f-4707-8de1-b21901383315",
    "organizationId": null,
    "folderId": null,
    "type": 1,
    "reprompt": 0,
    "name": "GitHub",
    "notes": null,
    "favorite": false,
    "fields": [
      {
        "name": "api-token",
        "value": "TOKEN"
        "type": 0,
        "linkedId": null
      },
      {
        "name": "api_key",
        "value": "APIKEY",
        "type": 0,
        "linkedId": null
      }
    ],
    "login": {
      "uris": [],
      "username": "your_username",
      "password": "your_password",
      "totp": null,
      "passwordRevisionDate": "2024-11-05T10:27:18.411Z"
    },
    "collectionIds": [],
    "attachments": []
  }
```

  Field Descriptions

  - passwordHistory: Array of previously used passwords with timestamps
  - revisionDate: Last modification timestamp (ISO 8601 format)
  - creationDate: Item creation timestamp (ISO 8601 format)
  - object: Always "item" for credential items
  - id: Unique identifier for this item
  - organizationId: Organization ID if shared, null for personal items
  - folderId: Folder ID if organized, null otherwise
  - type: Item type (1 = login, 2 = secure note, 3 = card, 4 = identity)
  - name: Display name of the credential item (name used as argument in get_secret())
  - notes: Optional notes field
  - favorite: Boolean indicating if item is favorited
  - fields: Array of custom fields with name-value pairs
    - name: Field name
    - value: Field value (can contain secrets)
    - type: Field type (0 = text, 1 = hidden, 2 = boolean)
  - login: Login credentials object
    - username: Login username
    - password: Login password
    - totp: TOTP secret for 2FA (if configured)
    - uris: Array of associated URIs/URLs
    - passwordRevisionDate: Last password change timestamp
  - collectionIds: Array of collection IDs this item belongs to
  - attachments: Array of file attachments

The module uses the [Bitwarden CLI](https://bitwarden.com/help/cli/) to interact with Bitwarden.

### HashiCorp Vault


#### Installing the dependency

This module uses hvac library, which is set as optional module in pyproject.toml.

 1. Normal install: poetry install --with hashicorp-manager
 2. For development: poetry install --with hashicorp-manager --with dev


#### Example use

```python
from grimoirelab_toolkit.credential_manager.hc_manager import HashicorpManager


# Instantiate the HashiCorp Vault manager using the vault URL and token
# The certificate can be a boolean (True/False) or a path to a CA bundle file
hc_manager = HashicorpManager("https://vault.example.com", "your_token", certificate=True)

# Retrieve a secret from HashiCorp Vault
github_secret = hc_manager.get_secret("github")
elasticsearch_secret = hc_manager.get_secret("elasticsearch")
```

#### Response format

When calling `get_secret(item_name)`, the method returns a JSON object with the following structure:

_NOTE: the parameter "item_name" corresponds to the secret path in HashiCorp Vault._

##### Example Response

```json
{
  "request_id": "d09e2bb5-00ee-576b-6078-5d291d35ccc3",
  "lease_id": "",
  "renewable": false,
  "lease_duration": 0,
  "data": {
    "data": {
      "username": "test_user",
      "password": "test_pass",
      "api_key": "test_key"
    },
    "metadata": {
      "created_time": "2024-11-23T12:20:59.985132927Z",
      "custom_metadata": null,
      "deletion_time": "",
      "destroyed": false,
      "version": 1
    }
  },
  "wrap_info": null,
  "warnings": null,
  "auth": null,
  "mount_type": "kv"
}
```

Field Descriptions

- request_id: Unique identifier for this Vault request
- lease_id: Lease identifier for renewable secrets (empty for KV secrets)
- renewable: Boolean indicating if the secret is renewable
- lease_duration: Lease duration in seconds (0 for KV secrets)
- data: Main data object containing the secret
  - data: The actual secret key-value pairs
    - username: Username credential
    - password: Password credential
    - api_key: API key or other custom fields
  - metadata: Vault metadata for this secret
    - created_time: Secret creation timestamp (ISO 8601 format)
    - custom_metadata: Custom metadata if configured
    - deletion_time: Soft deletion timestamp (empty if not deleted)
    - destroyed: Boolean indicating if secret version is destroyed
    - version: Secret version number
- wrap_info: Response wrapping information (null if not wrapped)
- warnings: Array of warning messages (null if none)
- auth: Authentication information (null for read operations)
- mount_type: Type of secrets engine (typically "kv" for key-value)

The module uses the [hvac](https://hvac.readthedocs.io/) Python library to interact with HashiCorp Vault.

### `resolve_credentials()` — Unified credential resolution

The `resolve_credentials()` function provides a high-level interface to
fetch and extract credentials from any supported secrets manager in a single
call. It handles manager instantiation, authentication, secret retrieval,
field extraction, and cleanup automatically.

This function is designed to work independently of any CLI framework, making
it usable from Perceval's `BackendCommand`, KingArthur, or any custom script.

#### Example

```python
from grimoirelab_toolkit.credential_manager import resolve_credentials

# Bitwarden example
credentials = resolve_credentials(
    manager_type='bitwarden',
    manager_config={
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'master_password': 'your-master-password',
    },
    item_name='GitHub',
    field_mapping={'api-token': 'api_token', 'username': 'user'},
)
# credentials = {'api_token': 'ghp_...', 'user': 'myuser'}

# HashiCorp example
credentials = resolve_credentials(
    manager_type='hashicorp',
    manager_config={
        'vault_url': 'https://vault.example.com',
        'token': 'hvs.your-token',
    },
    item_name='secret/my-service',
    field_mapping={'api_key': 'api_token'},
)
```

#### Parameters

- `manager_type` (`str`) — `"bitwarden"` or `"hashicorp"`
- `manager_config` (`dict`) — Manager-specific authentication credentials (see below)
- `item_name` (`str`) — Name/path of the secret item in the vault
- `field_mapping` (`dict[str, str]`) — Maps secret field names to output parameter names

#### Manager config by provider

- **Bitwarden**: `client_id`, `client_secret`, `master_password`
- **HashiCorp**: `vault_url`, `token`, `certificate` (optional)

#### Return value

A `dict[str, str]` mapping output parameter names to resolved string values.
Only fields that were found are included in the result. Missing fields
produce a warning log and are omitted (partial results are valid).

#### Field extraction behavior

Each manager returns secrets in a different format. `resolve_credentials()`
normalizes the extraction:

- **Bitwarden**: Checks `item['login']` dict first (for username, password),
  then searches the `item['fields']` array (for custom fields like API tokens).
- **HashiCorp**: Reads from `secret['data']['data'][field_name]`.

#### Error handling

- Unsupported `manager_type` raises `ValueError`
- Empty `item_name` raises `ValueError`
- Secret item not found raises `CredentialNotFoundError`
- Individual missing fields are skipped with a warning (no error)
- For Bitwarden, `logout()` is always called in a `finally` block

### Optional dependencies (lazy imports)

The secrets manager providers use lazy imports, so you only need to install
the dependencies for the provider you actually use:

- **Bitwarden**: requires `bw` CLI on `PATH` (no Python package needed)
- **HashiCorp**: requires `hvac` (`poetry install --with hashicorp-manager`)

## License

Licensed under GNU General Public License (GPL), version 3 or later.
