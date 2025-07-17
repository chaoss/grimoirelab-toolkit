# GrimoireLab Toolkit [![Build Status](https://github.com/chaoss/grimoirelab-toolkit/workflows/tests/badge.svg)](https://github.com/chaoss/grimoirelab-toolkit/actions?query=workflow:tests+branch:main+event:push) [![Coverage Status](https://img.shields.io/coveralls/chaoss/grimoirelab-toolkit.svg)](https://coveralls.io/r/chaoss/grimoirelab-toolkit?branch=main)

Toolkit of common functions used across GrimoireLab projects.

This package provides a library composed by functions widely used in other
GrimoireLab projects. These function deal with date handling, introspection,
URIs/URLs, among other topics.

## Requirements

 * Python >= 3.8
 * hvac >= 2.3.0
 * boto3 >= 1.35.63

(Hvac and boto3 are used for credential_manager)

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

## Credential Manager

This is a module made to retrieve credentials from different secrets management systems like Bitwarden.
It accesses the secrets management service, looks for the desired credential and returns it in String form.


There are two ways of using this module.


### Terminal

To use this, any of these two is valid:

Command-Line Interface:

```
$ python -m credential_manager <manager> <service> <credential>
```

Where:

- manager → credential manager used to store the credentials (Bitwarden, aws, Hashicorp Vault)
- service → the platform to which you want to connect (github, gitlab, bugzilla). It is the name of the secret in the credential storage, it does not have to be the same as the service.
- credential → the field inside the secret that you want to retrieve (username, password, api-token)

Examples:

```
$ python -m credential_manager bitwarden gmail password
$ python -m credential_manager hashicorp github api_token
$ python -m credential_manager aws production db_password
```

In each case, the script will log / access into the corresponding vault, search for the secret with the name of the service that wants to be accessed and then retrieve, from that secret, the value with the name inserted as credential.

That is, in the first case, it will log into Bitwarden, access the secret called "bugzilla", and from it retrieve the value of the field "username".

Each of the secrets management services are accessed in different forms and need different configurations to work, as specified in the [[#Managers]] section.


### Python API

To use the module in your python code


```
# Retrieve a secret from Bitwarden
username = get_secret("bitwarden", "bugzilla", "username")

# Retrieve a secret from AWS Secrets Manager
api_token = get_secret("aws", "github", "api-token")

# Retrieve a secret from HashiCorp Vault
password = get_secret("hashicorp", "gitlab", "password")
```

For more advaced usage, you can directly use the factory to get a specific manager:

```
from credential_manager.secrets_manager_factory import SecretsManagerFactory

# Get a Bitwarden manager instance
bw_manager = SecretsManagerFactory.get_bitwarden_manager()
username = bw_manager.get_secret("bugzilla", "username")

# Get an AWS Secrets Manager instance
aws_manager = SecretsManagerFactory.get_aws_manager()
api_token = aws_manager.get_secret("github", "api-token")

```

### Supported Managers


This section explains the different things to consider when using each of the supported secrets management services, like where to store the credentials to access the secrets manager.

#### AWS

The module uses [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html), and this looks for your credentials in the .aws folder, in the files "credentials" and "config".

Configuration:

- Credentials are read from the standard AWS credentials file (~/.aws/credentials)
- Region configuration is read from ~/.aws/config
- Ensure your IAM user/role has appropriate permissions to access Secrets Manager

More about this [here](https://docs.aws.amazon.com/sdkref/latest/guide/file-location.html).

#### Hashicorp Vault

The module uses [hvac](https://hvac.readthedocs.io/en/stable/overview.html) to interact with Hashicorp Vault.

The function will look for the following environment variables to get into the vault, and prompt the user for them if not found:

- VAULT_ADDR  → Address of the Vault server.
- VAULT_TOKEN → A Vault-issued service token that authenticates the CLI user to Vault.
- VAULT_CACERT → Path to a PEM-encoded CA certificate file on the local disk. Used to verify SSL certificates for the server

If environment variables are not found, the user will be prompted to introduce the data manually.

More info on this can be found [here](https://developer.hashicorp.com/vault/docs/commands).

#### Bitwarden

The module uses the [Bitwarden CLI](https://bitwarden.com/help/cli/) to interact with Bitwarden.

Required environment variables:

- BW_EMAIL → the email used to log into the bitwarden account
- BW_PASSWORD

If environment variables are not found, the user will be prompted to introduce the data manually.

## License

Licensed under GNU General Public License (GPL), version 3 or later.
