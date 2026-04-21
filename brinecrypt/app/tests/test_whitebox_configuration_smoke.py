import pathlib
import sys
from string import printable

import pytest
from app.src.misc.configuration import (
    __DISCRETE_PARAMETERS,
    KubeBroadcastConfiguration,
    ParameterSource,
    ParameterType,
    retrieve_configuration,
)
from pytest_httpserver import HTTPServer

TEST_TOKEN_0 = "TOKEN_TEST_0"
TEST_TOKEN_1 = "TOKEN_TEST_1"
TEST_ADMIN_SSH_0 = "SSH_TEST_ADMIN_0"
TEST_AGENT_SSH_0 = "SSH_TEST_AGENT_0"
TEST_PORT_0 = 8001
TEST_PORT_1 = 8000


@pytest.fixture
def mixed_source_config(monkeypatch, tmp_path, httpserver: HTTPServer):

    agent_path = tmp_path / "agent.key"
    agent_path.write_text(TEST_AGENT_SSH_0)
    TEST_DB_PATH_0 = tmp_path / "data.db"
    TEST_DB_PATH_0.write_text("")
    httpserver.expect_request("/").respond_with_data(TEST_ADMIN_SSH_0)
    config_file = tmp_path / "config.toml"
    test_config_toml = f"""
    port = {TEST_PORT_0}
    database = \"{TEST_DB_PATH_0}\""""
    config_file.write_text(test_config_toml)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--config",
            str(config_file),
            "--token",
            TEST_TOKEN_0,
            "--port",
            str(TEST_PORT_1),
            "--ssh_admin",
            httpserver.url_for("/"),
        ],
    )
    monkeypatch.setenv("SSH_AGENT_KEY", str(agent_path))

    return (retrieve_configuration(), TEST_DB_PATH_0.__str__())


def test_with_token(mixed_source_config: tuple[KubeBroadcastConfiguration, str]):
    config, db_test_path_orig = mixed_source_config
    assert config.k3s_server_token == TEST_TOKEN_0
    assert config.kube_broadcast_port == TEST_PORT_1
    assert config.homelab_admin_public_key == TEST_ADMIN_SSH_0
    assert config.homelab_agent_public_key == TEST_AGENT_SSH_0
    assert config.kube_broadcast_host == __DISCRETE_PARAMETERS["host"].default_value
    assert config.kube_broadcast_database == db_test_path_orig

    token = config._get_configuration_item("token")
    assert token.source == ParameterSource.COMMAND_LINE  # type: ignore[arg-type]
    assert token.type == ParameterType.PURE  # type: ignore[arg-type]

    port = config._get_configuration_item("port")
    assert port.source == ParameterSource.COMMAND_LINE  # type: ignore[arg-type]
    assert port.type == ParameterType.PURE  # type: ignore[arg-type]

    ssh_admin = config._get_configuration_item("ssh_admin")
    assert ssh_admin.source == ParameterSource.COMMAND_LINE  # type: ignore[arg-type]
    assert ssh_admin.type == ParameterType.REMOTE  # type: ignore[arg-type]

    ssh_agent = config._get_configuration_item("ssh_agent")
    assert ssh_agent.source == ParameterSource.ENV_VAR  # type: ignore[arg-type]
    assert ssh_agent.type == ParameterType.LOCAL  # type: ignore[arg-type]

    port = config._get_configuration_item("port")
    assert port.source == ParameterSource.COMMAND_LINE  # type: ignore[arg-type]
    assert port.type == ParameterType.PURE  # type: ignore[arg-type]

    host = config._get_configuration_item("host")
    assert host.source == ParameterSource.DEFAULT  # type: ignore[arg-type]
    assert host.type == ParameterType.PURE  # type: ignore[arg-type]

    db_path = config._get_configuration_item("database")
    assert db_path.source == ParameterSource.CONFIG_FILE  # type: ignore[arg-type]
    assert db_path.type == ParameterType.PURE  # type: ignore[arg-type]
