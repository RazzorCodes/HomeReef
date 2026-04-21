COMPOSE_FILE     := containerfiles/compose.yml
COMPOSE          := podman compose -f $(COMPOSE_FILE)
PIP_INDEX_URL    := $(or $(shell pip config get global.index-url 2>/dev/null),https://pypi.org/simple/)
PIP_TRUSTED_HOST := $(shell pip config get global.trusted-host 2>/dev/null)
TRANSFLUX_PIP_CONF := transflux/app/pip.conf

.PHONY: deploy-local-dev stop-local-dev logs-local-dev _gen-pip-conf

deploy-local-dev: _gen-pip-conf
	$(COMPOSE) up --build -d

stop-local-dev:
	$(COMPOSE) down

logs-local-dev:
	$(COMPOSE) logs -f

_gen-pip-conf:
	@printf '[global]\nindex-url = %s\ntrusted-host = %s\n' \
		"$(PIP_INDEX_URL)" "$(PIP_TRUSTED_HOST)" > $(TRANSFLUX_PIP_CONF)
