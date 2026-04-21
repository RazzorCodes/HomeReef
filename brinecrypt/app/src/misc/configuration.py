import builtins
import os
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar
from urllib.parse import urlparse

import requests
import tomli

from .logger import logger

# Local config file path
LOCAL_CONFIG_PATH = Path.home() / ".config" / "kube-broadcast" / "config.toml"


def read_file_content(filepath: str) -> Optional[str]:
    """
    Read content from a file, following symlinks.

    Args:
        filepath: Path to file

    Returns:
        File content as string, or None if file doesn't exist or can't be read
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return None

        # Follow symlinks
        if path.is_symlink():
            path = path.resolve()

        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content if content else None

    except Exception as e:
        logger.debug(f"Could not read file {filepath}: {e}")
        return None


def load_toml_config(filepath: str) -> dict:
    """
    Load configuration from TOML file.

    Args:
        filepath: Path to TOML file

    Returns:
        Dictionary of configuration values
    """
    try:
        path = Path(os.path.abspath(filepath))
        if not path.exists():
            return {}

        with open(path, "rb") as f:
            config = tomli.load(f)
            logger.info(f"Loaded configuration from: {filepath}")
            return config

    except Exception as e:
        logger.error(f"Failed to load TOML config from {filepath}: {e}")
        return {}


T = TypeVar("T")


@dataclass
class DiscreteConfigurationParameter(Generic[T]):
    param_name: str
    type: builtins.type[T]
    env_var: str | None = None
    default_path: Optional[str] = None
    reads_from_path: bool = False
    default_value: T | None = None
    description: str = ""


# Configuration parameter definitions
__DISCRETE_PARAMETERS = {
    "token": DiscreteConfigurationParameter(
        param_name="token",
        type=str,
        env_var="KUBE_TOKEN",
        reads_from_path=True,
        default_path="/mnt/data/token/node-token",
        description="K3s node token",
    ),
    "ssh_admin": DiscreteConfigurationParameter(
        param_name="ssh_admin",
        type=str,
        env_var="SSH_ADMIN_KEY",
        reads_from_path=True,
        default_path="/mnt/data/ssh/admin.pub",
        description="SSH admin public key",
    ),
    "ssh_agent": DiscreteConfigurationParameter(
        param_name="ssh_agent",
        type=str,
        env_var="SSH_AGENT_KEY",
        reads_from_path=True,
        default_path="/mnt/data/ssh/agent.pub",
        description="SSH agent public key",
    ),
    "host": DiscreteConfigurationParameter(
        param_name="host",
        type=str,
        env_var="KUBE_BROADCAST_HOST",
        description="Host address",
        default_value="0.0.0.0",
    ),
    "port": DiscreteConfigurationParameter(
        param_name="port",
        env_var="KUBE_BROADCAST_PORT",
        description="Port number",
        type=int,
        default_value=8000,
    ),
    "database": DiscreteConfigurationParameter(
        param_name="database",
        type=str,
        description="Database connection string",
        default_value="~/.local/kube-broadcast/data.db",
    ),
}


def _build_parser() -> ArgumentParser:
    """Build command-line argument parser."""

    parser = ArgumentParser(
        description="kube-broadcast: Configuration broadcast server for K3s clusters",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Configuration fallback order:
  1. CLI arguments (--token, --ssh-admin, etc.) OR --config file.toml
  2. Environment variables (KUBE_TOKEN, SSH_ADMIN_KEY, SSH_AGENT_KEY)
  3. Local config file (~/.config/kube-broadcast/config.toml)
  4. Default paths (/mnt/data/...)
  5. Default values

Examples:
  # Using config file
  kube-broadcast --config /path/to/config.toml

  # Using discrete parameters
  kube-broadcast --token /path/to/token --ssh-admin /path/to/admin.pub

  # Using environment variables
  export KUBE_TOKEN="K123456789..."
  kube-broadcast

Note: discrete parameters (--token, etc.) overwrite --config
        """,
    )

    # Config file option
    parser.add_argument(
        "--config",
        type=str,
        help="Path to TOML configuration file (mutually exclusive with discrete params)",
    )

    for discrete_parameter_key in __DISCRETE_PARAMETERS.keys():
        discrete_parameter = __DISCRETE_PARAMETERS[discrete_parameter_key]
        logger.debug(
            f"Adding dicrete parameter {discrete_parameter_key}: --{discrete_parameter.param_name} as {discrete_parameter.type}"
        )

        parser.add_argument(
            f"--{discrete_parameter.param_name}",
            type=discrete_parameter.type,
            help=f"{discrete_parameter.description}",
        )

    return parser


class ParameterSource(Enum):
    EMPTY = "Empty"
    DEFAULT = "Default Value"
    CONFIG_FILE = "Configuration file"
    ENV_VAR = "Environment variable"
    COMMAND_LINE = "Command line"


class ParameterType(Enum):
    PURE = "Pure"
    LOCAL = "Local"
    REMOTE = "Remote"


@dataclass
class KubeBroadcastConfigurationItem:
    name: str
    value: Any
    source: ParameterSource
    type: ParameterType
    source_details: Optional[str]

    def __str__(self):
        return f"{self.name}/{self.type.value}: {self.value} ({self.source.value})"


@dataclass
class KubeBroadcastConfiguration:
    configuration_file: Optional[str] = None

    kube_broadcast_configuration_items: list[KubeBroadcastConfigurationItem] = field(
        default_factory=list
    )

    @property
    def k3s_server_token(self) -> Optional[str]:
        return token.value if (token := self._get_configuration_item("token")) else None

    @property
    def homelab_admin_public_key(self) -> Optional[str]:
        return key.value if (key := self._get_configuration_item("ssh_admin")) else None

    @property
    def homelab_agent_public_key(self) -> Optional[str]:
        return key.value if (key := self._get_configuration_item("ssh_agent")) else None

    @property
    def kube_broadcast_host(self) -> Optional[str]:
        return host.value if (host := self._get_configuration_item("host")) else None

    @property
    def kube_broadcast_port(self) -> Optional[int]:
        return port.value if (port := self._get_configuration_item("port")) else None

    @property
    def kube_broadcast_database(self) -> Optional[str]:
        return (
            database.value
            if (database := self._get_configuration_item("database"))
            else None
        )

    def _get_configuration_item(
        self, name: str
    ) -> Optional[KubeBroadcastConfigurationItem]:
        for item in self.kube_broadcast_configuration_items:
            if item.name == name:
                return item
        return None


def _retrieve_configuration_with_fallback(
    name: str, value: str, accepts_path: bool, source: ParameterSource
) -> Optional[KubeBroadcastConfigurationItem]:
    print(f"Retrieving configuration item '{name}' with value '{value}'")
    if value and accepts_path:
        value_as_abspath = os.path.abspath(value)
        value_as_url = urlparse(value)
        print(value_as_abspath)
        if os.path.exists(value_as_abspath):
            if os.access(value_as_abspath, os.R_OK):
                try:
                    with open(value_as_abspath, "r") as file:
                        file_read_value = file.read().strip()
                        if not file_read_value:
                            logger.warning(
                                f"No data was retreived from file {value_as_abspath}"
                            )

                        return KubeBroadcastConfigurationItem(
                            name=name,
                            value=file_read_value,
                            type=ParameterType.LOCAL,
                            source=source,
                            source_details=value_as_abspath,
                        )

                except Exception as Ex:
                    logger.error(
                        f"While reading {value_as_abspath} an exception occured: {Ex}"
                    )
            else:
                logger.warning(f"No rights to read path {value_as_abspath}")
        if value_as_url.scheme in ("http", "https"):
            request_response = requests.get(value_as_url.geturl(), timeout=1)
            if request_response.status_code == 200:
                return KubeBroadcastConfigurationItem(
                    name=name,
                    value=request_response.text,
                    type=ParameterType.REMOTE,
                    source=source,
                    source_details=value,
                )
    return KubeBroadcastConfigurationItem(
        name=name,
        value=value,
        type=ParameterType.PURE,
        source=source,
        source_details=str(value),
    )


def _retrieve_configuration_for(
    name: str,
    discrete_parameter: DiscreteConfigurationParameter,
    args: Namespace,
    toml_config: dict,
    toml_path: str,
) -> Optional[KubeBroadcastConfigurationItem]:
    print(toml_config)
    if (
        discrete_parameter.param_name in args.__dict__
        and args.__dict__[discrete_parameter.param_name]
    ):
        return _retrieve_configuration_with_fallback(
            name,
            args.__dict__[discrete_parameter.param_name],
            discrete_parameter.reads_from_path,
            ParameterSource.COMMAND_LINE,
        )
    if discrete_parameter.env_var and os.getenv(discrete_parameter.env_var):
        return _retrieve_configuration_with_fallback(
            name,
            os.getenv(discrete_parameter.env_var),  # type: ignore[arg-type] - value is checked beforehand
            discrete_parameter.reads_from_path,
            ParameterSource.ENV_VAR,
        )

    if (
        discrete_parameter.param_name in toml_config
        and toml_config[discrete_parameter.param_name]
    ):
        config = _retrieve_configuration_with_fallback(
            name,
            toml_config[discrete_parameter.param_name],
            discrete_parameter.reads_from_path,
            ParameterSource.CONFIG_FILE,
        )
        if config and config.source_details:
            config.source_details = config.source_details
        return config

    if discrete_parameter.default_value:
        return _retrieve_configuration_with_fallback(
            name,
            discrete_parameter.default_value,
            discrete_parameter.reads_from_path,
            ParameterSource.DEFAULT,
        )

    return None


def retrieve_configuration():
    parser = _build_parser()
    args = parser.parse_args()

    config_file = args.config or str(LOCAL_CONFIG_PATH)
    toml_config = {}
    kube_config = KubeBroadcastConfiguration(configuration_file=config_file)

    if config_file:
        if os.path.exists(config_file):
            toml_config = load_toml_config(config_file)
            if not toml_config:
                logger.warning(f"Config file {config_file} could not be loaded")
        else:
            logger.warning("Config file path incorrect")

    for discrete_parameter_key in __DISCRETE_PARAMETERS.keys():
        discrete_parameter = __DISCRETE_PARAMETERS[discrete_parameter_key]
        config = _retrieve_configuration_for(
            discrete_parameter_key, discrete_parameter, args, toml_config, config_file
        )

        if config:
            kube_config.kube_broadcast_configuration_items.append(config)
            logger.debug(f"Configuration item {config} added")
        else:
            logger.warning(
                f"Configuration item {discrete_parameter_key} could not be parsed"
            )

    return kube_config
